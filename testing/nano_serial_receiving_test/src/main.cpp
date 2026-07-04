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

Servo claw;

// Not wired up yet, reserved here so the pin map matches Hashim's PCB doc:
// D10 (PWM) - Servo 2 (spare)
// D6  (PWM) - Buzzer      -- shares Timer2 with LEFT_SPEED (D3). If the
//                            buzzer is ever driven with tone(), it can
//                            transiently disrupt left-side motor PWM while
//                            a tone is playing. Avoid tone() while driving,
//                            or drive the buzzer with plain digitalWrite().
// D11       - LED strip data
// D2        - HC-SR04 Trig
// D13       - HC-SR04 Echo
// A4/A5     - I2C SDA/SCL (MPU6050)
// A6/A7     - Battery sense (Cell 1 / full pack, via divider)

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
void setSpeed(int speed) {
  analogWrite(LEFT_SPEED, speed);
  analogWrite(RIGHT_SPEED, speed);
}

void setup() {
  Serial.begin(115200);

  pinMode(LEFT_DIR_A, OUTPUT);  pinMode(LEFT_DIR_B, OUTPUT);
  pinMode(RIGHT_DIR_A, OUTPUT); pinMode(RIGHT_DIR_B, OUTPUT);
  pinMode(LEFT_SPEED, OUTPUT);  pinMode(RIGHT_SPEED, OUTPUT);

  claw.attach(CLAW_SERVO_PIN);
  claw.write(CLAW_OPEN_ANGLE); // NEVER FORGET OR ELSE SERVO WILL BREAK

  setSpeed(255);  // full speed by default, until a SPEED command says otherwise
  stopMotors();
  Serial.println("Setup complete. Starting motor test...");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;

    // Every command is a plain word, except SPEED, which carries a value:
    // "SPEED,180" — split off the part after the comma, if there is one.
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
      int speed = line.substring(commaIndex + 1).toInt();
      setSpeed(speed);
    } else if (keyword == "CLAW") {
      String argument = line.substring(commaIndex + 1);
      if (argument == "OPEN") {
        claw.write(CLAW_OPEN_ANGLE);
      } else if (argument == "CLOSE") {
        claw.write(CLAW_CLOSE_ANGLE);
      }
    } else {
      Serial.println("Unknown command: " + line);
      stopMotors();
    }
  }
}
