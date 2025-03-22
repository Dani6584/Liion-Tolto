import os
import time
import requests
from pymodbus.client import ModbusTcpClient
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("APPWRITE_BASE_URL", "https://appwrite.tsada.edu.rs/v1")
PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID", "67a5b2fd0036cbf53dbf")
API_KEY = os.getenv("APPWRITE_API_KEY", "")

DATABASE_ID = os.getenv("APPWRITE_DATABASE_ID", "67a5b54c00004b1a93d7")
BATTERY_COLLECTION = os.getenv("APPWRITE_PRIMARY_COLLECTION", "67a5b55b002eceac9c33")
SETTINGS_COLLECTION = os.getenv("APPWRITE_SETTINGS_COLLECTION", "67de7e600036fcfc5959")

HEADERS = {
    "X-Appwrite-Project": PROJECT_ID,
    "X-Appwrite-Key": API_KEY,
    "Content-Type": "application/json"
}

PLC_IP = os.getenv("PLC_IP", "192.168.1.5")
PLC_PORT = int(os.getenv("PLC_PORT", 502))

MODBUS_OUTPUT_PWM_ENABLE = 0
MODBUS_OUTPUT_BATTERY_LOADER = 1
MODBUS_OUTPUT_BAD_EJECT = 2
MODBUS_OUTPUT_GOOD_EJECT = 3

def modbus_pulse(client, output, duration=1):
    client.write_coil(output, True)
    time.sleep(duration)
    client.write_coil(output, False)
    print(f"⚙️ Kimenet {output} aktiválva {duration} mp-re.")

def control_valve(client, valve_name):
    outputs = {
        "load": MODBUS_OUTPUT_BATTERY_LOADER,
        "good": MODBUS_OUTPUT_GOOD_EJECT,
        "bad": MODBUS_OUTPUT_BAD_EJECT
    }
    if valve_name in outputs:
        print(f"💨 Szelep aktiválva: {valve_name}")
        modbus_pulse(client, outputs[valve_name], 3)

def get_active_cell_id():
    url = f"{BASE_URL}/databases/{DATABASE_ID}/collections/{SETTINGS_COLLECTION}/documents"
    params = {"queries[]": 'equal("setting_name", "ACTIVE_CELL_ID")'}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        docs = response.json().get("documents", [])
        if docs:
            return docs[0].get("setting_data", ""), docs[0].get("$id", "")
    return "", ""

def get_cell_data(cell_id):
    url = f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{cell_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

def update_cell_operation(cell_id, op=1):
    url = f"{BASE_URL}/databases/{DATABASE_ID}/collections/{BATTERY_COLLECTION}/documents/{cell_id}"
    payload = {"operation": op}
    requests.patch(url, headers=HEADERS, json=payload)
    print(f"✅ Operation {op} beállítva a cellának: {cell_id}")

def main():
    client = ModbusTcpClient(PLC_IP, port=PLC_PORT)
    if not client.connect():
        print("❌ Modbus kapcsolat sikertelen.")
        return

    print("🔁 Raspberry végrehajtó elindult.")
    try:
        while True:
            cell_id, setting_doc_id = get_active_cell_id()
            if not cell_id:
                print("⏳ Nincs aktív cella.")
                time.sleep(3)
                continue

            cell = get_cell_data(cell_id)
            if not cell:
                print("⚠️ Cellát nem sikerült lekérdezni.")
                time.sleep(3)
                continue

            status = cell.get("status")
            operation = cell.get("operation", 1)

            if operation != 0:
                print("⏳ Cellán már dolgoznak vagy végzett.")
                time.sleep(3)
                continue

            print(f"📦 Feldolgozás alatt: {cell_id} | status: {status}")

            if status == 1:
                print("🔄 Betöltés...")
                control_valve(client, "load")
                modbus_pulse(client, MODBUS_OUTPUT_PWM_ENABLE)
                update_cell_operation(cell_id)

            elif status == 7:
                print("✅ Jó cella kiadása...")
                control_valve(client, "good")
                modbus_pulse(client, MODBUS_OUTPUT_PWM_ENABLE)
                update_cell_operation(cell_id)

            elif status == 9:
                print("❌ Rossz cella kiadása...")
                control_valve(client, "bad")
                modbus_pulse(client, MODBUS_OUTPUT_PWM_ENABLE)
                update_cell_operation(cell_id)

            else:
                print("📛 Nincs hozzárendelve akció ehhez a státuszhoz.")
                time.sleep(3)

            time.sleep(2)

    except KeyboardInterrupt:
        print("🛑 Leállítás kérése...")

    finally:
        client.close()
        print("🔌 Modbus kapcsolat bontva.")

if __name__ == "__main__":
    main()
