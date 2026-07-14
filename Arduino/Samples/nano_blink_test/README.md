# Nano Blink Test

The "is this thing on?" test. Blinks the Arduino Nano's on-board LED once a
second and mirrors the state (`ON` / `OFF`) to the serial monitor. Used to
confirm the board, the USB connection, and the PlatformIO upload path all
work before touching any of the other `nano_testing` projects.

---

## Hardware

- Arduino Nano (ATmega328P, new bootloader)
- USB cable (power + upload)

No external wiring — the LED is on-board.

---

## Pin Connections

| Function     | Nano Pin |
|--------------|----------|
| On-board LED | D13 (`LED_BUILTIN`) |

**Note:** D13 doubles as the ultrasonic ECHO pin in Hashim's PCB pin map.
That's harmless here since nothing else is connected, but don't expect the
echo line to behave if you leave this sketch flashed with the sensor board
attached.

---

## What the Code Does

Toggles D13 HIGH for 1 s, LOW for 1 s, forever. Serial monitor at 115200
baud prints `ON` / `OFF` each half-cycle so you can confirm the loop is
running even if you can't see the LED.

---

## Build & Upload

```
pio run -t upload
pio device monitor
```
