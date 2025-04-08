import os
import time
import json
import socket
import glob
from datetime import datetime
from dotenv import load_dotenv
import serial
from pymodbus.client import ModbusTcpClient
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

# Hardcoded Appwrite credentials
BASE_URL = "https://appwrite.tsada.edu.rs/v1"
PROJECT_ID = "67a5b2fd0036cbf53dbf"
API_KEY = "standard_58f4f07f94d9b36d8168c64ca493b93eebd51a6fe1fd9d5855d491f2378d404eba5cdd9893033434123850b9426ed0edc51da499e06d986f393b7b9391484ef3db94d013bed0e02467e063f6c93566d96c3daefc93c82b581f108d1afa3f0d782b3772e625ee15c51470ba2bf3e2cad644ee56a645e88c21ec1bf434050febd8"  # 🔐 Hardcoded API key

# Appwrite SDK Setup
client = Client()
client.set_endpoint(BASE_URL)
client.set_project(PROJECT_ID)
client.set_key(API_KEY)
databases = Databases(client)

# Constants
DATABASE_ID = "67a5b54c00004b1a93d7"
RPI_LOGGING_COLLECTION = "67dfc9720019d64746b0"
HARDWARE_FLAGS_COLLECTION = "67de7e600036fcfc5959"
CHARGE_COLLECTION = "67d18e17000dc1b54f39"
DISCHARGE_COLLECTION = "67ac8901003b19f4ca35"
BATTERY_COLLECTION = "67f279860016263782ae"
REFERENCEBATTERY = "67d9b54d0005a8009bc2"

# Serial & PLC config
BAUD_RATE = 9600
PLC_IP = "192.168.1.5"
PLC_PORT = 502

# Modbus
SENSOR_COIL_ADDRESS = 8 # Lepetesnel hasznalt szenzor
MODBUS_INPUT_SENSOR = 9 # Ez azert kell hogy megnezzem, hogy van-e cella a taroloban
MODBUS_OUTPUT_STEPPER = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5
MODBUS_OUTPUT_DCMOTOR = 6

# Hardware_Flags
FORCE_PROGRESS = "67e978a400033ff184cf"
TEST_MODE = "67e96f70002ac63bf054"
RPI_MESSAGE = "67dfc91e003b95ec25dd"
ACTIVE_CELL_ID = "67df14d30029fd472f78"
ERROR_MSG = "67ded78000126b96814e"
SYSTEM_BUSY = "67ded77700122936b58d"
OCR_LAST = "67ded770000ab7e4ea08"
OCR_ACTIVE = "67ded75c002fdd6f4d2d"
ROTATE_CELL = "67debe6f0015e7f39e73"
DISCHARGE_SWITCH = "67deab5a0032c611045d"
CHARGER_SWITCH = "67dea772003c551fc53b"
REFERENCE_THRESHOLD = "67de7f1300149699e3ea"

STATUS_TO_POSITION = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 9: 5}

ROTATE_ON_TIME = 1
ROTATE_OFF_TIME = 2
SERIAL_PORT = "/dev/ttyACM0"

# Logging
def log_to_appwrite(message):
    timestamp = datetime.now().isoformat()
    formatted = f"{timestamp} – {message}"
    print(formatted)
    try:
        with open("/tmp/battery_sync.log", "a") as f:
            f.write(formatted + "\n")
    except:
        pass
    try:
        databases.create_document(
            database_id=DATABASE_ID,
            collection_id=RPI_LOGGING_COLLECTION,
            document_id="unique()",
            data={"MESSAGE": formatted}
        )
    except:
        pass

# Appwrite helpers
def get_setting(name):
    try:
        res = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=HARDWARE_FLAGS_COLLECTION,
            queries=[Query.equal("setting_name", [name])]
        )
        docs = res.get("documents", [])
        log_to_appwrite(f"🔍 get_setting({name}) returned: {docs}")
        return docs[0] if docs else None
    except Exception as e:
        log_to_appwrite(f"SDK error get_setting({name}): {e}")
        return None

