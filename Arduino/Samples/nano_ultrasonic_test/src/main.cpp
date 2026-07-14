// Hardware: Arduino Nano (ATmega328P, new bootloader) + HC-SR04
//
// Ultrasonic distance test. Prints the measured distance in cm to serial a
// few times a second so you can confirm the HC-SR04 wiring, the trig/echo
// pins, and the timeout behaviour before this feeds the automatic
// grab-and-revert logic in the combined firmware.

#include <Arduino.h>

// --- Pin map from Hashim's PCB design ---
#define ULTRASONIC_TRIG_PIN 2
#define ULTRASONIC_ECHO_PIN 13

// MODE + DISTANCE are reported on a fixed cadence in the real firmware; here
// we just poll distance. 100ms also respects the HC-SR04's own limit:
// pinging it faster than ~60ms apart lets the previous echo bleed into the
// next reading.
const unsigned long REPORT_INTERVAL_MS = 100;
unsigned long lastReportTime = 0;

// pulseIn() blocks until the echo returns or this timeout expires — kept
// tight (~1m round trip) so a sensor with nothing in range can't stall the
// loop for long. Anything past ~1m doesn't matter for "close enough to
// grab" anyway.
const unsigned long ULTRASONIC_ECHO_TIMEOUT_US = 6000;

// The distance the combined firmware treats as "close enough to grab" and
// trip the auto grab-and-revert. Flagged here so you can eyeball where the
// threshold sits relative to real readings.
const long GRAB_THRESHOLD_CM = 10;

// Returns distance in cm, or -1 if nothing echoed back within the timeout
// (out of range / no obstacle).
long readDistanceCm() {
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG_PIN, LOW);

  long duration = pulseIn(ULTRASONIC_ECHO_PIN, HIGH, ULTRASONIC_ECHO_TIMEOUT_US);
  if (duration == 0) return -1;
  return duration / 58;  // standard HC-SR04 conversion (speed of sound, round trip)
}

void setup() {
  Serial.begin(115200);
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);
  Serial.println("Setup complete. Starting ultrasonic test...");
}

void loop() {
  unsigned long now = millis();
  if (now - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = now;

    long distanceCm = readDistanceCm();

    // distanceCm == -1 means no echo (out of range), not close.
    if (distanceCm > 0 && distanceCm < GRAB_THRESHOLD_CM) {
      Serial.println("DISTANCE," + String(distanceCm) + "  <-- within grab range");
    } else {
      Serial.println("DISTANCE," + String(distanceCm));
    }
  }
}
