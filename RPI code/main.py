import os
import time
import requests
import serial
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

# 🔧 .env betöltés
load_dotenv()

# Appwrite
BASE_URL = os.environ.get("APPWRITE_BASE_URL", "https://appwrite.tsada.edu.rs/v1")
HEADERS = {
    "Content-Type": "application/json",
    "X-Appwrite-Project": os.environ.get("APPWRITE_PROJECT_ID", "67a5b2fd0036cbf53dbf"),
    "X-Appwrite-Key": os.environ.get("APPWRITE_API_KEY", "")
}
DATABASE_ID = "67a5b54c00004b1a93d7"
BATTERY_COLLECTION = "67a5b55b002eceac9c33"
SETTINGS_COLLECTION = "67de7e600036fcfc5959"
CHARGE_COLLECTION = "67d18e17000dc1b54f39"
DISCHARGE_COLLECTION = "67ac8901003b19f4ca35"

# Modbus
PLC_IP = os.environ.get("PLC_IP", "192.168.1.5")
PLC_PORT = int(os.environ.get("PLC_PORT", "502"))
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = int(os.environ.get("BAUD_RATE", "9600"))

# Kimenetek
MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5

# Státusz → pozíció
STATUS_TO_POSITION = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 7: 5, 9: 6}

def log_to_appwrite(message):
    try:
        requests.post(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/67dfc9720019d64746b0/documents",
            headers=HEADERS,
            json={"data": {"MESSAGE": message}}
        )
        print(f"📝 {message}")
    except Exception as e:
        print(f"❌ Log error: {e}")

def rotate_position(client):
    client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, True)
    time.sleep(1)
    client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, False)
    time.sleep(2)
    log_to_appwrite("🔄 Revolver forgatva 1 pozícióval")

def get_active_cell_id():
    try:
        r = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{SETTINGS_COLLECTION}/documents"
            f"?queries[]=equal(\"setting_name\",\"ACTIVE_CELL_ID\")&queries[]=limit(1)",
            headers=HEADERS
        )
        return r.json()["documents"][0]["setting_data"]
    except:
        return None

def get_battery_by_id(bid):
    try:
        r = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{bid}",
            headers=HEADERS
        )
        return r.json()
    except:
        return None

def update_battery_status(bid, data):
    try:
        requests.patch(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{bid}",
            headers=HEADERS, json={"data": data}
        )
    except:
        log_to_appwrite(f"⚠️ Akkumulátor frissítés hiba: {bid}")

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
            print(f"📤 Mentve: {collection_id} – {voltage:.2f} V")
    except Exception as e:
        print(f"❌ Mentés hiba: {e}")

def measure_from_serial(ser):
    try:
        ser.write(b"MEASURE\n")
        time.sleep(2)
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            data = eval(line)
            voltage = float(data.get("voltage", 0.0))
            current = float(data.get("current", 0.0))
            mode = int(data.get("mode", 1))
            return voltage, current, mode
    except Exception as e:
        log_to_appwrite(f"⚠️ Mérési hiba: {e}")
    return None, None, None

def do_loading_step(client, bid):
    log_to_appwrite(f"📦 Cellabetöltés ({bid})")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, True)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, False)
    update_battery_status(bid, {"operation": 1})

def do_output_step(client, bid, good=True):
    coil = MODBUS_OUTPUT_GOOD_EJECT if good else MODBUS_OUTPUT_BAD_EJECT
    client.write_coil(coil, True)
    time.sleep(2)
    client.write_coil(coil, False)
    rotate_position(client)
    update_battery_status(bid, {"operation": 1})

def do_discharge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(DISCHARGE_COLLECTION, bid, voltage, current, open_circuit=False, mode=mode)
    client.write_coil(MODBUS_OUTPUT_DISCHARGE, True)
    update_battery_status(bid, {"operation": 1})

def do_charge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, open_circuit=False, mode=mode)
    update_battery_status(bid, {"operation": 1})

def do_recharge_step(client, bid, ser):
    voltage, current, mode = measure_from_serial(ser)
    if voltage:
        save_measurement_to_appwrite(CHARGE_COLLECTION, bid, voltage, current, open_circuit=False, mode=mode)
    update_battery_status(bid, {"operation": 1})

def do_voltage_measure_step(ser, bid):
    voltage, _, _ = measure_from_serial(ser)
    if voltage is not None:
        update_battery_status(bid, {"feszultseg": voltage, "operation": 1})
        log_to_appwrite(f"🔍 Feszültség: {voltage:.2f} V")
        if voltage < 2.5:
            update_battery_status(bid, {"status": 9, "operation": 0})
            log_to_appwrite("⚠️ < 2.5V → hibás cella")

def initialize_position(client):
    try:
        cell_id = get_active_cell_id()
        bat = get_battery_by_id(cell_id)
        pos = STATUS_TO_POSITION.get(bat.get("status", 0), 0)
        for _ in range(pos):
            rotate_position(client)
    except Exception as e:
        log_to_appwrite(f"⚠️ Pozíció inicializálás hiba: {e}")

# 🚀 Fő ciklus
def main():
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)

    if not client.connect():
        log_to_appwrite("❌ Modbus kapcsolat hiba.")
        return

    initialize_position(client)

    try:
        while True:
            cell_id = get_active_cell_id()
            if not cell_id:
                time.sleep(3)
                continue

            bat = get_battery_by_id(cell_id)
            if not bat:
                time.sleep(3)
                continue

            status = bat.get("status", 0)
            operation = bat.get("operation", 0)

            if operation != 0:
                time.sleep(2)
                continue

            if status == 1:
                do_loading_step(client, cell_id)
                rotate_position(client)
            elif status == 2:
                do_voltage_measure_step(ser, cell_id)
                rotate_position(client)
            elif status == 3:
                do_charge_step(client, cell_id, ser)
                rotate_position(client)
            elif status == 4:
                do_discharge_step(client, cell_id, ser)
                rotate_position(client)
            elif status == 5:
                do_recharge_step(client, cell_id, ser)
                rotate_position(client)
            elif status == 7:
                do_output_step(client, cell_id, good=True)
            elif status == 9:
                do_output_step(client, cell_id, good=False)

            time.sleep(1)

    except KeyboardInterrupt:
        log_to_appwrite("🛑 Leállítás")
    finally:
        client.close()
        ser.close()

if __name__ == "__main__":
    main()
