#include <Arduino.h>
// Needed adding `lib_deps = arduino-libraries/Servo` to platformio.ini —
// unlike Arduino IDE, PlatformIO doesn't bundle Servo automatically and
// failed to compile (Servo.h not found) until it was declared explicitly.
#include <Servo.h>

#define SERVO_PIN 9  // Servo 1 (claw) per Hashim's PCB pin map

Servo claw;

int angle = 0;
int step = 1;
unsigned long lastStepTime = 0;
const unsigned long stepIntervalMs = 15;  // time between each 1-degree step

void setup() {
  claw.attach(SERVO_PIN);
}

// No delay() anywhere — instead, check "has enough time passed since the
// last step" every time this is called. Keeps loop() free to also handle
// serial commands, other actuators, etc. without waiting on the servo.
void sweep() {
  unsigned long now = millis();
  if (now - lastStepTime >= stepIntervalMs) {
    lastStepTime = now;

    angle += step;
    if (angle >= 180 || angle <= 0) {
      step = -step;  // hit an end — reverse direction
    }

    claw.write(angle);
  }
}

void loop() {
  claw.write(60);
  // 10 claw is fully open
  // 60 claw is fully closed
}
