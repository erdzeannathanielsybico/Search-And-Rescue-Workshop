# Nano RGB LED Test

Addressable RGB LED strip test for the Arduino Nano build. Steps the whole
strip through red → green → blue → white → off so you can confirm the strip
lights up, the colour order is correct, and the data line on D11 is good
before the strip is used for status indication on the robot.

---

## Hardware

- Arduino Nano (ATmega328P, new bootloader)
- WS2812 ("NeoPixel") addressable RGB LED strip
- 5V supply for the strip + common GND with the Nano

Hashim's PCB pin map lists **D11 as "LED strip data"** — a single data line,
which means an addressable strip (WS2812), not a plain 3-wire analog RGB
LED. This test drives it accordingly.

---

## Pin Connections

| Function       | Nano Pin |
|----------------|----------|
| LED strip data | D11      |

**Wiring notes:**
- Strip 5V from the 5V rail, not the Nano's regulator, if it's more than a
  few LEDs — WS2812s are current-hungry at full brightness.
- Common GND between the strip's supply and the Nano.

---

## Configuration

Two things to check at the top of `main.cpp`:

- `NUM_PIXELS` — set to however many LEDs are actually on your strip (default 8).
- Colour order — the strip is initialised as `NEO_GRB`, which is most common.
  If red and green come out swapped, change it to `NEO_RGB`.

Brightness is deliberately capped at 40/255 so it's safe to run off USB
during the bench test. Raise it once the strip is on its proper 5V rail.

---

## What the Code Does

Fills the entire strip with one colour at a time — red, green, blue, white —
for 1 s each, then blanks it, and repeats. Serial monitor at 115200 baud
prints the current colour each step.

---

## PlatformIO Note

The Adafruit NeoPixel library is declared in `platformio.ini`:

```
lib_deps = adafruit/Adafruit NeoPixel
```

---

## Build & Upload

```
pio run -t upload
pio device monitor
```
