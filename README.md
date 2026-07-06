# Search-And-Rescue-Workshop
Content for Hashim Search and Rescue Workshop inspired from STEM Competition Robots

Project Context as of 25 June 2026
Title: Save and Rescue Robots (decided by Fablab even though they were not agreeing before)

The adjusted 8-day plan (~90–120 productive min/day):

> **Pre-workshop instructor prep — not part of any student day.** Each team's laptop needs ROS 2, WSL2, and cross-machine networking (mirrored networking mode, matching `ROS_DOMAIN_ID`, the two Windows Firewall rules) working *before* Day 3 begins — see `ros2_journey.md` Journey 2. This has several non-obvious failure points (a symlink/Developer Mode gotcha, a stale-daemon issue after network changes, firewall rules that differ per team's domain ID) that took real troubleshooting even one-on-one — students should never be debugging this live. Set up and verify every team's laptop in advance, with a fallback plan (e.g. running the controller directly on the RPi via RDP) for any team whose networking can't be fixed in time. Also worth doing before Day 2: test the full firmware (drive + speed + claw) on an actual **Arduino Nano**, not just the ESP32 it's been prototyped on — the Nano has far fewer PWM-capable pins, and its `Servo` library claims a timer that can conflict with motor PWM once the claw is added.

Day 1 — Brief, Teams & Build. Ice breakers and team grouping, then an overview of what the next 8 days look like. Straight into assembling the kit chassis: motors, wheels, mount the boards, one guided solder joint as a real taste. Win: a fully wired-up robot that powers on.

Day 2 — Arduino: Make It Move. Introduce VS Code and PlatformIO, plus enough Linux/project-structure basics to keep the codebase clean. Progression from hello world → blink → the L298N motor driver → the claw servo → any other actuators/sensors on the robot, each tested individually as they're wired in. Win: every actuator and sensor on the robot has been individually tested and responds to code they wrote.

Day 3 — ROS Foundations. No Bluetooth phone app or USB gamepad — control is laptop-only for the rest of the workshop, so this day is entirely about building a real mental model of ROS before depending on it: what ROS is and why it exists, the publish/subscribe model, Linux command basics. The concrete deliverable is writing their own working publisher and subscriber pair, so the structure isn't just theory. Win: everyone has a working mental model of ROS and has written and run their own pub/sub pair.

Day 4 — Serial: From Topic to Actuator. Turn Day 3's pub/sub knowledge into action — build the serial bridge node so messages published from the laptop reach the Arduino Nano and actually move something. Win: every actuator on the robot can be triggered from the laptop over ROS.

Day 5 — Computer Vision They Build. Working from a provided OpenCV scaffold, they implement/tune HSV color detection themselves — find a target color in the camera frame and report where it is (left / right / center). Win: their code makes the robot see the target color and know where it is.

Day 6 — Automation: Tracking. Combine vision and actuators — can start at the tail end of Day 5 if time allows. Build simple closed-loop automation: the robot turns to keep the tracked color centered, rather than reacting to single keypresses. Win: the robot autonomously tracks and centers on the target.

Day 7 — Buffer / Customization. Open day for experimentation and extra features — ultrasonic sensors, an LED strip that reacts to the detected color, whatever teams want to add.

Day 8 — Competition & Showcase. Drive around the FabLab rescuing targets, using a mix of FPV (manual) and automatic (tracking) control, then judged awards, certificates, and a showcase where each team explains what they built and coded. Win: they compete with a robot whose brain and code are genuinely theirs.

Story: we need to think of story for the camp (final scenario)- Mars Exploration (we need to further detail it)

    (robot design should somehow look like rover)
    Hashem: test ros, source rp5 (I need to prepare full list of components), Find assistant within one week time.

    Components for now:

    Rassberry Pi 5-4gb
    Rasspberry Pi charger
    SD card 64GB A2 rating only
    Logitech C310 USB camera
    Arduino Nano
    4 DC motors (need to figure out best available ones) (specs: 6V - 130 RPM)

    Option 1 available locally, expensive
    Option 2 available locally, expensive
    Option 3 comes with nice off road wheel, bracket, coupler and encoder (we will not use encoder)- from China, will order anyway and use the locally available options for demo robots- Motors Ordered

    Metal Servo (large)
    Line following Module (besomi)
    RGB LED Strip (I have enough stock)
    PCB (Hashem to design and produce)
    Bluetooth Module
    Think of extra components if needed
    Battery Ordered

    Nathaniel: extra: do skelton design (4 wheels)- think of battle scenario
    First Robot Demo Deadline: 5th of July

