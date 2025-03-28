import os
import time
import json
import socket
import glob
import subprocess
import requests
import serial
from datetime import datetime
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

# 🌱 Load .env
load_dotenv()

# 🔁 Internet check
def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False

for _ in range(60):
    if is_connected():
        break
    print("🌐 Waiting for internet...")
    time.sleep(5)
else:
    print("❌ No internet after 5 minutes. Exiting.")
    exit(1)

def auto_update():
    repo_dir = "/home/pi/liion/Liion-Tolto"
    try:
        subprocess.run(["git", "pull"], cwd=repo_dir, check=True)
        print("✅ Code updated from Git.")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Auto-update failed: {e}")


auto_update()

# 🌍 Appwrite config
BASE_URL = os.environ.get("APPWRITE_BASE_URL", "https://appwrite.tsada.edu.rs/v1")
HEADERS = {
    "Content-Type": "application/json",
    "X-Appwrite-Project": os.environ.get("APPWRITE_PROJECT_ID", "67a5b2fd0036cbf53dbf"),
    "X-Appwrite-Key": os.environ.get("APPWRITE_API_KEY", "")
}

DATABASE_ID = "67a5b54c00004b1a93d7"
RPI_LOGGING_COLLECTION = "67dfc9720019d64746b0"
HARDWARE_FLAGS_COLLECTION = "67de7e600036fcfc5959"
CHARGE_COLLECTION = "67d18e17000dc1b54f39"
DISCHARGE_COLLECTION = "67ac8901003b19f4ca35"
BATTERY_COLLECTION = "67a5b55b002eceac9c33"

# ⚙️ Serial + PLC
BAUD_RATE = int(os.environ.get("BAUD_RATE", "9600"))
PLC_IP = os.environ.get("PLC_IP", "192.168.1.5")
PLC_PORT = int(os.environ.get("PLC_PORT", "502"))
ROTATE_ON_TIME = float(os.environ.get("ROTATE_ON_TIME", 1))
ROTATE_OFF_TIME = float(os.environ.get("ROTATE_OFF_TIME", 2))

MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5

STATUS_TO_POSITION = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 9: 5}
current_position = 0

# 🔌 Serial auto-detect
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")

def find_serial_port():
    ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
    return ports[0] if ports else None

def open_serial_port():
    global SERIAL_PORT
    try:
        return serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    except FileNotFoundError:
        print(f"⚠️ Serial port {SERIAL_PORT} not found, trying auto-detect...")
        SERIAL_PORT = find_serial_port()
        if SERIAL_PORT:
            print(f"✅ Found serial port: {SERIAL_PORT}")
            try:
                return serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            except Exception as e:
                print(f"❌ Failed to open auto-detected port: {e}")
        else:
            print("❌ No serial ports found.")
    except Exception as e:
        print(f"❌ Serial port open error: {e}")
    return None

# 📝 Appwrite logging
def log_to_appwrite(message):
    try:
        requests.post(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{RPI_LOGGING_COLLECTION}/documents",
            headers=HEADERS,
            json={"data": {"MESSAGE": f"{datetime.now().isoformat()} – {message}"}}
        )
    except Exception as e:
        print(f"Logging failed: {e}")

def get_setting(setting_name):
    try:
        r = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{HARDWARE_FLAGS_COLLECTION}/documents"
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

def do_loading_step(client, bid):
    log_to_appwrite(f"📦 Loading cell: {bid}")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 1)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, 0)
    update_battery_status(bid, {"operation": 1})

def do_voltage_measure_step(ser, bid):
    voltage, _, _ = measure_from_serial(ser)
    if voltage is not None:
        if voltage < 2.5:
            update_battery_status(bid, {"feszultseg": voltage, "status": 9, "operation": 0})
            log_to_appwrite("⚠️ Voltage < 2.5V → BAD CELL")
        else:
            update_battery_status(bid, {"feszultseg": voltage, "operation": 1})

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

def do_output_step(client, bid, good=True):
    coil = MODBUS_OUTPUT_GOOD_EJECT if good else MODBUS_OUTPUT_BAD_EJECT
    client.write_coil(coil, 1)
    time.sleep(2)
    client.write_coil(coil, 0)
    update_battery_status(bid, {"operation": 1})

# 🚀 Main
def main():
    global current_position
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    ser = open_serial_port()
    if not ser:
        log_to_appwrite("❌ Failed to open serial port. Exiting.")
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
    auto_update()
    main()
