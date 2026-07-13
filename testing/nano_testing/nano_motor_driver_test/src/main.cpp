// Hardware: Arduino Nano (ATmega328P, new bootloader) + 2x L298N
//
// Self-driving motor test — no serial commands needed. Cycles
// forward -> stop -> backward -> stop -> left -> stop -> right -> stop so
// you can verify motor wiring and direction on the bench before wiring the
// Nano into the RPi serial link (see nano_serial_receiving_test for that).

#include <Arduino.h>

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
void setSpeed(int leftSpeed, int rightSpeed) {
  analogWrite(LEFT_SPEED, leftSpeed);
  analogWrite(RIGHT_SPEED, rightSpeed);
}

void setup() {
  Serial.begin(115200);

  pinMode(LEFT_DIR_A, OUTPUT);  pinMode(LEFT_DIR_B, OUTPUT);
  pinMode(RIGHT_DIR_A, OUTPUT); pinMode(RIGHT_DIR_B, OUTPUT);
  pinMode(LEFT_SPEED, OUTPUT);  pinMode(RIGHT_SPEED, OUTPUT);

  setSpeed(255, 255);  // full speed for the bench test
  stopMotors();
  Serial.println("Setup complete. Starting motor test...");
}

void loop() {
  Serial.println("FORWARD");
  forward();
  delay(2000);

  Serial.println("STOP");
  stopMotors();
  delay(500);

  Serial.println("BACKWARD");
  backward();
  delay(2000);

  Serial.println("STOP");
  stopMotors();
  delay(500);

  Serial.println("LEFT");
  turnLeft();
  delay(1000);

  Serial.println("STOP");
  stopMotors();
  delay(500);

  Serial.println("RIGHT");
  turnRight();
  delay(1000);

  Serial.println("STOP");
  stopMotors();
  delay(500);
}