def get_active_cell_id():
    test_flag = get_setting("TEST_MODE")
    if test_flag and test_flag.get("setting_boolean"):
        log_to_appwrite("🧪 TEST MODE active – using dummy cell")
        return "TEST_CELL_ID"
    doc = get_setting("ACTIVE_CELL_ID")
    if doc:
        return doc.get("setting_data")
    return None

def get_discharge_switch_mode():
    doc = get_setting("DISCHARGE_SWITCH")
    return 1 if doc and doc.get("setting_boolean") else 2

def get_battery_by_id(bid):
    if bid == "TEST_CELL_ID":
        log_to_appwrite("🧪 Returning dummy battery document for test mode")
        return {
            "$id": bid,
            "status": 1,
            "operation": 0,
            "charge_capacity": 1900,
            "discharge_capacity": 1850,
            "measured_capacity": None,
            "allapot": None
        }
    try:
        return databases.get_document(DATABASE_ID, BATTERY_COLLECTION, bid)
    except Exception as e:
        log_to_appwrite(f"get_battery_by_id error: {e}")
        return None

def update_battery_status(bid, data):
    try:
        databases.update_document(DATABASE_ID, BATTERY_COLLECTION, bid, data=data)
    except Exception as e:
        log_to_appwrite(f"update_battery_status error: {e}")

def update_battery_hardware(hardwarename, data):
    try:
        databases.update_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, hardwarename, data=data)
    except Exception as e:
        log_to_appwrite(f"update_battery_hardware error: {e}")

def save_measurement_to_appwrite(collection_id, battery_id, voltage, current=None, open_circuit=False, status=None):
    try:
        payload = {
            "battery": battery_id,
            "voltage": voltage,
            "open_circuit": open_circuit
        }
        if current:
            if collection_id == CHARGE_COLLECTION:
                payload["chargecurrent"] = current
                payload["status"] = status
            elif collection_id == DISCHARGE_COLLECTION:
                payload["dischargecurrent"] = current

        databases.create_document(DATABASE_ID, collection_id, "unique()", data=payload)
        log_to_appwrite(f"📤 Measurement saved: {voltage:.2f}V")
    except Exception as e:
        log_to_appwrite(f"save_measurement error: {e}")

# Serial helpers
def find_serial_port():
    ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    return ports[0] if ports else None

def open_serial_port():
    global SERIAL_PORT
    try:
        return serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except FileNotFoundError:
        SERIAL_PORT = find_serial_port()
        if SERIAL_PORT:
            return serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    return None

def measure_from_serial(ser):
    try:
        timeout_val = time.time() + 5
        while time.time() < timeout_val:
            line = ser.readline().decode(errors='ignore').strip()
            if not line:
                continue
            log_to_appwrite(f"🔎 Serial line: {line}")
            try:
                data = json.loads(line)
                voltage = float(data.get("chargerA_voltage", 0.0))
                current = float(data.get("charge", 0.0)) / 1000.0  # Convert mA -> A
                mode = 1  # fallback mode if you want to keep 'mode'
                discharge_current = float(data.get("discharge", 0.0)) / 1000.0
                discharge_voltage = float(data.get("discharge_voltage", 0.0))
                charger_b_voltage = float(data.get("chargerB_voltage", 0.0))

                if discharge_current > 0:
                    resistance_check = round(discharge_voltage / discharge_current, 2)
                    log_to_appwrite(f"🧪 Resistance check from serial: {resistance_check} Ω")

                return voltage, current, mode, discharge_current, discharge_voltage, charger_b_voltage
            except Exception:
                pass
        raise ValueError("No valid structured measurement found in serial input")
    except Exception as e:
        log_to_appwrite(f"measure_from_serial error: {e}")
        return None, None, None, None, None, None

