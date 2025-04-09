// Arduino Mega kód a 18650 cella válogatóhoz
// 4 csatornás ACS712 DC árammérő és feszültségmérő

const int chargePin = A0;       // Töltőáram bemenet
const int dischargePin = A1;    // Kisütőáram bemenet
const int dischargeVoltagePin = A2; // Kisütő feszültség bemenet
const int chargerAVoltagePin = A3;  // A töltő feszültség
const int chargerBVoltagePin = A4;  // B töltő feszültség

const float vRef = 5.0;          // Arduino tápfeszültség
const float sensitivity = 0.185; // ACS712 5A modul érzékenység (185 mV/A)

int zeroCharge = 512;            // Nullpont a töltő szenzornak
int zeroDischarge = 512;         // Nullpont a kisütő szenzornak

String jsonData="";
void setup() {
  Serial.begin(9600);
  // Nullpont kalibrálása mindkét áramérzékelő szenzorra
  zeroCharge = calibrateACS712(chargePin);
  zeroDischarge = calibrateACS712(dischargePin);

  //Serial.print("Charge nullpont: "); Serial.println(zeroCharge);
  //Serial.print("Discharge nullpont: "); Serial.println(zeroDischarge);
  tone(3, 100);
}

void loop() {
  // Mérések elvégzése
  float chargeCurrent = measureCurrent(chargePin, zeroCharge);
  float dischargeCurrent = measureCurrent(dischargePin, zeroDischarge);
  float dischargeVoltage = measureVoltage(dischargeVoltagePin);
  float chargerAVoltage = measureVoltage(chargerAVoltagePin);
  float chargerBVoltage = measureVoltage(chargerBVoltagePin);
  
  float chargerAVoltageArray = measureVoltageArray(chargerAVoltagePin);

  // JSON formátumú adat küldése egyetlen sorban a soros portra plusz új sor
  //jsonData = "{\"charge\":" + String(chargeCurrent, 2) + ", \"discharge\":" + String(dischargeCurrent, 2) +
  //                   ", \"discharge_voltage\":" + String(dischargeVoltage, 2) + ", \"chargerA_voltage\":" + String(chargerAVoltage, 2) +
  //                   ", \"chargerB_voltage\":" + String(chargerBVoltage, 2) + "}";

  jsonData = "{\"chargerA_voltage\":" + String(chargerAVoltage, 2) + ", \"chargerA_voltageArray\":" + String(chargerAVoltageArray, 2) + "}";

  Serial.println(jsonData);
  Serial.flush();

  delay(1000);
}

// 🌟 Nullpont kalibráció (átlagolással)
int calibrateACS712(int pin) {
  long sum = 0;
  const int samples = 100;

  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }

  return sum / samples;
}

// ⚡ Áram mérése DC-ben (átlagolással)
float measureCurrent(int pin, int zero) {
  long sum = 0;
  const int samples = 50;

  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }

  float avgValue = sum / (float)samples;

  // Feszültség kiszámítása
  float voltage = avgValue * (vRef / 1023.0);

  // Áram kiszámítása milliamperben
  float current = ((voltage - (zero * vRef / 1023.0)) / sensitivity) * 1000;

  return current;
}

// 🔋 Feszültség mérése DC-ben (átlagolással)
float measureVoltage(int pin) {
  long sum = 0;
  const int samples = 50;

  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }

  float avgValue = sum / (float)samples;

  // Feszültség kiszámítása
  float voltage = avgValue * (vRef / 1023.0);

  return voltage;
}

float measureVoltageArray(int pin) {
  const int samples = 50;
  float tomb[50];
  for (int i = 0; i < samples; i++) {
    tomb[i] = analogRead(pin);
    delay(5);
  }

  return tomb;
}