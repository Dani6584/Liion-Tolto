void setup() {
  Serial.begin(9600);
  tone(3, 100);
}

void loop() {
  Serial.println(5);
  Serial.flush();

  delay(1000);
}
