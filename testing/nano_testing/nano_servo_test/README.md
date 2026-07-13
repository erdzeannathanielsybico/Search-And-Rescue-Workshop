# Nano Servo Test

Claw servo test for the Arduino Nano build. Toggles the claw between its open
and closed positions every 2 seconds so you can watch it travel and confirm
the endpoints don't bind or stall the servo. This is where the real
open/closed angles for a given claw get dialled in before they're hard-coded
into the combined firmware.

---

## Hardware

- Arduino Nano (ATmega328P, new bootloader)
- Servo (claw), signal on D9
- Servo power: 5V + common GND (from the PCB's servo rail, not the Nano's
  5V pin if the servo draws much current)

---

## Pin Connections

| Function      | Nano Pin |
|---------------|----------|
| Claw servo signal | D9   |

---

## Angles

These are **this claw's** measured endpoints, not the servo's mechanical
0/180. Driving past them risks stalling the servo against the mechanism.

| State  | Angle |
|--------|-------|
| Open   | 10°   |
| Closed | 60°   |

If you're testing a different claw, find its real endpoints here and update
`CLAW_OPEN_ANGLE` / `CLAW_CLOSE_ANGLE` before copying them into
`nano_serial_receiving_test`.

---

## What the Code Does

Opens the claw in `setup()` (so it never powers up clamped shut), then
toggles open ↔ closed every 2 s using a non-blocking `millis()` timer — no
`delay()` — so the same pattern drops straight into the combined firmware
where the claw shares `loop()` with serial and the motors. Serial monitor at
115200 baud prints `CLAW,OPEN` / `CLAW,CLOSE` on each toggle.

---

## PlatformIO Note

Unlike the Arduino IDE, PlatformIO does not bundle the Servo library. It's
declared in `platformio.ini`:

```
lib_deps = arduino-libraries/Servo
```

Without it the build fails with `Servo.h: No such file or directory`.

---

## Build & Upload

```
pio run -t upload
pio device monitor
```
