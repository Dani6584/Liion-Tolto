# Li-ion Battery Handler using Appwrite SDK (with hardcoded credentials)

import os
import time
import json
<<<<<<< Updated upstream
import socket
import glob
=======
import requests
import serial
>>>>>>> Stashed changes
from datetime import datetime
from dotenv import load_dotenv
import serial
from pymodbus.client import ModbusTcpClient
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.query import Query

<<<<<<< Updated upstream
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
=======
# 🌱 Load environment variables
load_dotenv()
BASE_URL = os.environ.get("APPWRITE_BASE_URL", "https://appwrite.tsada.edu.rs/v1")
HEADERS = {
    "Content-Type": "application/json",
    "X-Appwrite-Project": os.environ.get("APPWRITE_PROJECT_ID", "67a5b2fd0036cbf53dbf"),
    "X-Appwrite-Key": os.environ.get("APPWRITE_API_KEY", "")
}

# 📦 Appwrite Collections
>>>>>>> Stashed changes
DATABASE_ID = "67a5b54c00004b1a93d7"
RPI_LOGGING_COLLECTION = "67dfc9720019d64746b0"
HARDWARE_FLAGS_COLLECTION = "67de7e600036fcfc5959"
CHARGE_COLLECTION = "67d18e17000dc1b54f39"
DISCHARGE_COLLECTION = "67ac8901003b19f4ca35"
BATTERY_COLLECTION = "67a5b55b002eceac9c33"

<<<<<<< Updated upstream
# Serial & PLC config
BAUD_RATE = 9600
PLC_IP = "192.168.1.5"
PLC_PORT = 502
ROTATE_ON_TIME = 1
ROTATE_OFF_TIME = 2
SERIAL_PORT = "/dev/ttyACM0"
=======
# ⚙️ PLC & Serial
PLC_IP = os.environ.get("PLC_IP", "192.168.1.5")
PLC_PORT = int(os.environ.get("PLC_PORT", "502"))
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = int(os.environ.get("BAUD_RATE", "9600"))
>>>>>>> Stashed changes

# 🔁 Revolver delay times
ROTATE_ON_TIME = float(os.environ.get("ROTATE_ON_TIME", 1))
ROTATE_OFF_TIME = float(os.environ.get("ROTATE_OFF_TIME", 2))

# 🔌 Modbus outputs
MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5

# 🔁 Status to revolver position
STATUS_TO_POSITION = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 9: 5}
current_position = 0

<<<<<<< Updated upstream
# Logging

=======
# 📝 Log helper
>>>>>>> Stashed changes
def log_to_appwrite(message):
    timestamp = datetime.now().isoformat()
    formatted = f"{timestamp} – {message}"
    print(formatted)
    try:
<<<<<<< Updated upstream
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
=======
        requests.post(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{RPI_LOGGING_COLLECTION}/documents",
            headers=HEADERS,
            json={"data": {"MESSAGE": f"{datetime.now().isoformat()} – {message}"}}
        )
    except Exception as e:
        print(f"Logging failed: {e}")

# 🔧 Settings
def get_setting(setting_name):
    try:
        r = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{HARDWARE_FLAGS_COLLECTION}/documents"
            f"?queries[]=equal(\"setting_name\",\"{setting_name}\")&queries[]=limit(1)",
            headers=HEADERS
>>>>>>> Stashed changes
        )
    except:
        pass

<<<<<<< Updated upstream
# Appwrite helpers

def get_setting(name):
    try:
        from appwrite.query import Query
        res = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=HARDWARE_FLAGS_COLLECTION,
            queries=[Query.equal("setting_name", [name])]
        )
        docs = res.get("documents", [])
        return docs[0] if docs else None
    except Exception as e:
        log_to_appwrite(f"SDK error get_setting({name}): {e}")
        return None

def get_active_cell_id():
    doc = get_setting("ACTIVE_CELL_ID")
    if doc:
        return doc.get("setting_data")
    return None

def get_discharge_switch_mode():
    doc = get_setting("DISCHARGE_SWITCH")
    return 1 if doc and doc.get("setting_boolean") else 2

def get_battery_by_id(bid):
    try:
        return databases.get_document(DATABASE_ID, BATTERY_COLLECTION, bid)
    except Exception as e:
        log_to_appwrite(f"get_battery_by_id error: {e}")
        return None
=======
def get_active_cell_id():
    doc = get_setting("ACTIVE_CELL_ID")
    return doc.get("setting_data") if doc else None

