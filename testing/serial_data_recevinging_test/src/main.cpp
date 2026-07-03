#include <Arduino.h>

// --- Driver 1 (proven pins from previous project) ---
#define ENA1 14
#define IN1  27
#define IN2  26
#define IN3  25
#define IN4  33
#define ENB1 32

// --- Driver 2 ---
#define ENA2 13
#define IN5  16
#define IN6  17
#define IN7  18
#define IN8  19
#define ENB2 21

void forward() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  digitalWrite(IN5, HIGH); digitalWrite(IN6, LOW);
  digitalWrite(IN7, HIGH); digitalWrite(IN8, LOW);
}

void backward() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW); digitalWrite(IN4, HIGH);
  digitalWrite(IN5, LOW); digitalWrite(IN6, HIGH);
  digitalWrite(IN7, LOW); digitalWrite(IN8, HIGH);
}

void stopMotors() {
  digitalWrite(IN1, LOW); digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW); digitalWrite(IN4, LOW);
  digitalWrite(IN5, LOW); digitalWrite(IN6, LOW);
  digitalWrite(IN7, LOW); digitalWrite(IN8, LOW);
}

// Assumes Driver 1 (IN1-IN4) = left side, Driver 2 (IN5-IN8) = right side.
// If the robot turns the wrong way on first test, swap which side reverses.
void turnLeft() {
  digitalWrite(IN1, LOW);  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);  digitalWrite(IN4, HIGH);
  digitalWrite(IN5, HIGH); digitalWrite(IN6, LOW);
  digitalWrite(IN7, HIGH); digitalWrite(IN8, LOW);
}

void turnRight() {
  digitalWrite(IN1, HIGH); digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH); digitalWrite(IN4, LOW);
  digitalWrite(IN5, LOW);  digitalWrite(IN6, HIGH);
  digitalWrite(IN7, LOW);  digitalWrite(IN8, HIGH);
}

// Speed lives entirely on the ENA/ENB pins as a PWM duty cycle (0-255),
// separate from the IN pins that pick direction above — so changing speed
// never needs to know or touch the current direction, and vice versa.
void setSpeed(int speed) {
  analogWrite(ENA1, speed);
  analogWrite(ENB1, speed);
  analogWrite(ENA2, speed);
  analogWrite(ENB2, speed);
}

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(IN5, OUTPUT); pinMode(IN6, OUTPUT);
  pinMode(IN7, OUTPUT); pinMode(IN8, OUTPUT);

  pinMode(ENA1, OUTPUT); pinMode(ENB1, OUTPUT);
  pinMode(ENA2, OUTPUT); pinMode(ENB2, OUTPUT);

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
    } else {
      Serial.println("Unknown command: " + line);
      stopMotors();
    }
  }
}