# State functions
def rotate_to_position(client, current, target):
    log_to_appwrite(f"Position: {current} → {target}")
    n = target - current

    for i in range(n):
        client.write_coil(MODBUS_OUTPUT_STEPPER, 1)
        time.sleep(0.2)
        
        coils = client.read_coils(SENSOR_COIL_ADDRESS, count=1)
        while coils.bits[0] != True:
            coils = client.read_coils(SENSOR_COIL_ADDRESS, count=1)
        
        time.sleep(0.1)
        client.write_coil(MODBUS_OUTPUT_STEPPER, 0)
        time.sleep(3)
    log_to_appwrite(f"Position reached: {target}")

def do_loading_step(client, bid, current, status, operation):
    if databases.get_document(DATABASE_ID, BATTERY_COLLECTION, bid).get("betoltes") == False:
        if status == 1 and operation == 0:
            log_to_appwrite(f"📦 Loading cell: {bid}")
            client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, True)
            time.sleep(2)
            client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
            update_battery_status(bid, {"status": 2, "operation": 0, "current_position": 1, "target_position": 2, "betoltes": True})
            time.sleep(2)
        else:
            log_to_appwrite(f"📦 Loading cell: {bid}")
            client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, True)
            time.sleep(2)
            client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
            update_battery_status(bid, {"betoltes": True})
            time.sleep(2)
            if status != 2:
                rotate_to_position(client, 1, current)
    
def do_loading_step_any(client):
    log_to_appwrite(f"📦 Loading cell")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, True)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)

def do_voltage_measure_step(ser, bid):
    log_to_appwrite("Voltage measurement started")
    voltage, *_ = measure_from_serial(ser)
    if voltage is not None:
        update_battery_status(bid, {"feszultseg": voltage, "operation": 1})
        if voltage < 2.5:
            log_to_appwrite("⚠️ Voltage < 2.5V → BAD CELL")
            update_battery_status(bid, {"status": 9, "operation": 0, "current_position": 2, "target_position": 6, "feszultsegjo": False, "toltes_kezdes": datetime.now().isoformat()})
        else:
            log_to_appwrite("Voltage measurement: ✅")
            update_battery_status(bid, {"status": 3, "operation": 0, "current_position": 2, "target_position": 2, "feszultsegjo": True, "toltes_kezdes": datetime.now().isoformat()})
    
def do_charge_step(client, bid, ser, status):
    if databases.get_document(DATABASE_ID, BATTERY_COLLECTION, bid).get("operation") == 0:
        log_to_appwrite("⚡ Charge started")

        # DISCHARGE_SWITCH ellenőrzése és kapcsolása    
        dischargestate = databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, DISCHARGE_SWITCH).get("setting_boolean")
        dischargestate = False if dischargestate else dischargestate
        update_battery_hardware(DISCHARGE_SWITCH, {"setting_boolean": dischargestate})
        client.write_coil(MODBUS_OUTPUT_DISCHARGE, dischargestate)
        
        if status == 3:
            update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": True})
            client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, True)
        elif status == 5:
            update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": False})
            client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, False)
        time.sleep(3)

        # Toltes kezdetekori ertek
        #ocv, *_ = measure_from_serial(ser)
        #if ocv: save_measurement_to_appwrite(CHARGE_COLLECTION, bid, ocv, 0, True, status)

        while ocv < 4.18: #TODO:TOLTO
            switchstate = not databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, CHARGER_SWITCH).get("setting_boolean")
            client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, switchstate)
            update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": switchstate})
            time.sleep(1)

            voltage, current, *_ = measure_from_serial(ser)
            save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, False, status)

            time.sleep(30)

            switchstate = not databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, CHARGER_SWITCH).get("setting_boolean")
            client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, switchstate)
            update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": switchstate})

            time.sleep(5)
            
            ocv, *_ = measure_from_serial(ser)
            if ocv: save_measurement_to_appwrite(CHARGE_COLLECTION, bid, ocv, 0, True, status)

            '''
            try:
                ocv_entry = databases.list_documents(DATABASE_ID, CHARGE_COLLECTION, [Query.equal("battery", [bid]), Query.equal("open_circuit", [True])]).get("documents", [])[0]
                ocv = ocv_entry.get("voltage")

                if ocv and voltage and current:
                    resistance = round(abs((ocv - voltage) / current), 3)
                    update_battery_status(bid, {"belso_ellenallas": resistance})
                    log_to_appwrite(f"🧮 Estimated Internal Resistance: {resistance} Ω")
            except Exception as e:
                log_to_appwrite(f"⚠️ Failed to calculate internal resistance: {e}")
            '''
        update_battery_status(bid, {"operation": 1})