def get_discharge_switch_mode():
    doc = get_setting("DISCHARGE_SWITCH")
    return 1 if doc and doc.get("setting_boolean", False) else 2

# 🔋 Akkumulátor adatlekérés
def get_battery_by_id(bid):
    try:
        r = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{bid}",
            headers=HEADERS
        )
        if r.status_code == 200:
            return r.json()
        else:
            log_to_appwrite(f"⚠️ Battery fetch failed: {r.status_code} for {bid}")
    except Exception as e:
        log_to_appwrite(f"⚠️ Battery fetch exception: {e}")
    return None
>>>>>>> Stashed changes

def update_battery_status(bid, data):
    try:
        databases.update_document(DATABASE_ID, BATTERY_COLLECTION, bid, data=data)
    except Exception as e:
<<<<<<< Updated upstream
        log_to_appwrite(f"update_battery_status error: {e}")
=======
        log_to_appwrite(f"⚠️ Battery update failed: {e}")

# 🔁 Revolver forgatása
def rotate_to_position(client, target_position):
    global current_position
    steps = (target_position - current_position) % 6
    for _ in range(steps):
        client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, 1)
        time.sleep(ROTATE_ON_TIME)
        client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, 0)
        time.sleep(ROTATE_OFF_TIME)
    current_position = target_position
    log_to_appwrite(f"🔄 Revolver moved {steps} steps to position {current_position}")
>>>>>>> Stashed changes

# 📟 Mérési adat soros portról
def measure_from_serial(ser):
    try:
        ser.write(b"MEASURE\n")
        time.sleep(2)
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            try:
                data = json.loads(line)
                voltage = float(data.get("voltage", 0.0))
                current = float(data.get("current", 0.0))
                mode = int(data.get("mode", 1))
                return voltage, current, mode
            except json.JSONDecodeError:
                log_to_appwrite(f"⚠️ JSON decode error from serial: {line}")
    except Exception as e:
        log_to_appwrite(f"⚠️ Serial error: {e}")
    return None, None, None

# 🧪 Mentés Appwrite-ba
def save_measurement_to_appwrite(collection_id, battery_id, voltage, current=None, open_circuit=False, mode=1):
    try:
        payload = {
            "battery": battery_id,
            "voltage": voltage,
            "open_circuit": open_circuit,
            "mode": mode
        }
        if current:
            if collection_id == CHARGE_COLLECTION:
                payload["chargecurrent"] = current
            elif collection_id == DISCHARGE_COLLECTION:
                payload["dischargecurrent"] = current

        databases.create_document(DATABASE_ID, collection_id, "unique()", data=payload)
        log_to_appwrite(f"📤 Measurement saved: {voltage:.2f}V")
    except Exception as e:
        log_to_appwrite(f"save_measurement error: {e}")

<<<<<<< Updated upstream
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
        ser.write(b"MEASURE\n")
        time.sleep(2)
        line = ser.readline().decode(errors='ignore').strip()
        data = json.loads(line)
        return float(data.get("voltage", 0.0)), float(data.get("current", 0.0)), int(data.get("mode", 1))
    except Exception as e:
        log_to_appwrite(f"measure_from_serial error: {e}")
    return None, None, None

# Core steps

def rotate_to_position(client, target):
    global current_position
    steps = (target - current_position) % 6
    for _ in range(steps):
        client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, 1)
        time.sleep(ROTATE_ON_TIME)
        client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, 0)
        time.sleep(ROTATE_OFF_TIME)
    current_position = target
    log_to_appwrite(f"🔄 Revolver moved {steps} steps to position {target}")

=======
# ⚙️ Egyes lépések
>>>>>>> Stashed changes
def do_loading_step(client, bid):
    log_to_appwrite(f"📦 Loading cell: {bid}")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 1)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
    update_battery_status(bid, {"operation": 1})

def do_voltage_measure_step(ser, bid):
    voltage, _, _ = measure_from_serial(ser)
    if voltage is not None:
<<<<<<< Updated upstream
        update_battery_status(bid, {"feszultseg": voltage, "operation": 1})
        if voltage < 2.5:
            update_battery_status(bid, {"status": 9, "operation": 0})
            log_to_appwrite("⚠️ Voltage < 2.5V → BAD CELL")
=======
        if voltage < 2.5:
            update_battery_status(bid, {"feszultseg": voltage, "status": 9, "operation": 0})
            log_to_appwrite("⚠️ Voltage < 2.5V → BAD CELL")
        else:
            update_battery_status(bid, {"feszultseg": voltage, "operation": 1})
