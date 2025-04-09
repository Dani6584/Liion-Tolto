String jsonData="";
void setup() {
  Serial.begin(9600);
  tone(3, 100);
}

void loop() {
  // Mérések elvégzése
  float chargeCurrent = 1.5;
  float dischargeCurrent = 2.5;
  float dischargeVoltage = 3.5;
  float chargerAVoltage = 4.5;
  float chargerBVoltage = 5.5;

  // JSON formátumú adat küldése egyetlen sorban a soros portra plusz új sor
   jsonData = "{\"charge\":" + String(chargeCurrent, 2) + ", \"discharge\":" + String(dischargeCurrent, 2) +
                     ", \"discharge_voltage\":" + String(dischargeVoltage, 2) + ", \"chargerA_voltage\":" + String(chargerAVoltage, 2) +
                     ", \"chargerB_voltage\":" + String(chargerBVoltage, 2) + "}";
  Serial.println(jsonData);
  Serial.flush();

  delay(1000);
}