def do_discharge_step(client, bid, ser):
    if databases.get_document(DATABASE_ID, BATTERY_COLLECTION, bid).get("operation") == 0:
        log_to_appwrite("🔋 Discharge started")
        
        # DISCHARGE_SWITCH ellenőrzése és kapcsolása
        dischargestate = databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, DISCHARGE_SWITCH).get("setting_boolean")
        dischargestate = True if not dischargestate else dischargestate
        update_battery_hardware(DISCHARGE_SWITCH, {"setting_boolean": dischargestate})
        client.write_coil(MODBUS_OUTPUT_DISCHARGE, dischargestate)
        
        update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": True})
        client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, True)
        time.sleep(3)
        # Merites kezdetekori ertek
        #ocv, *_ = measure_from_serial(ser)
        #if ocv: save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, ocv, 0, True)

        while ocv > 3.02:
            switchstate = not databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, CHARGER_SWITCH).get("setting_boolean")
            client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, switchstate)
            update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": switchstate})
            time.sleep(1)

            voltage, current, *_ = measure_from_serial(ser)
            save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage, current, False)

            time.sleep(30)

            switchstate = not databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, CHARGER_SWITCH).get("setting_boolean")
            client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, switchstate)
            update_battery_hardware(CHARGER_SWITCH, {"setting_boolean": switchstate})

            time.sleep(5)
            
            ocv, *_ = measure_from_serial(ser)
            if ocv: save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, ocv, 0, True)

            '''
            try:
                ocv_entry = databases.list_documents(DATABASE_ID, CHARGE_COLLECTION, [Query.equal("battery", [bid]), Query.equal("open_circuit", [True])]).get("documents", [])[0]
                ocv = ocv_entry.get("voltage")
                
                if ocv and voltage and current:
                    resistance = round((ocv - voltage) / current, 3)
                    update_battery_status(bid, {"belso_ellenallas": resistance})
                    log_to_appwrite(f"🧮 Estimated Internal Resistance: {resistance} Ω")
            except Exception as e:
                log_to_appwrite(f"⚠️ Failed to calculate internal resistance: {e}")
            '''
        update_battery_status(bid, {"operation": 1})


def convert(a):
    dt = datetime.fromisoformat(a)
    return dt.hour + (dt.minute / 60)

def reference_capacity_check(kod):
    reftype = [doc.get("Type") for doc in databases.list_documents(DATABASE_ID, REFERENCEBATTERY).get("documents", [])]
    for refkod in reftype:
        if (kod == refkod):
            return next((doc.get("Capacity") for doc in databases.list_documents(DATABASE_ID, REFERENCEBATTERY, [Query.equal("Type", kod)]).get("documents", [])))
    return 2400

