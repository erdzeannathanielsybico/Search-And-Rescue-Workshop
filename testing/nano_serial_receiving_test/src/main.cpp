// Hardware: Arduino Nano (ATmega328P, new bootloader)

#include <Arduino.h>
#include <Servo.h>

// --- Pin map from Hashim's PCB design ---
// Each side's two motors are jumpered together on the board (both IN pins
// tied to one Nano pin, both ENA/ENB tied to one PWM pin), so each side
// moves as a single unit: one speed pin + two direction pins per side.
#define LEFT_SPEED   3   // PWM — ENA+ENB of L298N #1 (jumpered)
#define RIGHT_SPEED  5   // PWM — ENA+ENB of L298N #2 (jumpered)
#define LEFT_DIR_A   4   // IN1+IN3 of L298N #1 (jumpered)
#define LEFT_DIR_B   7   // IN2+IN4 of L298N #1 (jumpered)
#define RIGHT_DIR_A  8   // IN1+IN3 of L298N #2 (jumpered)
#define RIGHT_DIR_B  12  // IN2+IN4 of L298N #2 (jumpered)

#define CLAW_SERVO_PIN 9  // Servo 1 (claw)

// Angles found by testing in servo_test — not 0/180, these are this specific
// claw's actual open/closed positions.
#define CLAW_OPEN_ANGLE  10
#define CLAW_CLOSE_ANGLE 60

#define ULTRASONIC_TRIG_PIN 2
#define ULTRASONIC_ECHO_PIN 13

Servo claw;

// Reported back to the RPi over serial whenever it changes — the RPi never
// assumes a mode switch took effect just because it asked, it waits for this.
String currentMode = "MANUAL";

// MODE + DISTANCE are both reported on this cadence, not just on change —
// periodic beats event-only here, so a single dropped/garbled serial line
// self-heals on the next tick instead of leaving the RPi stuck on stale
// data. 100ms also respects the HC-SR04's own limit: pinging it faster than
// ~60ms apart lets the previous echo bleed into the next reading.
const unsigned long REPORT_INTERVAL_MS = 100;
unsigned long lastReportTime = 0;

// pulseIn() blocks until the echo returns or this timeout expires — kept
// tight (~1m round trip) so a sensor with nothing in range can't stall
// command responsiveness for long. Anything past ~1m doesn't matter for
// "close enough to grab" anyway.
const unsigned long ULTRASONIC_ECHO_TIMEOUT_US = 6000;

// Not wired up yet, reserved here so the pin map matches Hashim's PCB doc:
// D10 (PWM) - Servo 2 (spare)
// D6  (PWM) - Buzzer      -- shares Timer2 with LEFT_SPEED (D3). If the
//                            buzzer is ever driven with tone(), it can
//                            transiently disrupt left-side motor PWM while
//                            a tone is playing. Avoid tone() while driving,
//                            or drive the buzzer with plain digitalWrite().
// D11       - LED strip data
// A4/A5     - I2C SDA/SCL (MPU6050)
// A6/A7     - Battery sense (Cell 1 / full pack, via divider)

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

void forward() {
  digitalWrite(LEFT_DIR_A, HIGH);  digitalWrite(LEFT_DIR_B, LOW);
  digitalWrite(RIGHT_DIR_A, HIGH); digitalWrite(RIGHT_DIR_B, LOW);
}

void backward() {
  digitalWrite(LEFT_DIR_A, LOW);  digitalWrite(LEFT_DIR_B, HIGH);
  digitalWrite(RIGHT_DIR_A, LOW); digitalWrite(RIGHT_DIR_B, HIGH);
}

void stopMotors() {
  digitalWrite(LEFT_DIR_A, LOW);  digitalWrite(LEFT_DIR_B, LOW);
  digitalWrite(RIGHT_DIR_A, LOW); digitalWrite(RIGHT_DIR_B, LOW);
}

// Assumes left = Nano's "left" pins above, right = Nano's "right" pins above.
// If the robot turns the wrong way on first test, swap which side reverses.
void turnLeft() {
  digitalWrite(LEFT_DIR_A, LOW);   digitalWrite(LEFT_DIR_B, HIGH);
  digitalWrite(RIGHT_DIR_A, HIGH); digitalWrite(RIGHT_DIR_B, LOW);
}

