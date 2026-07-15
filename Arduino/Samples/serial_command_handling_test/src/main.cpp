#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#define LED_STRIP_PIN 11
#define LED_PIXELS 8

Adafruit_NeoPixel strip(LED_PIXELS, LED_STRIP_PIN, NEO_GRB + NEO_KHZ800);

const uint8_t BRIGHTNESS = 40;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(115200);

  strip.begin();
  strip.setBrightness(BRIGHTNESS);
  strip.show();


}

void loop() {
  // digitalWrite(LED_BUILTIN, HIGH);
  // Serial.println("HIGH");
  // delay(200);
  // digitalWrite(LED_BUILTIN, LOW);
  // Serial.println("LOW");
  // delay(200);

  strip.setPixelColor(1, strip.Color(255, 255, 255));
  strip.show();


}
