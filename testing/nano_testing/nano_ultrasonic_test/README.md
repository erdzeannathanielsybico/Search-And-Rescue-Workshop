# Nano Ultrasonic Sensor Test

HC-SR04 distance test for the Arduino Nano build. Prints the measured
distance in cm to serial ~10 times a second so you can confirm the sensor,
its wiring, and the trig/echo pins before it feeds the automatic
grab-and-revert logic in the combined firmware
(`../../nano_serial_receiving_test`).

---

## Hardware

- Arduino Nano (ATmega328P, new bootloader)
- HC-SR04 ultrasonic sensor
- USB (Nano power)

---

## Pin Connections

| HC-SR04 | Nano Pin |
|---------|----------|
| Trig    | D2       |
| Echo    | D13      |
| Vcc     | 5V       |
| Gnd     | GND      |

**Note:** D13 is also the Nano's on-board LED pin, so the LED may flicker
with the echo pulses — that's expected, not a fault.

---

## What the Code Does

Every 100 ms it pings the sensor and prints `DISTANCE,<cm>`. The 100 ms
cadence respects the HC-SR04's own limit — pinging faster than ~60 ms apart
lets the previous echo bleed into the next reading.

- A reading of `-1` means nothing echoed back within the timeout (out of
  range / no obstacle), **not** a distance of zero.
- `pulseIn()` uses a tight ~6000 µs timeout (~1 m round trip) so a sensor
  with nothing in range can't stall the loop for long. Anything past ~1 m
  doesn't matter for "close enough to grab" anyway.
- Readings under `GRAB_THRESHOLD_CM` (10 cm) are flagged `<-- within grab
  range` so you can see where the combined firmware's auto grab-and-revert
  threshold sits relative to real readings.

---

## Build & Upload

```
pio run -t upload
pio device monitor
```