def do_capacity_calculation(bid):
    bat = get_battery_by_id(bid)
    refmAh = reference_capacity_check(kod=bat.get("leolvasottkod"))
    bathard = databases.get_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, REFERENCE_THRESHOLD).get("setting_data")

    reference_capacity_check( kod=bat.get("leolvasottkod"))

    charge = bat.get("charge_capacity") or 0
    discharge = bat.get("discharge_capacity") or 0
    recharge = bat.get("recharge_capacity") or 0

    if not charge:
        try:
            logs = databases.list_documents(DATABASE_ID, CHARGE_COLLECTION, [Query.equal("battery", [bid]), Query.equal("open_circuit", False), Query.equal("status", [3])]).get("documents", [])
            ido = abs(convert(bat.get("toltes_vege")) - convert(bat.get("toltes_kezdes")))
            osszeadva = sum(entry.get("chargecurrent", 0) for entry in logs if entry.get("chargecurrent"))
            avg = round( osszeadva / len(logs), 2)
            
            mAh = round(avg * ido * 1000, 2)
            PmAh = round((mAh / refmAh) * 100)

            update_battery_status(bid, {"charge_capacity": mAh})
            update_battery_status(bid, {"charge_capacity_percentage": PmAh})
        except Exception as e:
            log_to_appwrite(f"❌ Charge capacity esitmation failed: {e}")

    if not discharge:
        try:
            logs = databases.list_documents(DATABASE_ID, DISCHARGE_COLLECTION, [Query.equal("battery", [bid])]).get("documents", [])
            ido = abs(convert(bat.get("merites_vege")) - convert(bat.get("mnerites_kezdes")))
            osszeadva = sum(entry.get("dischargecurrent", 0) for entry in logs if entry.get("dischargecurrent"))
            avg = round( osszeadva / len(logs), 2)
            
            mAh = avg * ido * 1000
            PmAh = round((mAh / refmAh) * 100)

            update_battery_status(bid, {"discharge_capacity": mAh})
            update_battery_status(bid, {"discharge_capacity_percentage": PmAh})

            # Akkumulátorcella besorolása | jó vagy rossz
            quality = "jo" if mAh >= (refmAh * bathard.get("REFERENCE_THRESHOLD")) else "rossz"
            status_next = 7 if quality == "jo" else 9
            position_next = 5 if quality == "jo" else 6

            update_battery_status(bid, {"status": status_next, "operation": 0, "current_position": 4, "target_position": position_next, "toltes_kezdes": datetime.now().isoformat()})

        except Exception as e:
            log_to_appwrite(f"❌ Discharge capacity esitmation failed: {e}")

    if not recharge:
        try:
            logs = databases.list_documents(DATABASE_ID, CHARGE_COLLECTION, [Query.equal("battery", [bid]), Query.equal("status", [5])]).get("documents", [])
            ido = abs(convert(bat.get("ujratoltes_vege")) - convert(bat.get("ujratoltes_kezdes")))
            osszeadva = sum(entry.get("chargecurrent", 0) for entry in logs if entry.get("chargecurrent"))
            avg = round( osszeadva / len(logs), 2)
            
            mAh = avg * ido * 1000
            PmAh = round((mAh / refmAh) * 100)

            update_battery_status(bid, {"recharge_capacity": mAh})
            update_battery_status(bid, {"recharge_capacity_percentage": PmAh})
        except Exception as e:
            log_to_appwrite(f"❌ Recharge capacity esitmation failed: {e}")

def do_output_step(client, bid, good=True):
    log_to_appwrite(f"📦 Ejecting cell: {bid}")

    coil = MODBUS_OUTPUT_GOOD_EJECT if good else MODBUS_OUTPUT_BAD_EJECT
    client.write_coil(coil, 1)
    time.sleep(2)
    client.write_coil(coil, 0)
    update_battery_status(bid, {"operation": 1})

def rotate_ocr_motor(client):
    log_to_appwrite("🔁 Rotating OCR motor due to failed read")
    max_attempts = 5
    for attempt in range(max_attempts):
        log_to_appwrite(f"🔄 OCR rotation attempt {attempt + 1}/{max_attempts}")
        client.write_coil(MODBUS_OUTPUT_DCMOTOR, 1)
        time.sleep(1)
        client.write_coil(MODBUS_OUTPUT_DCMOTOR, 0)
        time.sleep(1)
        cell_id = get_active_cell_id()
        if cell_id:
            log_to_appwrite(f"✅ Cell detected after rotation attempt {attempt + 1}")
            update_battery_status(cell_id, {"rotate_attempts": {attempt + 1}})
            break
    else:
        log_to_appwrite("❌ No cell detected after max OCR rotation attempts")
        try:
            doc = databases.create_document(
                database_id=DATABASE_ID,
                collection_id=BATTERY_COLLECTION,
                document_id="unique()",
                data={
                    "status": 1,
                    "operation": 0,
                    "leolvasottkod": "---",
                    "nyerskod": "---",
                    "rotate_attempts": max_attempts,
                    "current_position": 0,
                    "target_position": 1
                }
            )
            doc_active = get_setting("ACTIVE_CELL_ID")
            if doc_active:
                databases.update_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, document_id=doc_active["$id"], data={"setting_data": doc["$id"]})
            log_to_appwrite(f"📌 Created UNKNOWN cell and set as active: {doc['$id']}")
        except Exception as e:
            log_to_appwrite(f"❌ Failed to create UNKNOWN cell: {e}")