Tasks:

---

## Plan — 2026-07-06: finalize automatic tracking + claw grab

**First task today:** `laptop_controller` and the Nano need to support directional commands with a speed value (e.g. `LEFT,180` / `RIGHT,90`), not just plain `LEFT`/`RIGHT`. This is groundwork the automatic-tracking node depends on later — it needs to turn *proportionally* (speed up the turn the further off-center the target is), not just snap to a fixed on/off turn.

**Full architecture being built out today/next:**

Topics:
- `ManualDirection` — laptop_controller's raw keyboard output (rename of today's `Direction`)
- `AutomaticDirection` — output of the new color-tracking node: converts the target's position (from `color_detection.py`'s saved HSV ranges) into `LEFT`/`RIGHT`/`FORWARD`-with-speed commands to keep it centered
- `ControlMode` — current mode (`MANUAL`/`AUTO`), broadcast for the GUI and the command switcher — sourced from what the Nano actually reports, never assumed from the last command sent
- `Direction` — the final, merged command stream that reaches `direction_to_serial`, unchanged from how it works today

Nodes:
- **Command switcher** (new) — subscribes to `ManualDirection`, `AutomaticDirection`, `ControlMode`; forwards whichever source is currently active onto `Direction`. Its whole job is that one if/else — no vision, no serial.
- **Color-tracking node** (new) — reads the target's position (from the camera side) and publishes `AutomaticDirection` commands to keep it centered.
- **`direction_to_serial`** (existing, gets extended) — write side stays exactly as-is (relay `Direction` to serial verbatim); new read side polls incoming serial lines from the Nano (distance + mode reports) and republishes them as ROS topics (`ControlMode`, a distance topic for the HUD). It doesn't decide anything — just reports what the Nano says, same "don't interpret, just pass through" philosophy as the write side.
- **`camera_feed_publisher`** (existing, gets extended) — subscribes to a new `CameraViewMode` topic (raw/mask/box), published by `laptop_controller` on a keypress, and renders the feed accordingly before publishing `CameraFeed`.
- **Nano firmware** — owns the actual auto/manual decision: runs the ultrasonic check locally, and once the target's close enough, closes the claw and reverts to manual — regardless of what commands are still arriving — then reports the new mode + distance back up over serial. This is deliberately the final authority/backstop, so a stray stale automatic command right at the mode transition can't cause a bad grab.

**Why mode-toggle bypasses the command switcher:** the key that triggers auto/manual publishes straight onto `Direction` as a plain control string, the same way `SPEED,180` / `CLAW,OPEN` do today — `direction_to_serial` doesn't need to understand it, it just relays it to the Nano like anything else.

---

## Known Issues & Fixes

### Raspberry Pi — WiFi connects but no internet (missing default route)
**Symptom:** wlan0 has an IP address but `ip route show` is empty and pings to external IPs fail with "Network is unreachable." Git, SSH, and anything network-dependent will fail.

**Cause:** DHCP assigned an IP but didn't install the default gateway route — a NetworkManager hiccup on reconnect.

**Fix:** Turn the wifi connection off and on again to force a clean DHCP handshake:
```bash
sudo nmcli connection down "Addi" && sleep 3 && sudo nmcli connection up "Addi"
```
Replace `"Addi"` with your wifi network name if it changes. Verify with `ip route show` — you should see a `default via 192.168.1.x dev wlan0` line.

### Serial port — PermissionError: [Errno 13] Permission denied opening /dev/ttyUSB0 (or /dev/serial/by-id/...)
**Symptom:** A ROS2 node (or any script) calling `serial.Serial(port, baud)` crashes with `PermissionError: [Errno 13] Permission denied` on the port path.

**Cause:** Raw serial port access is restricted to users in the `dialout` group. A fresh user account isn't in it by default.

