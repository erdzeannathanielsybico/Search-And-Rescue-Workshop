// Hardware: Arduino Nano (ATmega328P, new bootloader) + WS2812 LED strip
//
// RGB LED strip test. Steps the whole strip through red -> green -> blue ->
// white -> off so you can confirm the strip lights, the colour order is
// right (see NEO_GRB note below), and the data line on D11 is good before
// the strip gets used for status indication on the robot.
//
// Hashim's PCB pin map lists D11 as "LED strip data" — a single data line,
// which means an addressable strip (WS2812 / "NeoPixel"), not a plain
// 3-wire analog RGB LED. This test drives it as such.

#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#define LED_DATA_PIN 11  // "LED strip data" per Hashim's PCB pin map
#define NUM_PIXELS   8   // adjust to however many LEDs are on the strip

// Most WS2812 strips are GRB order. If red/green come out swapped, this is
// the first thing to change (e.g. NEO_RGB).
Adafruit_NeoPixel strip(NUM_PIXELS, LED_DATA_PIN, NEO_GRB + NEO_KHZ800);

// Kept low on purpose: at full brightness a strip of these can pull more
// current than USB / the Nano's regulator likes. Raise once it's on the
// proper 5V rail.
const uint8_t BRIGHTNESS = 40;

// Fill the whole strip with one colour and push it out.
void fill(uint8_t r, uint8_t g, uint8_t b) {
  for (int i = 0; i < NUM_PIXELS; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void setup() {
  Serial.begin(115200);
  strip.begin();
  strip.setBrightness(BRIGHTNESS);
  strip.show();  // start with everything off
  Serial.println("Setup complete. Starting RGB LED test...");
}

void loop() {
  Serial.println("RED");
  fill(255, 0, 0);
  delay(1000);

  Serial.println("GREEN");
  fill(0, 255, 0);
  delay(1000);

  Serial.println("BLUE");
  fill(0, 0, 255);
  delay(1000);

  Serial.println("WHITE");
  fill(255, 255, 255);
  delay(1000);

  Serial.println("OFF");
  fill(0, 0, 0);
  delay(1000);
}
