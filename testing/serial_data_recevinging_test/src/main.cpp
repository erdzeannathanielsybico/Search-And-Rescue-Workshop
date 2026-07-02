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

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT); pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); pinMode(IN4, OUTPUT);
  pinMode(IN5, OUTPUT); pinMode(IN6, OUTPUT);
  pinMode(IN7, OUTPUT); pinMode(IN8, OUTPUT);

  pinMode(ENA1, OUTPUT); pinMode(ENB1, OUTPUT);
  pinMode(ENA2, OUTPUT); pinMode(ENB2, OUTPUT);

  // Full speed on all enable pins
  digitalWrite(ENA1, HIGH);
  digitalWrite(ENB1, HIGH);
  digitalWrite(ENA2, HIGH);
  digitalWrite(ENB2, HIGH);

  stopMotors();
  Serial.println("Setup complete. Starting motor test...");
}

void loop() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) return;

    // Commands look like "<KEYWORD>,<argument>", e.g. "MOTOR,0"
    int commaIndex = line.indexOf(',');
    String keyword = (commaIndex == -1) ? line : line.substring(0, commaIndex);
    String argument = (commaIndex == -1) ? "" : line.substring(commaIndex + 1);

    if (keyword == "MOTOR") {
      int direction = argument.toInt();
      if (direction == 0) {
        Serial.println("FORWARD");
        forward();
      } else if (direction == 1) {
        Serial.println("BACKWARD");
        backward();
      } else {
        Serial.println("STOP");
        stopMotors();
      }
    } else {
      Serial.println("Unknown command: " + line);
      stopMotors();
    }
  }
}
