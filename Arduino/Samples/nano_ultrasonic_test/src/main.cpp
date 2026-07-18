#include <Arduino.h>

#define ECHO_PIN 13
#define TRIG_PIN 2

unsigned long time_now = 0;
long last_report_time = 0;
long interval = 100;

long get_distance_in_CM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH);
  
  long distance = duration * 0.034/2;

  return distance;
}

void setup() {
  Serial.begin(115200);

  pinMode(ECHO_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
}

void loop() {
  
  unsigned long time_now = millis();
  if ((time_now - last_report_time) >= interval) {
    last_report_time = time_now;
      Serial.println(get_distance_in_CM());
  }
}