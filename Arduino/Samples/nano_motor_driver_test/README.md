# Nano Motor Driver Test

Self-driving L298N test for the Arduino Nano build. Cycles through every
movement (forward, backward, left, right) with stops in between so you can
confirm motor wiring and direction on the bench — no serial commands
required. This is the Nano equivalent of the ESP32 `L298N_testing` project,
rewired to Hashim's PCB pin map.

Once this passes, the serial-controlled version lives in
`../../nano_serial_receiving_test`.

---

## Hardware

- Arduino Nano (ATmega328P, new bootloader)
- 2x L298N motor driver modules
- 4x DC motors (2 per side, jumpered together on the PCB)
- Separate motor power supply (into the L298N 12V terminal)
- USB (Nano logic power)

---

## Pin Connections

Each side's two motors are jumpered together on Hashim's PCB, so each side is
driven as a single unit: one PWM speed pin + two direction pins.

| Function      | Nano Pin | L298N                     |
|---------------|----------|---------------------------|
| `LEFT_SPEED`  | D3 (PWM) | ENA + ENB of #1 (jumpered)|
| `LEFT_DIR_A`  | D4       | IN1 + IN3 of #1 (jumpered)|
| `LEFT_DIR_B`  | D7       | IN2 + IN4 of #1 (jumpered)|
| `RIGHT_SPEED` | D5 (PWM) | ENA + ENB of #2 (jumpered)|
| `RIGHT_DIR_A` | D8       | IN1 + IN3 of #2 (jumpered)|
| `RIGHT_DIR_B` | D12      | IN2 + IN4 of #2 (jumpered)|

**Wiring notes:**
- Common GND between Nano, both L298N boards, and the motor supply.
- Motor power into the L298N 12V screw terminal, not off the Nano.
- Do NOT power the Nano from the L298N 5V output.

---

## What the Code Does

Loops: forward 2 s → stop → backward 2 s → stop → left 1 s → stop →
right 1 s → stop. Serial monitor at 115200 baud prints the current action
each step. Speed is fixed at full (255/255) via `setSpeed()`.

If the robot turns the wrong way, swap which side reverses in `turnLeft()` /
`turnRight()`.

---

## Build & Upload

```
pio run -t upload
pio device monitor
```