def get_force_progress():
    flag = get_setting("FORCE_PROGRESS")
    return flag and flag.get("setting_boolean")

def fail_active_cell():
    try:
        doc = get_setting("ACTIVE_CELL_ID")
        if doc and doc.get("setting_data"):
            battery = get_battery_by_id(doc.get("settings_data"))
            pozicio = STATUS_TO_POSITION[battery.get("status")]
            update_battery_status(doc["setting_data"], {"status": 9, "operation": 0, "current": pozicio,"target": 6, "allapot": "rossz"}) #"allapot": "Hibás indulás"
            log_to_appwrite("❌ Marked active cell as failed on startup")
    except Exception as e:
        log_to_appwrite(f"⚠️ Failed to mark active cell as failed: {e}")

def main():
    def ping_watchdog():
        try:
            with open("/tmp/battery_watchdog.ping", "w") as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            log_to_appwrite(f"⚠️ Failed to ping watchdog: {e}")

    # Kapcsolatok létesítése
    log_to_appwrite("🚀 MAIN STARTED")
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    ser = open_serial_port()
    if not ser:
        log_to_appwrite("❌ Serial port not available. Exiting.")
        return
    if not client.connect():
        log_to_appwrite("❌ Modbus connection failed. Exiting.")
        return
    log_to_appwrite("✅ Serial and Modbus ready. Entering main loop.")

    # Modbus Output-ok törlése
    client.write_coil(MODBUS_OUTPUT_STEPPER, 0)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
    client.write_coil(MODBUS_OUTPUT_GOOD_EJECT, 0)
    client.write_coil(MODBUS_OUTPUT_BAD_EJECT, 0)
    client.write_coil(MODBUS_OUTPUT_DISCHARGE, 0)
    client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, 0)
    client.write_coil(MODBUS_OUTPUT_DCMOTOR, 0)
    log_to_appwrite("🧹 All Modbus outputs reset")

    fail_active_cell()

    # Induktív szenzorral megnézem, hogy van-e akkumulátorcella a kezdőhelyen
    coils = client.read_coils(MODBUS_INPUT_SENSOR, count=1)
    log_to_appwrite(coils.bits[0])
    while coils.bits[0] != True:
        coils = client.read_coils(MODBUS_INPUT_SENSOR, count=1)

    rotate_ocr_motor(client)
    time.sleep(3)


    try:
        while True:
            ping_watchdog()
            log_to_appwrite("Retrieving Active Cell ID...")
            cell_id = get_active_cell_id()

            ###########################if cell_id != databases.get_document(DATABASE_ID, BATTERY_COLLECTION, ).get("operation") == 0:
            #if not cell_id:
            #    # Induktív szenzorral megnézem, hogy van-e akkumulátorcella a kezdőhelyen
            #    coils = client.read_coils(MODBUS_INPUT_SENSOR, count=1)
            #    log_to_appwrite(coils.bits[0])
            ##    while coils.bits[0] != True:
            #        coils = client.read_coils(MODBUS_INPUT_SENSOR, count=1)
            #    if coils == 0:
            #        log_to_appwrite("🕵️ No active cell ID found.")
            #        time.sleep(5)
            #        continue
            #        
            #    rotate_ocr_motor(client)
            #    time.sleep(3)
            #    continue

            bat = get_battery_by_id(cell_id)
            log_to_appwrite(f"📦 Battery doc: {bat}")
            if not bat:
                log_to_appwrite(f"⚠️ Battery ID '{cell_id}' not found.")
                time.sleep(3)
                continue
            
            status = bat.get("status", 0)
            operation = bat.get("operation", 0)
            force_progress = get_force_progress() #
            log_to_appwrite(f"BatteryID: {cell_id}, Status: {status}, Operation: {operation}, FORCE_PROGRESS: {force_progress}")
            if operation == 1 and not force_progress:
                time.sleep(2)
                continue

            current = bat.get("current_position")
            target = bat.get("target_position")
            feszultsegjo = bat.get("feszultsegjo")

            do_loading_step(client, cell_id, current, status, operation) # P1 - Betöltés után

            if status == 2: # P2 - Feszültségmérés
                rotate_to_position(client, current, target)
                update_battery_status(cell_id, {"current_position": 2})
                time.sleep(2)
                do_voltage_measure_step(ser, cell_id)
                time.sleep(2)

            elif status == 3: # P2 - Töltés
                do_charge_step(client, cell_id, ser, status)
                if operation == 1: update_battery_status(cell_id, {"status": 4, "operation": 0, "current_position": 2, "target_position": 3, "toltes_vege": datetime.now().isoformat(), "merites_kezdes": datetime.now().isoformat()})
                time.sleep(2)

            elif status == 4: # Merítés
                rotate_to_position(client, current, target)
                update_battery_status(cell_id, {"current_position": 3})
                time.sleep(2)
                do_discharge_step(client, cell_id, ser)
                if operation == 1: update_battery_status(cell_id, {"status": 5, "operation": 0, "current_position": 3, "target_position": 4, "merites_vege": datetime.now().isoformat(), "ujratoltes_kezdes": datetime.now().isoformat()})
                time.sleep(2)
            
            elif status == 5: # Újratöltés
                rotate_to_position(client, current, target)
                update_battery_status(cell_id, {"current_position": 4})
                time.sleep(2)
                do_charge_step(client, cell_id, ser, status)
                update_battery_status(cell_id, {"ujratoltes_vege": datetime.now().isoformat()})
                do_capacity_calculation(cell_id)
            
            elif status in (7, 9) and feszultsegjo == True: # Jó vagy Rossz
                rotate_to_position(client, current, target)
                update_battery_status(cell_id, {"current_position": STATUS_TO_POSITION[status]})
                time.sleep(5)
                do_output_step(client, cell_id, good=(status == 7))
                
                update_battery_status(cell_id, {"status": 0, "operation": 0})
                log_to_appwrite("Kész cella, új betöltés jöhet")

                try:
                    doc_active = get_setting("ACTIVE_CELL_ID")
                    if doc_active:
                        databases.update_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, doc_active["$id"], {"setting_data": None})
                        log_to_appwrite("🧹 Cleared ACTIVE_CELL_ID after completion")
                except Exception as e:
                    log_to_appwrite(f"⚠️ Failed to clear ACTIVE_CELL_ID: {e}")
            
            elif status == 9 and (feszultsegjo == False or feszultsegjo == None):
                rotate_to_position(client, current, target)
                update_battery_status(cell_id, {"current_position": STATUS_TO_POSITION[status]})
                time.sleep(5)
                do_output_step(client, cell_id, good = False)

                update_battery_status(cell_id, {"status": 0, "operation": 0})
                log_to_appwrite("Kész cella, új betöltés jöhet")

                try:
                    doc_active = get_setting("ACTIVE_CELL_ID")
                    if doc_active:
                        databases.update_document(DATABASE_ID, HARDWARE_FLAGS_COLLECTION, doc_active["$id"], {"setting_data": None})
                        log_to_appwrite("🧹 Cleared ACTIVE_CELL_ID after completion")
                except Exception as e:
                    log_to_appwrite(f"⚠️ Failed to clear ACTIVE_CELL_ID: {e}")

            time.sleep(1)
    except KeyboardInterrupt:
        log_to_appwrite("🛑 Script terminated by user.")
    finally:
        client.close()
        ser.close()

if __name__ == "__main__":
    main()
