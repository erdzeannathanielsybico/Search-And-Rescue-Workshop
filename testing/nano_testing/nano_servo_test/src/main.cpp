// Hardware: Arduino Nano (ATmega328P, new bootloader) + claw servo
//
// Claw servo test. Slowly toggles the claw between its open and closed
// positions on a timer so you can watch the mechanism travel and confirm
// the endpoints don't bind. Uses the actual open/closed angles found for
// this specific claw — NOT 0/180.

#include <Arduino.h>
// PlatformIO doesn't bundle Servo like the Arduino IDE does — it's declared
// in platformio.ini (lib_deps) or this include won't resolve.
#include <Servo.h>

#define CLAW_SERVO_PIN 9  // Servo 1 (claw) per Hashim's PCB pin map

// Endpoints found by testing this exact claw — driving past these risks
// stalling the servo against the mechanism. Open first in setup() so the
// claw never powers up clamped shut.
#define CLAW_OPEN_ANGLE  10
#define CLAW_CLOSE_ANGLE 60

Servo claw;

// Non-blocking toggle: no delay() in loop(), so this pattern drops straight
// into the combined firmware where the claw has to share the loop with
// serial handling and the motors.
const unsigned long TOGGLE_INTERVAL_MS = 2000;
unsigned long lastToggleTime = 0;
bool clawOpen = true;

void setup() {
  Serial.begin(115200);
  claw.attach(CLAW_SERVO_PIN);
  claw.write(CLAW_OPEN_ANGLE);  // NEVER FORGET OR ELSE SERVO WILL BREAK
  Serial.println("Setup complete. Starting servo test...");
}

void loop() {
  unsigned long now = millis();
  if (now - lastToggleTime >= TOGGLE_INTERVAL_MS) {
    lastToggleTime = now;

    clawOpen = !clawOpen;
    if (clawOpen) {
      claw.write(CLAW_OPEN_ANGLE);
      Serial.println("CLAW,OPEN");
    } else {
      claw.write(CLAW_CLOSE_ANGLE);
      Serial.println("CLAW,CLOSE");
    }
  }
}
