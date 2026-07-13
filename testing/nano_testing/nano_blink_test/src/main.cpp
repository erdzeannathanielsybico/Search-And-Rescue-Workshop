// Hardware: Arduino Nano (ATmega328P, new bootloader)
//
// Simplest possible sanity check — proves the board is alive, the correct
// PlatformIO env is selected, and uploads are landing before moving on to
// any of the other nano_testing projects. If this doesn't blink, nothing
// else will work either.

#include <Arduino.h>

// The Nano's on-board LED sits on D13. Note that on Hashim's PCB pin map D13
// is also the ultrasonic ECHO pin — that's fine for this standalone blink
// (nothing else is wired), but don't run this sketch with the sensor board
// attached expecting the echo line to behave.
#define LED_PIN LED_BUILTIN  // = D13 on the Nano

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  Serial.println("Setup complete. Starting blink test...");
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  Serial.println("ON");
  delay(1000);

  digitalWrite(LED_PIN, LOW);
  Serial.println("OFF");
  delay(1000);
}
