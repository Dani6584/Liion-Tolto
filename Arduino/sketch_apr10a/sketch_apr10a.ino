// Arduino Mega kód a 18650 cella válogatóhoz
// 4 csatornás ACS712 DC árammérő és feszültségmérő

const int chargePin = A0;       // Töltőáram bemenet
const int dischargePin = A1;    // Kisütőáram bemenet
const int dischargeVoltagePin = A2; // Kisütő feszültség bemenet
const int chargerAVoltagePin = A3;  // A töltő feszültség
const int chargerBVoltagePin = A4;  // B töltő feszültség
unsigned  int a,b,c,d;
const float vRef = 5.0;          // Arduino tápfeszültség
const float sensitivity = 0.185; // ACS712 5A modul érzékenység (185 mV/A)
double voltage;
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
  if (Serial.available() > 0) {
    String receivedPacket = Serial.readStringUntil('\n');
    receivedPacket.trim();

    if (receivedPacket == "SEND_DATA") {
      noTone(3);
      delay(10);
      
      // Mérések elvégzése
      a=analogRead(dischargeVoltagePin);
      delay(5);
      b=analogRead(chargerAVoltagePin);
      delay(5);
      c=analogRead(chargerBVoltagePin);
      
      double chargeCurrent = measureCurrent(chargePin, zeroCharge);
      double dischargeCurrent = measureCurrent(dischargePin, zeroDischarge);
      double dischargeVoltage = measureVoltage(dischargeVoltagePin);
      double chargerAVoltage = measureVoltage(chargerAVoltagePin);
      double chargerBVoltage = measureVoltage(chargerBVoltagePin);

      // JSON formátumú adat küldése egyetlen sorban a soros portra plusz új sor
      jsonData = "{\"charge\":" + String(chargeCurrent, 2) + ", \"discharge\":" + String(dischargeCurrent, 2) +
                      ", \"discharge_voltage\":" + String(a * (5.01 / 1023), 2) + ", \"chargerA_voltage\":" + String(b * (5.01 / 1023), 2) +
                      ", \"chargerB_voltage\":" + String(c * (5.01 / 1023), 2) + "}";
      Serial.println(jsonData);
      Serial.flush();

      delay(1000);
      tone(3,100);
    }
    
  }
  
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
double measureCurrent(int pin, int zero) {
  voltage=0;
  const int samples = 50;
/*
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }*/

 // float avgValue = sum / (float)samples;

  // Feszültség kiszámítása
  voltage = (double)analogRead(pin) * (vRef / 1023.0);

  // Áram kiszámítása milliamperben
  double current = (double)((voltage - (zero * vRef / 1023.0)) / sensitivity) * 1000;

  return current;
}


// 🔋 Feszültség mérése DC-ben (átlagolással)
float measureVoltage(int pin) {
 voltage=0;
 // const int samples = 50;
/*
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }*/

  //double avgValue = sum / (float)samples;
  
  //double avgValue = analogRead(pin);
  // Feszültség kiszámítása
  voltage = (double)analogRead(pin) * ((double)vRef / 1023.0);

  return voltage;
}
