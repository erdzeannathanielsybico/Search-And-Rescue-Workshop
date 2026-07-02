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
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "forward") {
      Serial.println("FORWARD");
      forward();
    } else if (cmd == "backward") {
      Serial.println("BACKWARD");
      backward();
    } else if (cmd.length() > 0) {
      Serial.println("STOP");
      stopMotors();
    }
  }
}
