# L298N Motor Driver Test

Basic forward/backward test for 2x L298N motor drivers with an ESP32, used to verify motors and wiring before integrating into the main robot.

---

## Hardware

- ESP32 Dev Module
- 2x L298N motor driver modules
- 4x DC motors
- 9V power supply (motor power)
- USB (ESP32 logic power)

---

## Pin Connections

### Driver 1
| L298N | ESP32 GPIO |
|-------|-----------|
| ENA   | 14        |
| IN1   | 27        |
| IN2   | 26        |
| IN3   | 25        |
| IN4   | 33        |
| ENB   | 32        |

### Driver 2
| L298N | ESP32 GPIO |
|-------|-----------|
| ENA   | 13        |
| IN1   | 16        |
| IN2   | 17        |
| IN3   | 18        |
| IN4   | 19        |
| ENB   | 21        |

**Wiring notes:**
- L298N 5V jumper left ON — onboard regulator active
- Motor power (9V) into the 12V screw terminal
- Common GND between ESP32, both L298N boards, and power supply
- Do NOT connect ESP32 to L298N's 5V output pin

---

## What the Code Does

Loops: forward 2 seconds → stop → backward 2 seconds → stop. Serial monitor at 115200 baud prints FORWARD / STOP / BACKWARD each cycle as a sanity check.

---

## Problems Encountered

**Motors not moving despite serial prints working**
- Cause 1: Two of the L298N boards were faulty out of the box. Swapping them fixed it.
- Cause 2: `analogWrite()` was used for ENA/ENB but ESP32 Arduino core v3.x removed it. Pins stayed LOW, disabling the drivers. Fixed by switching to `digitalWrite(HIGH)` since full speed is all that's needed for this test.

**5V breadboard PSU couldn't run 4 motors**
- Symptoms: motors twitched or didn't spin under load
- Fix: powered motors directly from 9V supply into the L298N's motor terminal. The breadboard PSU simply can't supply enough current for 4 motors simultaneously.
