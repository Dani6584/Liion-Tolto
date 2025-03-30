# Li-ion Battery Handler using Appwrite SDK (with hardcoded credentials)

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
BATTERY_COLLECTION = "67a5b55b002eceac9c33"

# Serial & PLC config
BAUD_RATE = 9600
PLC_IP = "192.168.1.5"
PLC_PORT = 502
# The sensor coil address used for reading the endstop sensor (LOGO! V2.0). Adjust as needed.
SENSOR_COIL_ADDRESS = 6  # <--- ADJUST IF NEEDED

# The original code used these constants for outputs:
MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5

# For revolve logic, we keep track of the current revolver position in code:
STATUS_TO_POSITION = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 9: 5}
current_position = 0

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
            "chargecapacity": 1900,
            "dischargecapacity": 1850,
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

def save_measurement_to_appwrite(collection_id, battery_id, voltage, current=None, open_circuit=False, mode=1):
    try:
        payload = {
            "battery": battery_id,
            "voltage": voltage,
            "open_circuit": open_circuit,
            "mode": mode
        }
        if current:
            if collection_id == "67d18e17000dc1b54f39":  # CHARGE_COLLECTION
                payload["chargecurrent"] = current
            elif collection_id == "67ac8901003b19f4ca35":  # DISCHARGE_COLLECTION
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
        lines = []
        timeout_val = time.time() + 5
        while time.time() < timeout_val:
            line = ser.readline().decode(errors='ignore').strip()
            if not line:
                continue
            log_to_appwrite(f"🔎 Serial line: {line}")
            lines.append(line)
            try:
                data = json.loads(line)
                voltage = float(data.get("chargerA_voltage", 0.0))
                current = float(data.get("charge", 0.0)) / 1000.0  # Convert mA to A for storage
                mode = 1  # fallback mode
                discharge_current = float(data.get("discharge", 0.0)) / 1000.0
                discharge_voltage = float(data.get("discharge_voltage", 0.0))
                charger_b_voltage = float(data.get("chargerB_voltage", 0.0))

                # 🔍 Kontroll ellenállás számítás (ha discharge_current hibás lenne)
                if discharge_current > 0:
                    resistance_check = round(discharge_voltage / discharge_current, 2)
                    log_to_appwrite(f"🧪 Resistance check from serial: {resistance_check} Ω")

                return voltage, current, mode, discharge_current, discharge_voltage, charger_b_voltage
            except Exception as e:
                continue
        raise ValueError("No valid structured measurement found in serial input")
    except Exception as e:
        log_to_appwrite(f"measure_from_serial error: {e}")
        return None, None, None, None, None, None
    except Exception as e:
        log_to_appwrite(f"measure_from_serial error: {e}")
        return None, None, None

# ==========================
# NEW: Endstop-based revolve logic
# ==========================

def wait_for_sensor_rising_edge(client, address=SENSOR_COIL_ADDRESS, timeout=10):
    """
    Waits until the sensor connected to a Modbus coil (e.g., V2.0) performs a LOW -> HIGH transition.
    address: coil address for the sensor
    timeout: max time to wait in seconds
    """
    start_time = time.time()

    # Wait for sensor to go LOW first
    while True:
        result = client.read_coils(address=address, count=1)
        if result and len(result.bits) > 0:
            if not result.bits[0]:
                break
        if time.time() - start_time > timeout:
            log_to_appwrite("⚠️ Timeout while waiting for sensor to go LOW")
            return False
        time.sleep(0.05)

    # Then wait for sensor to go HIGH
    while True:
        result = client.read_coils(address=address, count=1)
        if result and len(result.bits) > 0:
            if result.bits[0]:
                break
        if time.time() - start_time > timeout:
            log_to_appwrite("⚠️ Timeout while waiting for sensor to go HIGH")
            return False
        time.sleep(0.05)

    log_to_appwrite("📍 Sensor edge detected (LOW → HIGH)")
    return True


