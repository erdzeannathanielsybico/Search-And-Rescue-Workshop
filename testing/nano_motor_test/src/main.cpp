// Hardware: Arduino Nano (ATmega328P, new bootloader)

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

void setup() {
  pinMode(LEFT_DIR_A, OUTPUT);  pinMode(LEFT_DIR_B, OUTPUT);
  pinMode(RIGHT_DIR_A, OUTPUT); pinMode(RIGHT_DIR_B, OUTPUT);
  pinMode(LEFT_SPEED, OUTPUT);  pinMode(RIGHT_SPEED, OUTPUT);

  analogWrite(LEFT_SPEED, 255);
  analogWrite(RIGHT_SPEED, 255);
  stopMotors();
}

void loop() {
  forward();
  delay(2000);

  stopMotors();
  delay(200);

  backward();
  delay(2000);

  stopMotors();
  delay(200);
}
