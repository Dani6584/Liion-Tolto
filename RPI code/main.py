import os
import time
import json
import requests
import serial
from datetime import datetime
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

# 🌱 Load environment variables
load_dotenv()
BASE_URL = os.environ.get("APPWRITE_BASE_URL", "https://appwrite.tsada.edu.rs/v1")
HEADERS = {
    "Content-Type": "application/json",
    "X-Appwrite-Project": os.environ.get("APPWRITE_PROJECT_ID", "67a5b2fd0036cbf53dbf"),
    "X-Appwrite-Key": os.environ.get("APPWRITE_API_KEY", "")
}

# 📦 Appwrite Collections
DATABASE_ID = "67a5b54c00004b1a93d7"
BATTERY_COLLECTION = "67a5b55b002eceac9c33"
SETTINGS_COLLECTION = "67de7e600036fcfc5959"
CHARGE_COLLECTION = "67d18e17000dc1b54f39"
DISCHARGE_COLLECTION = "67ac8901003b19f4ca35"
BATTERY_COLLECTION = "67a5b55b002eceac9c33"

# ⚙️ PLC & Serial
PLC_IP = os.environ.get("PLC_IP", "192.168.1.5")
PLC_PORT = int(os.environ.get("PLC_PORT", "502"))
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = int(os.environ.get("BAUD_RATE", "9600"))

# Modbus outputs
MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5

# 🔁 Status to revolver position
STATUS_TO_POSITION = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 9: 5}
current_position = 0

# 📝 Log helper
def log_to_appwrite(message):
    try:
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
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{SETTINGS_COLLECTION}/documents"
            f"?queries[]=equal(\"setting_name\",\"{setting_name}\")&queries[]=limit(1)",
            headers=HEADERS
        )
        if r.status_code == 200:
            return r.json()["documents"][0]
    except Exception as e:
        log_to_appwrite(f"⚠️ Error fetching setting {setting_name}: {e}")
    return None

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

def update_battery_status(bid, data):
    try:
        requests.patch(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{bid}",
            headers=HEADERS, json={"data": data}
        )
    except Exception as e:
        log_to_appwrite(f"⚠️ Battery update failed: {e}")


def save_measurement_to_appwrite(collection_id, battery_id, voltage, current=None, open_circuit=False, mode=1):
    try:
        payload = {
            "battery": battery_id,
            "voltage": voltage,
            "open_circuit": open_circuit,
            "mode": mode
        }
        if current is not None:
            if collection_id == CHARGE_COLLECTION:
                payload["chargecurrent"] = current
            elif collection_id == DISCHARGE_COLLECTION:
                payload["dischargecurrent"] = current

        r = requests.post(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{collection_id}/documents",
            headers=HEADERS, json={"data": payload}
        )
        if r.status_code == 201:
            log_to_appwrite(f"📤 Measurement saved: {voltage:.2f}V {'(open)' if open_circuit else '(load)'}")
    except Exception as e:
        log_to_appwrite(f"❌ Save error: {e}")

# ⚙️ Egyes lépések
def do_loading_step(client, bid):
    log_to_appwrite(f"📦 Loading cell: {bid}")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 1)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
    update_battery_status(bid, {"operation": 1})


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

    client.write_coil(MODBUS_OUTPUT_DISCHARGE, 1)
    time.sleep(2)

    voltage, current, _ = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage, current, False, mode)
    update_battery_status(bid, {"operation": 1})

def do_recharge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, False, mode)
    update_battery_status(bid, {"operation": 1})


def do_recharge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, False, mode)
    update_battery_status(bid, {"operation": 1})

# 🚀 Main loop
def main():
    global current_position
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        log_to_appwrite(f"❌ Serial port open failed: {e}")
        return

    if not client.connect():
        log_to_appwrite("❌ Modbus connection failed")
        return

    try:
        while True:
            cell_id = get_active_cell_id()
            if not cell_id:
                log_to_appwrite("🔍 No active cell ID found.")
                time.sleep(3)
                continue

            bat = get_battery_by_id(cell_id)
            if not bat:
                log_to_appwrite(f"⚠️ Battery ID '{cell_id}' not found.")
                time.sleep(3)
                continue

            status = bat.get("status", 0)
            operation = bat.get("operation", 0)
            if operation != 0:
                log_to_appwrite(f"⏳ Battery {cell_id} is still processing. Skipping.")
                time.sleep(2)
                continue

            log_to_appwrite(f"⚙️ Performing action for battery {cell_id} with status {status}")

            if status in STATUS_TO_POSITION:
                rotate_to_position(client, STATUS_TO_POSITION[status])

            if status == 1:
                do_loading_step(client, cell_id)
            elif status == 2:
                do_voltage_measure_step(ser, cell_id)
            elif status == 3:
                do_charge_step(client, cell_id, ser)
            elif status == 4:
                do_discharge_step(client, cell_id, ser)
            elif status == 5:
                do_recharge_step(client, cell_id, ser)
            elif status == 7:
                do_output_step(client, cell_id, good=True)
            elif status == 9:
                do_output_step(client, cell_id, good=False)

            time.sleep(1)

    except KeyboardInterrupt:
        log_to_appwrite("🛑 Script terminated by user.")
    finally:
        client.close()
        ser.close()

if __name__ == "__main__":
    main()