def rotate_to_position(client, target_position):
    """
    Rotates the revolver to a specific logical position (0–5), using endstop sensor detection.
    This REPLACES the old time-based stepping approach.
    """
    global current_position
    steps_needed = (target_position - current_position) % 6
    log_to_appwrite(f"🎯 Need to move from {current_position} to {target_position} ({steps_needed} steps)")

    for step in range(steps_needed):
        log_to_appwrite(f"🔄 Step {step + 1}/{steps_needed}")
        # Start motor
        client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, True)

        # Wait for sensor to detect a rising edge
        if not wait_for_sensor_rising_edge(client, address=SENSOR_COIL_ADDRESS, timeout=10):
            # If we never get a rising edge, abort
            client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, False)
            log_to_appwrite("❌ Sensor edge not detected. Aborting rotation.")
            return

        # Stop motor
        client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, False)
        time.sleep(0.5)

        # Update the in-software position
        current_position = (current_position + 1) % 6

    log_to_appwrite(f"✅ Reached position {current_position}")

# ==========================
# End revolve logic
# ==========================

def do_loading_step(client, bid):
    log_to_appwrite(f"📦 Loading cell: {bid}")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 1)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
    update_battery_status(bid, {"operation": 1})

def do_voltage_measure_step(ser, bid):
    voltage, *_ = measure_from_serial(ser)
    if voltage is not None:
        update_battery_status(bid, {"feszultseg": voltage, "operation": 1})
        if voltage < 2.5:
            update_battery_status(bid, {"status": 9, "operation": 0})
            log_to_appwrite("⚠️ Voltage < 2.5V → BAD CELL")

def do_charge_step(client, bid, ser):
    voltage, current, mode, *_ = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite("67d18e17000dc1b54f39", bid, voltage, current, False, mode)
    # Toggle charging relay
    client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, 1)
    time.sleep(1)
    client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, 0)

    voltage, current, mode, *_ = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite("67d18e17000dc1b54f39", bid, voltage, current, False, mode)

    # Estimate internal resistance if open-circuit voltage is known
    try:
        ocv_entry = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=DISCHARGE_COLLECTION,
            queries=[Query.equal("battery", [bid]), Query.equal("open_circuit", [True])]
        ).get("documents", [])[0]
        ocv = ocv_entry.get("voltage")
        if ocv and current and voltage:
            resistance = round((ocv - voltage) / current, 3) if current else None
            update_battery_status(bid, {"belso_ellenallas": resistance})
            log_to_appwrite(f"🧮 Internal resistance estimated: {resistance} Ω")
    except Exception as e:
        log_to_appwrite(f"⚠️ Failed to calculate internal resistance: {e}")

    update_battery_status(bid, {"operation": 1})

def do_discharge_step(client, bid, ser):
    mode = get_discharge_switch_mode()

    # Open-circuit measurement before discharge
    voltage_oc, _, _ = measure_from_serial(ser)
    if voltage_oc:
        save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage_oc, None, True, mode)

    # Start discharge
    client.write_coil(MODBUS_OUTPUT_DISCHARGE, 1)
    time.sleep(2)

    voltage, current, _ = measure_from_serial(ser)
    if voltage:
        # NB: the original code tried to do `/ 1000.0` but measure_from_serial already does that
        save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage, current, False, mode)

    # Estimate internal resistance now that we have both OCV and loaded voltage
    try:
        logs = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=DISCHARGE_COLLECTION,
            queries=[Query.equal("battery", [bid])]
        ).get("documents", [])
        ocv = next((entry.get("voltage") for entry in logs if entry.get("open_circuit")), None)
        under_load = next((entry.get("voltage") for entry in logs if not entry.get("open_circuit")), None)
        current_val = next((entry.get("dischargecurrent") for entry in logs if not entry.get("open_circuit")), None)
        if ocv and under_load and current_val:
            resistance = round((ocv - under_load) / current_val, 3)
            update_battery_status(bid, {"belso_ellenallas": resistance})
            log_to_appwrite(f"🧮 Internal resistance estimated: {resistance} Ω")
    except Exception as e:
        log_to_appwrite(f"⚠️ Failed to estimate resistance: {e}")

    update_battery_status(bid, {"operation": 1})

def do_recharge_step(client, bid, ser):
    voltage, current, mode, *_ = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, False, mode)

    update_battery_status(bid, {"operation": 1})