**Fix:**
```bash
groups                              # check if dialout is already listed
sudo usermod -aG dialout $USER
```
Then **log out and log back in** (or reboot) — a new terminal window is *not* enough, since group membership is only re-read when a new login session starts. Verify with `groups` again afterward.

### Identifying which /dev/tty* is the microcontroller
**Problem:** `ls /dev/tty*` lists hundreds of unrelated virtual/legacy tty devices — not useful for finding a specific USB device, and the `/dev/ttyUSB0`-style number isn't stable across reboots/replugs anyway.

**Fix:** Use the `by-id` symlink instead, which is tied to the device's hardware ID and stays consistent:
```bash
ls -l /dev/serial/by-id/
```
Output looks like:
```
usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 -> ../../ttyUSB0
```
Use the full `/dev/serial/by-id/...` path (not the `ttyUSB0` it resolves to) wherever a serial port path is needed in code — it survives re-enumeration even if the device later shows up as `ttyUSB1`.

### Accidentally running colcon build from the wrong directory
**Symptom:** Stray `build/`, `install/`, `log/` folders appear at the repo root (or another wrong location), and/or `ros2 run` picks up a node from an unexpected `install/` path.

**Cause:** `colcon build` always builds into whatever directory you're `cd`'d into when you run it — it doesn't know or care where your actual ROS2 workspace is. Running it from the repo root, or from inside a package's `src/` folder, silently creates a second, wrong workspace instead of erroring out.

**Fix:** Always `cd` into the workspace root (`testing/ros2_test_workspace/`) before running `colcon build`, `source install/setup.bash`, or `ros2 run`. If stray artifacts appear elsewhere, they're safe to delete — they're just regenerated build output, not source code.

