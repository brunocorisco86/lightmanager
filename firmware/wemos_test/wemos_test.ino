// Firmware de Teste: Alternância de Canais (D1 vs D2)
// Quando D1 está HIGH, D2 está LOW, e vice-versa.

const int pin1 = D1; // GPIO 5
const int pin2 = D2; // GPIO 4

void setup() {
  pinMode(pin1, OUTPUT);
  pinMode(pin2, OUTPUT);
}

void loop() {
  // Estado 1: D1 Ligado, D2 Desligado
  digitalWrite(pin1, HIGH);
  digitalWrite(pin2, LOW);
  delay(2000);

  // Estado 2: D1 Desligado, D2 Ligado
  digitalWrite(pin1, LOW);
  digitalWrite(pin2, HIGH);
  delay(2000);
}