def do_output_step(client, bid, good=True):
    coil = MODBUS_OUTPUT_GOOD_EJECT if good else MODBUS_OUTPUT_BAD_EJECT
    client.write_coil(coil, 1)
    time.sleep(2)
    client.write_coil(coil, 0)
    update_battery_status(bid, {"operation": 1})

# OCR motor rotation if no cell read

def rotate_ocr_motor(client):
    log_to_appwrite("🔁 Rotating OCR motor due to failed read")
    max_attempts = 5
    for attempt in range(max_attempts):
        log_to_appwrite(f"🔄 OCR rotation attempt {attempt + 1}/{max_attempts}")
        client.write_coil(6, 1)  # Q7 (V0.7)
        time.sleep(1)
        client.write_coil(6, 0)
        time.sleep(1)
        cell_id = get_active_cell_id()
        if cell_id:
            log_to_appwrite(f"✅ Cell detected after rotation attempt {attempt + 1}")
            break
    else:
        log_to_appwrite("❌ No cell detected after max OCR rotation attempts")
        # Create UNKNOWN CELL entry
        try:
            doc = databases.create_document(
                database_id=DATABASE_ID,
                collection_id=BATTERY_COLLECTION,
                document_id="unique()",
                data={
                    "status": 1,
                    "operation": 0,
                    "leolvasottkod": "Ismeretlen cella",
                    "nyerskod": "---",
                    "allapot": "Folyamatban",
                    "ideal_capacity": "0",
                    "ideal_voltage": ""
                }
            )
            # Set this new ID as ACTIVE_CELL_ID
            doc_active = get_setting("ACTIVE_CELL_ID")
            if doc_active:
                databases.update_document(
                    database_id=DATABASE_ID,
                    collection_id=HARDWARE_FLAGS_COLLECTION,
                    document_id=doc_active["$id"],
                    data={"setting_data": doc["$id"]}
                )
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
            update_battery_status(doc["setting_data"], {"status": 9, "operation": 0, "allapot": "Hibás indulás"})
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
    global current_position
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

    # Reset all outputs and fail current active cell
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
    client.write_coil(MODBUS_OUTPUT_GOOD_EJECT, 0)
    client.write_coil(MODBUS_OUTPUT_BAD_EJECT, 0)
    client.write_coil(MODBUS_OUTPUT_DISCHARGE, 0)
    client.write_coil(MODBUS_OUTPUT_CHARGE_SWITCH, 0)
    client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, 0)
    log_to_appwrite("🧹 All Modbus outputs reset")
    fail_active_cell()

    try:
        while True:
            ping_watchdog()
            log_to_appwrite("🔍 Checking for active cell...")
            cell_id = get_active_cell_id()
            if not cell_id:
                log_to_appwrite("🕵️ No active cell ID found.")
                rotate_ocr_motor(client)
                time.sleep(3)
                continue
            bat = get_battery_by_id(cell_id)
            log_to_appwrite(f"📦 Battery doc: {bat}")
            if not bat:
                log_to_appwrite(f"⚠️ Battery ID '{cell_id}' not found.")
                time.sleep(3)
                continue
            status = bat.get("status", 0)
            operation = bat.get("operation", 0)
            force_progress = get_force_progress()
            log_to_appwrite(f"📊 Status: {status}, Operation: {operation}, FORCE_PROGRESS: {force_progress}")
            if operation == 1 and not force_progress:
                time.sleep(2)
                continue
            log_to_appwrite(f"⚙️ Performing action for battery {cell_id} with status {status}")

            # If we are at position 0, and the status is 7 or 9, we rotate to the ejection position.
            if current_position == 0 and status in STATUS_TO_POSITION and status in [7, 9]:
                rotate_to_position(client, STATUS_TO_POSITION[status])

            if status == 1:
                do_loading_step(client, cell_id)
                # Now revolve to measurement position
                rotate_to_position(client, STATUS_TO_POSITION[2])
                update_battery_status(cell_id, {"status": 2, "operation": 0})
            elif status == 2:
                do_voltage_measure_step(ser, cell_id)
                log_to_appwrite("➡️ Switching to charging phase (status = 3)")
                update_battery_status(cell_id, {"status": 3, "operation": 0, "toltes_kezdes": datetime.now().isoformat()})

            elif status == 3:
                do_charge_step(client, cell_id, ser)
                log_to_appwrite("⚡ Charging started")
                update_battery_status(cell_id, {"status": 4, "operation": 0, "toltes_vege": datetime.now().isoformat(), "merites_kezdes": datetime.now().isoformat()})
            elif status == 4:
                do_discharge_step(client, cell_id, ser)
                log_to_appwrite("🔋 Discharge started")
                update_battery_status(cell_id, {"status": 5, "operation": 0, "merites_vege": datetime.now().isoformat()})
            elif status == 5:
                do_recharge_step(client, cell_id, ser)
                log_to_appwrite("🔁 Recharge started")
                bat = get_battery_by_id(cell_id)
                charge = bat.get("chargecapacity") or 0
                discharge = bat.get("dischargecapacity") or 0
                measured = discharge or 0
                if not measured:
                    try:
                        logs = databases.list_documents(
                            database_id=DATABASE_ID,
                            collection_id=DISCHARGE_COLLECTION,
                            queries=[Query.equal("battery", [cell_id])]
                        ).get("documents", [])
                        measured = sum(entry.get("dischargecurrent", 0) for entry in logs if entry.get("dischargecurrent"))
                        measured = round(measured / 3600, 2)
                    except Exception as e:
                        log_to_appwrite(f"❌ Discharge capacity estimation failed: {e}")
                if not charge:
                    try:
                        logs = databases.list_documents(
                            database_id=DATABASE_ID,
                            collection_id=CHARGE_COLLECTION,
                            queries=[Query.equal("battery", [cell_id])]
                        ).get("documents", [])
                        charge = sum(entry.get("chargecurrent", 0) for entry in logs if entry.get("chargecurrent"))
                        charge = round(charge / 3600, 2)
                        update_battery_status(cell_id, {"chargecapacity": charge})
                        log_to_appwrite(f"⚡ Estimated charge capacity: {charge} mAh")
                    except Exception as e:
                        log_to_appwrite(f"❌ Charge capacity estimation failed: {e}")
                    except Exception as e:
                        log_to_appwrite(f"❌ Capacity estimation failed: {e}")
                quality = "Jó" if measured >= 1800 else "Rossz"
                status_next = 7 if quality == "Jó" else 9
                log_to_appwrite(f"🧪 Capacity measured: {measured} mAh → {quality}")
                update_battery_status(cell_id, {
                    "status": status_next,
                    "operation": 0,
                    "recharge_kezdes": datetime.now().isoformat(),
                    "recharge_vege": datetime.now().isoformat(),
                    "measured_capacity": measured,
                    "allapot": quality
                })
            elif status == 7:
                do_output_step(client, cell_id, good=True)
                update_battery_status(cell_id, {"status": 0, "operation": 0, "allapot_uzenet": "Kész cella, új betöltés jöhet"})
                try:
                    doc_active = get_setting("ACTIVE_CELL_ID")
                    if doc_active:
                        databases.update_document(
                            database_id=DATABASE_ID,
                            collection_id=HARDWARE_FLAGS_COLLECTION,
                            document_id=doc_active["$id"],
                            data={"setting_data": None}
                        )
                        log_to_appwrite("🧹 Cleared ACTIVE_CELL_ID after completion")
                except Exception as e:
                    log_to_appwrite(f"⚠️ Failed to clear ACTIVE_CELL_ID: {e}")
            elif status == 9:
                do_output_step(client, cell_id, good=False)
                update_battery_status(cell_id, {"status": 0, "operation": 0, "allapot_uzenet": "Kész cella, új betöltés jöhet"})
                try:
                    doc_active = get_setting("ACTIVE_CELL_ID")
                    if doc_active:
                        databases.update_document(
                            database_id=DATABASE_ID,
                            collection_id=HARDWARE_FLAGS_COLLECTION,
                            document_id=doc_active["$id"],
                            data={"setting_data": None}
                        )
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
