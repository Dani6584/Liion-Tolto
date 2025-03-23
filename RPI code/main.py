import os
import time
import requests
import serial
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

# .env betöltés
load_dotenv()

# 🌐 Appwrite adatok
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

# 💡 Modbus beállítások
PLC_IP = os.environ.get("PLC_IP", "192.168.1.5")
PLC_PORT = int(os.environ.get("PLC_PORT", "502"))

# 💬 Serial beállítások
SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM1")
BAUD_RATE = int(os.environ.get("BAUD_RATE", "9600"))

# Modbus kimenetek
MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3
MODBUS_OUTPUT_CHARGE_SWITCH = 4
MODBUS_OUTPUT_DISCHARGE = 5
MODBUS_INPUT_POSITION_SWITCH = 3

# 💬 Logolás Appwrite-ba
def log_to_appwrite(message):
    try:
        url = f"{BASE_URL}/databases/{DATABASE_ID}/collections/67dfc9720019d64746b0/documents"
        requests.post(url, json={"data": {"MESSAGE": message}}, headers=HEADERS)
        print(f"📝 {message}")
    except Exception as e:
        print(f"❌ Log hiba: {e}")

# 🔁 Revolver pozíció státusz szerint
STATUS_TO_POSITION = {
    1: 0,
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    7: 5,
    9: 6
}

# 🔃 Forgatás a kívánt pozícióba
def initialize_position(client):
    try:
        res = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{SETTINGS_COLLECTION}/documents"
            f"?queries[]=equal(\"setting_name\",\"ACTIVE_CELL_ID\")&queries[]=limit(1)",
            headers=HEADERS
        )
        doc = res.json()["documents"][0]
        cell_id = doc["setting_data"]
        bat = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{cell_id}",
            headers=HEADERS
        ).json()
        status = int(bat.get("status", 0))
        pos = STATUS_TO_POSITION.get(status, 0)
        for _ in range(pos):
            client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, True)
            time.sleep(1)
            client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, False)
            time.sleep(2)
        log_to_appwrite(f"✅ Revolver pozícióba forgatva: {pos} (status: {status})")
        return pos
    except Exception as e:
        log_to_appwrite(f"⚠️ Pozíció inicializálás hiba: {e}")
        return 0

# 🧠 Appwrite lekérések
def get_active_cell_id():
    try:
        res = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{SETTINGS_COLLECTION}/documents"
            f"?queries[]=equal(\"setting_name\",\"ACTIVE_CELL_ID\")&queries[]=limit(1)",
            headers=HEADERS
        )
        doc = res.json()["documents"][0]
        return doc["setting_data"] if doc else None
    except:
        return None

def get_battery_by_id(bid):
    try:
        res = requests.get(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{bid}",
            headers=HEADERS
        )
        return res.json()
    except:
        return None

def update_battery_status(bid, data):
    try:
        requests.patch(
            f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{bid}",
            json={"data": data}, headers=HEADERS
        )
    except:
        log_to_appwrite(f"⚠️ Akkumulátor frissítési hiba: {bid}")

# ✅ Folyamatlépések
def do_loading_step(client, bid):
    log_to_appwrite(f"➡️ Betöltés indítása ({bid})")
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, True)
    time.sleep(2)
    client.write_coil(MODBUS_OUTPUT_BATTERY_LOADER, False)
    update_battery_status(bid, {"operation": 1})

def do_output_step(client, bid, good=True):
    log_to_appwrite(f"➡️ Cella kiadása ({'jó' if good else 'rossz'})")
    coil = MODBUS_OUTPUT_GOOD_EJECT if good else MODBUS_OUTPUT_BAD_EJECT
    client.write_coil(coil, True)
    time.sleep(2)
    client.write_coil(coil, False)
    client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, True)
    time.sleep(1)
    client.write_coil(MODBUS_OUTPUT_PWM_ENABLE, False)
    time.sleep(2)
    update_battery_status(bid, {"operation": 1})

def do_discharge_step(client, bid):
    log_to_appwrite(f"⚡ Merítés aktiválva")
    client.write_coil(MODBUS_OUTPUT_DISCHARGE, True)
    update_battery_status(bid, {"operation": 1})

def do_charge_step(client, bid):
    log_to_appwrite("🔋 Töltés indítása")
    update_battery_status(bid, {"operation": 1})

def do_recharge_step(client, bid):
    log_to_appwrite("🔁 Visszatöltés indítása")
    update_battery_status(bid, {"operation": 1})

def do_voltage_measure_step(ser, bid, client):
    ser.write(b"MEASURE\n")
    time.sleep(2)
    line = ser.readline().decode(errors='ignore').strip()
    if line:
        try:
            data = eval(line)
            voltage = float(data.get("voltage", 0.0))
            update_battery_status(bid, {"feszultseg": voltage, "operation": 1})
            log_to_appwrite(f"🔍 Feszültség mérve: {voltage}V")
            if voltage < 2.5:
                update_battery_status(bid, {"status": 9, "operation": 0})
                log_to_appwrite("⚠️ Feszültség < 2.5V → hibás cella")
        except Exception as e:
            log_to_appwrite(f"❌ Fesz mérési hiba: {e}")

# 🧠 Főprogram
def main():
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)

    if not client.connect():
        log_to_appwrite("❌ Modbus kapcsolat hiba.")
        return

    initialize_position(client)

    try:
        while True:
            active_id = get_active_cell_id()
            if not active_id:
                time.sleep(3)
                continue

            battery = get_battery_by_id(active_id)
            if not battery:
                time.sleep(3)
                continue

            status = battery.get("status", 0)
            operation = battery.get("operation", 0)

            if operation != 0:
                time.sleep(2)
                continue

            if status == 1:
                do_loading_step(client, active_id)
            elif status == 2:
                do_voltage_measure_step(ser, active_id, client)
            elif status == 3:
                do_charge_step(client, active_id)
            elif status == 4:
                do_discharge_step(client, active_id)
            elif status == 5:
                do_recharge_step(client, active_id)
            elif status == 7:
                do_output_step(client, active_id, good=True)
            elif status == 9:
                do_output_step(client, active_id, good=False)

            time.sleep(1)

    except KeyboardInterrupt:
        log_to_appwrite("🛑 Leállítás")
    finally:
        client.close()
        ser.close()

if __name__ == "__main__":
    main()