### Camera feed over ROS2 — wobbly video despite low latency (wrong pixel format)
**Symptom:** Video looked smooth in other apps on the same machine (e.g. Windows' built-in camera app) even when shaking/moving the camera fast, but was wobbly/juddery once streamed over the ROS2 `CameraFeed` topic — the wobble persisted regardless of `CAP_PROP_BUFFERSIZE` (tried 1 through 50, barely any difference), so it wasn't a buffering/latency problem.

**Cause:** `cv2.VideoCapture`'s V4L2 backend was negotiating raw **YUYV** instead of the camera's hardware **MJPG** encoder. Uncompressed YUYV at 1280x720@30fps needs ~66MB/s, more than the bus reliably sustains, so frames arrive at irregular intervals instead of cleanly dropping to a lower fps — that irregular timing is what reads as wobble. Confirmed with:
```bash
v4l2-ctl --list-formats-ext -d /dev/video0
```
which showed YUYV capped at a few fps for larger sizes, while MJPG held a steady 30fps at 1280x720.

**Fix:** Force the FourCC to MJPG *before* setting width/height (V4L2 only applies the format change at that point), and pin the backend explicitly so property order is respected:
```python
self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
```
See `camera_feed_test/camera_feed_publisher.py`.

---

## Confirmed Hardware & Software

### Raspberry Pi 5
- **OS:** Ubuntu 24.04.4 LTS (Noble Numbat)
- **Architecture:** aarch64 (ARM64)
- **ROS:** ROS 2 Jazzy
- **Note:** VS Code snap install does not work on ARM64 — use the `.deb` package from the official VS Code website instead

### Microcontroller
- **Currently testing on an ESP32** (see `testing/serial_data_recevinging_test/src/main.cpp`) — an Arduino Nano hasn't been acquired yet; the ESP32 is standing in for it during development.
- **Planned final microcontroller: Arduino Nano (ATmega328P)** — handles low-level motor control via serial commands from RPi
- Neither can run micro-ROS (insufficient memory) — communicates with ROS via a serial bridge node on the RPi (`direction_to_serial`)

### Motor Driver
- 2x L298N motor driver modules
- Motor power: 9V supply into the 12V terminal (5V breadboard PSU insufficient for 4 motors)
- L298N 5V jumper left ON

### Motors
- 4x DC motors (6V, 130 RPM)

---

## ROS2 Workspace — Building & Running

Workspace root: `testing/ros2_test_workspace/`. Packages live under `src/` inside it (e.g. `src/py_pubsub_test/`, `src/serial_bridge_test/`). `colcon build` / `source install/setup.bash` / `ros2 run` are always run from the workspace root — never from inside `src/`.

**Build** — always `cd` into the workspace root first. Running `colcon build` from anywhere else (e.g. the repo root, or inside `src/`) scatters duplicate `build/`, `install/`, `log/` directories in the wrong place:
```bash
cd testing/ros2_test_workspace
colcon build
```

**Run** — needs `source install/setup.bash` in *every new terminal*, run from the workspace root. Sourcing without `cd`-ing there first will fail to find the package:
```bash
# Terminal 1
cd testing/ros2_test_workspace
source install/setup.bash
ros2 run py_pubsub_test talker

# Terminal 2
cd testing/ros2_test_workspace
source install/setup.bash
ros2 run py_pubsub_test listener
```

### serial_bridge_test (testing/ros2_test_workspace/src/serial_bridge_test)
RPi ↔ ESP32/Nano serial bridge. Runs **on the RPi**. `direction_to_serial` subscribes to the `Direction` topic and forwards whatever string it receives, unchanged, over serial to the microcontroller (it's protocol-agnostic — doesn't parse or care what the message content is, just relays it).

`direction_publisher` (also in this package) publishes mock alternating `forward`/`backward` messages — it was the original stand-in used to test the pub/sub wiring before a real controller existed. **It's now superseded by `laptop_controller_test`'s `laptop_controller` node** (see below) and its message content (`forward`/`backward`, lowercase) no longer matches the microcontroller's current protocol — don't use it to test against real hardware anymore, it's kept only as a minimal pub/sub example.

**Serial protocol (main.cpp on the microcontroller):** plain-word commands, one per line — `FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `STOP`. No numeric codes/magic numbers, deliberately, for readability. Only one action happens at a time (tank-style: can't turn and drive forward simultaneously) — this falls out naturally since the controller only ever tracks one active command. Turning pivots in place (one side's motors forward, the other side's backward); see the comment above `turnLeft()`/`turnRight()` in `main.cpp` for the left/right pin assumption, which may need swapping once tested on the real chassis.

**Identifying the microcontroller's serial port** — the `/dev/ttyUSBx` number isn't stable across reboots/replugs, so use the `by-id` symlink instead, which is tied to the device's hardware ID:
```bash
ls -l /dev/serial/by-id/
```
This prints something like:
```
usb-Silicon_Labs_CP2102_USB_to_UART_Bridge_Controller_0001-if00-port0 -> ../../ttyUSB0
```
Use the full `/dev/serial/by-id/...` path (not the `../../ttyUSB0` it resolves to) as the serial port passed to `serial.Serial(...)` — it stays correct even if the device gets re-enumerated as `ttyUSB1` etc.

If you get a permissions error opening the port, check you're in the `dialout` group:
```bash
groups
sudo usermod -aG dialout $USER   # if not listed — requires logging out/in to take effect
```

### laptop_controller_test (testing/ros2_test_workspace/src/laptop_controller_test)

> ## ⚠️ NOT PART OF THE STUDENT CURRICULUM
> This package is instructor/prototype tooling only — students will **not** write or see this code, and it is **not** the Day 3 "manual control" step. The workshop plan for student-facing manual control is a **phone app or USB gamepad**, chosen specifically because a 2-day ROS introduction doesn't leave time to also teach pygame, keyboard event handling, or GUI programming. This package exists purely so the RPi ↔ laptop ↔ hardware chain could be tested end-to-end during setup, and is documented here for transparency and future reference — not as teaching material.

Runs **on the laptop** (via WSL2 — see `ros2_journey.md` Journey 2), not the RPi. Opens a small `pygame` window and reads arrow-key input with real `KEYDOWN`/`KEYUP` events (press = fires once, release = fires once — no flicker, unlike an earlier terminal-based attempt that approximated "held down" with a timeout). Publishes `FORWARD` / `BACKWARD` / `LEFT` / `RIGHT` / `STOP` as plain-word `String` messages on the real `Direction` topic — the same topic `serial_bridge_test`'s `direction_to_serial` subscribes to.

Requires `pygame`, installed via apt — **not** `pip install pygame`, which fails on Ubuntu 24.04 due to PEP 668 (`externally-managed-environment`) protecting the system Python:
```bash
sudo apt install python3-pygame
```

The pygame window displaying at all from inside WSL2 relies on **WSLg** (GUI app support built into WSL2 on Windows 11) — no extra X-server setup needed.

```bash
cd testing/ros2_test_workspace
colcon build
source install/setup.bash
ros2 run laptop_controller_test laptop_controller
```
Click the window first so it has keyboard focus, then use the arrow keys.

**This requires cross-machine ROS 2 networking to be set up first** (laptop and RPi are two separate machines on the LAN, not two nodes on one machine) — see `ros2_journey.md` Journey 2, step 8, for WSL2 mirrored networking, matching `ROS_DOMAIN_ID`, and the two Windows Firewall rules (ICMP + DDS UDP port range) that were needed.

### camera_feed_test (testing/ros2_test_workspace/src/camera_feed_test)

Runs **on the RPi**. `camera_feed_publisher` opens the Logitech C310 (`cv2.VideoCapture`, V4L2 backend, hardware MJPG — see the wobble fix above) at 1280x720 and publishes each frame as a JPEG-encoded `sensor_msgs/CompressedImage` on the `CameraFeed` topic, using `qos_profile_sensor_data` — same reasoning as `Direction`: on a network hiccup, video should drop stale frames rather than queue them up and add lag.

`laptop_controller_test`'s `laptop_controller` node subscribes to `CameraFeed` and decodes/displays each frame in the same pygame window used for keyboard control, so one window shows the live feed while driving.

```bash
# On the RPi
cd testing/ros2_test_workspace
source install/setup.bash
ros2 run camera_feed_test camera_feed_publisher
```

### color_detection.py (testing/ros2_test_workspace/src/camera_feed_test/camera_feed_test/color_detection.py)

Standalone HSV color-tuning tool — **not a ROS2 node**, run directly with `python3 color_detection.py` (no `colcon build`/`ros2 run` needed). Its only job is finding and saving the HSV threshold range that isolates a target color (e.g. a rescue target) in the camera feed, robust to lighting changes. It doesn't publish anything itself — its only lasting output is `color_ranges.json`, written next to the script, which other code reads via `range_for_color()` instead of re-tuning from scratch (planned consumers: `camera_feed_publisher` for HUD overlays, and a future color-tracking node for autonomous driving).

Uses HSV, not RGB — Hue/Saturation/Value separates a color's identity from lighting brightness, so a threshold tuned once holds up much better than an RGB threshold would as light changes. Red is the one color that needs care: it sits at both ends of OpenCV's Hue wheel (0-179), so a single min/max range only catches one side of it. Green and blue don't have this problem and are generally the easiest, most reliable colors to detect indoors (uncommon in backgrounds/skin tones, no hue wraparound) — worth steering teams toward those if red isn't required by the theme.

**How to use:**
1. Run the script. Three windows open: **Camera** (live feed with a detection box + label), **Mask** (black/white threshold preview), **HSV Tuning** (six sliders).
2. Press **1 / 2 / 3** to load a starting point for RED / GREEN / BLUE onto the sliders — the last saved range for that color if one exists, otherwise a rough default.
3. Adjust the sliders while watching the **Mask** window: the goal is white only where the target object is, black everywhere else. Narrow `H Min`/`H Max` first, then raise `S Min`/`V Min` to kill background noise (shadows, skin tone, walls).
4. Press **S** to save the current sliders under the active color's name into `color_ranges.json`.
5. Press **Q** to quit.

Saved ranges reflect whatever lighting was present at save time — if venue lighting differs on the actual day, budget a few minutes to re-tune and re-save rather than trusting old saved values.

**✅ Confirmed working end-to-end:** all three nodes running simultaneously across both machines — laptop keypress (pygame) → `Direction` topic over the cross-machine ROS 2 network → RPi's `direction_to_serial` → serial → ESP32 (`main.cpp`) → motors actually drive, **at the same time as** the RPi's `camera_feed_publisher` → `CameraFeed` topic → the laptop's pygame window, showing live 720p video while driving. Full chain, both machines, tested and working.