>>>>>>> Stashed changes

def do_charge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, False, mode)
    update_battery_status(bid, {"operation": 1})

def do_discharge_step(client, bid, ser):
    mode = get_discharge_switch_mode()
    voltage_oc, _, _ = measure_from_serial(ser)
    if voltage_oc:
        save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage_oc, None, True, mode)
<<<<<<< Updated upstream
    client.write_coil(MODBUS_OUTPUT_DISCHARGE, 1)
    time.sleep(2)
=======

    client.write_coil(MODBUS_OUTPUT_DISCHARGE, 1)
    time.sleep(2)

>>>>>>> Stashed changes
    voltage, current, _ = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage, current, False, mode)
    update_battery_status(bid, {"operation": 1})

def do_recharge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, False, mode)
    update_battery_status(bid, {"operation": 1})

def do_output_step(client, bid, good=True):
    coil = MODBUS_OUTPUT_GOOD_EJECT if good else MODBUS_OUTPUT_BAD_EJECT
    client.write_coil(coil, 1)
    time.sleep(2)
    client.write_coil(coil, 0)
    update_battery_status(bid, {"operation": 1})

<<<<<<< Updated upstream
# Main loop

=======
# 🚀 Main loop
>>>>>>> Stashed changes
def main():
    global current_position
    log_to_appwrite("🚀 MAIN STARTED")
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
<<<<<<< Updated upstream
    ser = open_serial_port()
    if not ser:
        log_to_appwrite("❌ Serial port not available. Exiting.")
=======

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        log_to_appwrite(f"❌ Serial port open failed: {e}")
        return

    if not client.connect():
        log_to_appwrite("❌ Modbus connection failed")
>>>>>>> Stashed changes
        return
    if not client.connect():
        log_to_appwrite("❌ Modbus connection failed. Exiting.")
        return
    log_to_appwrite("✅ Serial and Modbus ready. Entering main loop.")
    try:
        while True:
            log_to_appwrite("🔍 Checking for active cell...")
            cell_id = get_active_cell_id()
            if not cell_id:
<<<<<<< Updated upstream
                log_to_appwrite("🕵️ No active cell ID found.")
=======
                log_to_appwrite("🔍 No active cell ID found.")
>>>>>>> Stashed changes
                time.sleep(3)
                continue
            bat = get_battery_by_id(cell_id)
            if not bat:
                log_to_appwrite(f"⚠️ Battery ID '{cell_id}' not found.")
                time.sleep(3)
                continue
            status = bat.get("status", 0)
            operation = bat.get("operation", 0)
<<<<<<< Updated upstream
            if operation == 0:
=======
            if operation != 0:
                log_to_appwrite(f"⏳ Battery {cell_id} is still processing. Skipping.")
>>>>>>> Stashed changes
                time.sleep(2)
                continue
            log_to_appwrite(f"⚙️ Performing action for battery {cell_id} with status {status}")

<<<<<<< Updated upstream
            # Automatically set next status once operation is confirmed complete
=======
            log_to_appwrite(f"⚙️ Performing action for battery {cell_id} with status {status}")

>>>>>>> Stashed changes
            if status in STATUS_TO_POSITION:
                rotate_to_position(client, STATUS_TO_POSITION[status])

            # Only steps the hardware should fully automate
            if status == 1:
                do_loading_step(client, cell_id)
                update_battery_status(cell_id, {"operation": 0})
            elif status == 2:
                do_voltage_measure_step(ser, cell_id)
                update_battery_status(cell_id, {"operation": 0})

            # Remaining steps require web interface to decide when to move on
            elif status == 3:
                do_charge_step(client, cell_id, ser)
                update_battery_status(cell_id, {"operation": 1})
            elif status == 4:
                do_discharge_step(client, cell_id, ser)
                update_battery_status(cell_id, {"operation": 1})
            elif status == 5:
                do_recharge_step(client, cell_id, ser)
                update_battery_status(cell_id, {"operation": 1})
            elif status == 7:
                do_output_step(client, cell_id, good=True)
                update_battery_status(cell_id, {"operation": 1})
            elif status == 9:
                do_output_step(client, cell_id, good=False)
                update_battery_status(cell_id, {"operation": 1})

            time.sleep(1)
    except KeyboardInterrupt:
        log_to_appwrite("🛑 Script terminated by user.")
    finally:
        client.close()
        ser.close()

if __name__ == "__main__":
    main()