void turnRight() {
  digitalWrite(LEFT_DIR_A, HIGH); digitalWrite(LEFT_DIR_B, LOW);
  digitalWrite(RIGHT_DIR_A, LOW); digitalWrite(RIGHT_DIR_B, HIGH);
}

// Speed lives entirely on the two speed pins as a PWM duty cycle (0-255),
// separate from the direction pins above — so changing speed never needs
// to know or touch the current direction, and vice versa.
// Left and right are independent on purpose: manual mode always sends equal
// values (a plain speed setting), but automatic tracking will steer while
// moving FORWARD by biasing one side faster than the other, line-follower
// style, instead of pivoting with LEFT/RIGHT.
void setSpeed(int leftSpeed, int rightSpeed) {
  analogWrite(LEFT_SPEED, leftSpeed);
  analogWrite(RIGHT_SPEED, rightSpeed);
}

void setup() {
  Serial.begin(115200);

  pinMode(LEFT_DIR_A, OUTPUT);  pinMode(LEFT_DIR_B, OUTPUT);
  pinMode(RIGHT_DIR_A, OUTPUT); pinMode(RIGHT_DIR_B, OUTPUT);
  pinMode(LEFT_SPEED, OUTPUT);  pinMode(RIGHT_SPEED, OUTPUT);
  pinMode(ULTRASONIC_TRIG_PIN, OUTPUT);
  pinMode(ULTRASONIC_ECHO_PIN, INPUT);

  claw.attach(CLAW_SERVO_PIN);
  claw.write(CLAW_OPEN_ANGLE); // NEVER FORGET OR ELSE SERVO WILL BREAK

  setSpeed(255, 255);  // full speed by default, until a SPEED command says otherwise
  stopMotors();
  Serial.println("Setup complete. Starting motor test...");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;

    // Every command is a plain word, except SPEED (two values, "SPEED,180,220")
    // and CLAW (one value, "CLAW,OPEN") — split off the part after the comma.
    int commaIndex = line.indexOf(',');
    String keyword = (commaIndex == -1) ? line : line.substring(0, commaIndex);

    if (keyword == "FORWARD") {
      forward();
    } else if (keyword == "BACKWARD") {
      backward();
    } else if (keyword == "LEFT") {
      turnLeft();
    } else if (keyword == "RIGHT") {
      turnRight();
    } else if (keyword == "STOP") {
      stopMotors();
    } else if (keyword == "SPEED") {
      // "SPEED,<left>,<right>" — split the remainder on its own comma.
      String args = line.substring(commaIndex + 1);
      int secondComma = args.indexOf(',');
      int leftSpeed = args.substring(0, secondComma).toInt();
      int rightSpeed = args.substring(secondComma + 1).toInt();
      setSpeed(leftSpeed, rightSpeed);
    } else if (keyword == "CLAW") {
      String argument = line.substring(commaIndex + 1);
      if (argument == "OPEN") {
        claw.write(CLAW_OPEN_ANGLE);
      } else if (argument == "CLOSE") {
        claw.write(CLAW_CLOSE_ANGLE);
      }
    } else if (keyword == "MODE") {
      // Just a request — accept it and echo back so the RPi knows it
      // actually took effect. The ultrasonic-triggered auto-revert (once
      // the sensor's wired in) will echo this same way, unprompted.
      String argument = line.substring(commaIndex + 1);
      if (argument == "AUTO" || argument == "MANUAL") {
        currentMode = argument;
        if (currentMode == "MANUAL") {
          // Halt immediately on entering manual, regardless of what was
          // driving before — this is the emergency-override path, it can't
          // wait on a STOP command surviving a round trip back through ROS.
          stopMotors();
        }
        Serial.println("MODE," + currentMode);
      }
    } else {
      Serial.println("Unknown command: " + line);
      stopMotors();
    }
  }

  unsigned long now = millis();
  if (now - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = now;
    long distanceCm = readDistanceCm();

    // Final authority: grab and revert the instant the target's close
    // enough, regardless of whatever commands are still arriving from the
    // RPi — this is the safety backstop the automatic-tracking design
    // depends on. distanceCm == -1 means no echo (out of range), not close.
    if (currentMode == "AUTO" && distanceCm > 0 && distanceCm < 10) {
      claw.write(CLAW_CLOSE_ANGLE);
      stopMotors();
      currentMode = "MANUAL";
    }

    Serial.println("MODE," + currentMode);
    Serial.println("DISTANCE," + String(distanceCm));
  }
}
