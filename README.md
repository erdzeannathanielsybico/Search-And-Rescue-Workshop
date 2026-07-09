# Search-And-Rescue-Workshop
Content for Hashim Search and Rescue Workshop inspired from STEM Competition Robots

Project Context as of 25 June 2026
Title: Save and Rescue Robots (decided by Fablab even though they were not agreeing before)

The adjusted 8-day plan (~90–120 productive min/day):

## Prerequisites (pre-workshop instructor prep — not part of any student day)

### Networking — three tiers, in priority order
1. **Best: each RPi hosts its own WiFi hotspot, one per team** (e.g. `Team1-Robot`, `Team2-Robot`, ...). The fastest and most reliable of the three tested so far. Each team's laptop connects straight to their own RPi's hotspot — no venue WiFi involved at all, so no risk of client/AP isolation, and perfect team-to-team isolation for free (physically separate networks, not just distinct `ROS_DOMAIN_ID`s sharing one). Set up via Ubuntu Desktop's GNOME Wi-Fi settings ("Turn On Wi-Fi Hotspot") or `nmcli`.
2. **Backup: a shared WiFi network.** Confirmed working on at least one tested network, but this is genuinely hit-or-miss — a *different* network entirely blocked device-to-device traffic outright (client/AP isolation, a router-level policy, confirmed by `ping` replies showing "Packet filtered" from the gateway itself rather than the actual destination). If falling back to this option, test the actual venue's WiFi in advance — don't assume it behaves like whatever network was last tested on.
3. **Backup of last resort: run `laptop_controller` directly on the RPi** (e.g. via RDP — see `rpi5_rdp_setup_log.md`) instead of on a separate laptop. Manual control still works, but there's no FPV this way — no separate device left to show a live camera feed on while driving.

Whichever tier is used, options 1 and 2 both still need the laptop-side ROS 2 setup in `ros2_journey.md` Journey 2 — WSL2, mirrored networking mode, matching `ROS_DOMAIN_ID`, the two Windows Firewall rules (option 3 runs everything on the RPi itself, no laptop ROS 2 install needed at all). That setup has several non-obvious failure points (a symlink/Developer Mode gotcha, a stale-daemon issue after network changes) that took real troubleshooting even one-on-one — students should never be debugging this live. Set up and verify every team's laptop in advance.

### Boot automation — RPi should need zero commands after power-on

For competition/demo day, nobody should be typing anything after flipping the power switch — no login, no manually running each node in its own terminal. Three independent pieces; combine all three for a genuinely hands-off boot. (Placeholders below like `<pkg1>`, `<your-service-name>` are illustrative — substitute this project's actual package/node names and whatever absolute paths apply on the machine being set up; none of this is pinned to one specific file layout.)

**1. Skip the login screen (autologin).**
- Raspberry Pi OS: `sudo raspi-config` → System Options → Boot / Auto Login → Desktop Autologin.
- Ubuntu Desktop (what this RPi actually runs — `raspi-config` doesn't exist on Ubuntu): edit `/etc/gdm3/custom.conf`, and under `[daemon]` add:
  ```ini
  AutomaticLoginEnable = true
  AutomaticLogin = <your-username>
  ```
  This only skips the login screen — it does **not** remove the account password, so SSH and `sudo` still work normally.

**2. Make the RPi always boot as its own WiFi hotspot** (Networking tier 1 above). To guarantee it's *only* ever the hotspot — no dependency on a venue/home network being in range — disable autoconnect on every other saved WiFi profile and leave it enabled only on the hotspot connection:
```bash
nmcli connection show                                                  # list all saved profiles
nmcli connection modify <other-wifi-name> connection.autoconnect no    # repeat per other profile
nmcli connection modify <hotspot-name> connection.autoconnect yes
```

**3. Auto-launch the ROS 2 nodes with systemd** — not a desktop autostart entry, since that depends on a graphical session being active. Two pieces:

**a. A launch file** bundling every node that needs to run on the RPi, in its own small dedicated package rather than stuffed inside one of the node packages (it doesn't belong to any single one of them). Following this repo's `<concept>_test` naming convention, e.g. `bringup_test`:
```python
# <bringup_package>/launch/<name>.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(package='<pkg1>', executable='<node1>'),
        Node(package='<pkg2>', executable='<node2>'),
        # one Node(...) per node that needs to start on the RPi
    ])
```
Register it in that package's `setup.py` (add `import os` and `from glob import glob` at the top, then a `data_files` entry):
```python
data_files=[
    ...,
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
],
```
Test it standalone before wiring up systemd: `ros2 launch <bringup_package> <name>.launch.py`.

**b. A systemd service** reproducing "source ROS 2, source the workspace, run the launch file" with no terminal and no interactive shell involved:
```ini
# /etc/systemd/system/<your-service-name>.service
[Unit]
Description=<description>
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=<your-username>
Environment=ROS_DOMAIN_ID=<your-domain-id>
ExecStartPre=/bin/bash -c 'until ip -4 addr show <wifi-interface> | grep -q "inet <hotspot-ip>"; do sleep 1; done'
ExecStart=/bin/bash -c "source /opt/ros/<distro>/setup.bash && source <absolute-path-to-workspace>/install/setup.bash && ros2 launch <bringup_package> <name>.launch.py"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now <your-service-name>.service
journalctl -u <your-service-name> -f     # watch it live
```
Manage it afterward with `sudo systemctl stop|start|restart <your-service-name>.service` — there's no terminal window to `Ctrl+C` anymore, that's the point of moving it to systemd.

**Before assuming this is done**, see "ROS 2 nodes launched via systemd are invisible..." in Known Issues & Fixes below — a systemd-launched node is invisible to everything else, even another process on the same machine, unless `ROS_DOMAIN_ID` is set directly on the service. It does not inherit `~/.bashrc`.

### Firmware
Test the full firmware (drive + speed + claw + ultrasonic) on the actual **Arduino Nano** each team will use in competition, not just a dev unit — the Nano is the primary, actively-developed target now (see Confirmed Hardware & Software below), and its limited PWM-capable pins mean a servo/motor pin conflict can be specific to which physical pins a given board actually got wired to.

Day 1 — Brief, Teams & Build. Ice breakers and team grouping, then an overview of what the next 8 days look like. Straight into assembling the kit chassis: motors, wheels, mount the boards, one guided solder joint as a real taste. Win: a fully wired-up robot that powers on.

Day 2 — Arduino: Make It Move. Introduce VS Code and PlatformIO, plus enough Linux/project-structure basics to keep the codebase clean. Progression from hello world → blink → the L298N motor driver → the claw servo → any other actuators/sensors on the robot, each tested individually as they're wired in. Win: every actuator and sensor on the robot has been individually tested and responds to code they wrote.

Day 3 — ROS Foundations. Control is laptop-only for the rest of the workshop, so this day is entirely about building a real mental model of ROS before depending on it: what ROS is and why it exists, the publish/subscribe model, Linux command basics. The concrete deliverable is writing their own working publisher and subscriber pair, so the structure isn't just theory. Win: everyone has a working mental model of ROS and has written and run their own pub/sub pair.

Day 4 — Serial: From Topic to Actuator. Turn Day 3's pub/sub knowledge into action — build the serial bridge node so messages published from the laptop reach the Arduino Nano and actually move something. Win: every actuator on the robot can be triggered from the laptop over ROS.

Day 5 — Computer Vision They Build. Working from a provided OpenCV scaffold, they implement/tune HSV color detection themselves — find a target color in the camera frame and report where it is (left / right / center). Win: their code makes the robot see the target color and know where it is.

Day 6 — Automation: Tracking. Combine vision and actuators — can start at the tail end of Day 5 if time allows. Build simple closed-loop automation: the robot turns to keep the tracked color centered, rather than reacting to single keypresses. Win: the robot autonomously tracks and centers on the target.

Day 7 — Buffer / Customization. Open day for experimentation and extra features — ultrasonic sensors, an LED strip that reacts to the detected color, whatever teams want to add.

Day 8 — Competition & Showcase. Drive around the FabLab rescuing targets, using a mix of FPV (manual) and automatic (tracking) control, then judged awards, certificates, and a showcase where each team explains what they built and coded. Win: they compete with a robot whose brain and code are genuinely theirs.

Story: we need to think of a story for the camp (final scenario) — needs further detail.

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

### ROS 2 discovery randomly breaking, on the same machine and across machines (root cause never confirmed)
**Symptom:** `ros2 topic list`/`echo` hanging indefinitely with zero output, and even `talker`/`listener` on the *same* machine failing to discover each other, intermittently. No single fix worked reliably twice in a row — sometimes a `ros2 daemon stop`/`start` fixed it, sometimes it needed a full `wsl --shutdown`, sometimes a full Windows restart.

**Investigation:** `echo $ROS_AUTOMATIC_DISCOVERY_RANGE` kept printing `SUBNET` in supposedly-fresh terminals, even after `unset`, a full WSL restart, and a full Windows restart. Searched for where it was set: `.bashrc`, `.profile`, `.bash_profile`, `/etc/environment`, `/etc/profile`, `/etc/profile.d/*`, a full recursive grep of the home directory and `/etc`, `systemctl show-environment`, Windows User/Machine environment variables, and Windows Terminal's own `settings.json`. It wasn't in any of them. The RPi — a completely separate machine — showed the same `SUBNET` value independently, which rules out anything Windows/WSL-specific and suggests it might just be ROS 2 Jazzy's own default, but this was never actually confirmed.

**Fix:** None confirmed. Whatever actually resolved it coincided with a full restart of both machines plus reconfirming plain `ping` connectivity before retrying ROS 2 — after that, discovery worked reliably. Whether the env var was ever the real cause, or just a red herring that happened to clear alongside an unrelated fix, is unknown. If this recurs: check `ping` between the two machines *first*, before chasing this variable again.

### ROS 2 nodes launched via systemd are invisible to everything else, even locally (`ROS_DOMAIN_ID` not inherited)
**Symptom:** Nodes started manually (`ros2 launch ...` typed in a terminal) are discovered fine — from the laptop, from a second terminal on the same RPi, everywhere. The *exact same* launch file, run automatically via a systemd service instead, is invisible everywhere — including `ros2 node list` run locally on the RPi itself, right next to the running service. Changing the network (WiFi vs. hotspot, timing, firewall) makes no difference either way, which is what makes this one easy to misdiagnose as a networking problem first.

**Cause:** `ROS_DOMAIN_ID` (see `ros2_journey.md` step 8b) was only ever set via `export ROS_DOMAIN_ID=<n>` in `~/.bashrc`. `.bashrc` only loads in interactive shells — a systemd service's process never reads it, so it silently defaults to domain `0` instead of whatever the rest of the fleet uses. DDS domains are fully isolated from each other, so a domain-`0` node is invisible to anything expecting the real domain, even on the same machine over loopback — this has nothing to do with the network layer at all.

**Fix:** Set the domain ID directly on the systemd unit instead of relying on `.bashrc` being sourced:
```ini
[Service]
Environment=ROS_DOMAIN_ID=<n>
```
To verify what a running service's process actually has (don't assume `.bashrc` exports apply just because they work in every terminal you've tested):
```bash
cat /proc/<pid>/environ | tr '\0' '\n' | grep ROS_DOMAIN_ID
```

---

## Confirmed Hardware & Software

### Raspberry Pi 5
- **OS:** Ubuntu 24.04.4 LTS (Noble Numbat)
- **Architecture:** aarch64 (ARM64)
- **ROS:** ROS 2 Jazzy
- **Note:** VS Code snap install does not work on ARM64 — use the `.deb` package from the official VS Code website instead

### Microcontroller
- **Arduino Nano (ATmega328P)** — the actual, actively-developed target. Firmware lives in `testing/nano_serial_receiving_test/src/main.cpp`: drive, per-side speed, claw servo, ultrasonic distance sensing, and auto/manual mode switching, all driven by serial commands from the RPi.
- An ESP32 (`testing/serial_data_recevinging_test/src/main.cpp`) was used earlier as a stand-in before a Nano was available. Kept in the repo for reference only — it's not been updated to match the current serial protocol and shouldn't be used to test against real hardware.
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
RPi ↔ Nano serial bridge. Runs **on the RPi**. `direction_to_serial` has two independent jobs:
- **Write side** (unchanged since it was first written): subscribes to the `Direction` topic and forwards whatever string it receives, unchanged, over serial to the Nano — it's protocol-agnostic, doesn't parse or care what the message content is, just relays it.
- **Read side** (added alongside auto-tracking/claw-grab): polls the serial connection for lines the Nano sends unprompted, and republishes them as ROS topics — `MODE,<mode>` becomes `ControlMode`, `DISTANCE,<cm>` becomes `UltrasonicData`. Same "don't interpret, just pass through" philosophy as the write side — it doesn't decide anything, only reports what the Nano says.

`direction_publisher` (also in this package) publishes mock alternating `forward`/`backward` messages — it was the original stand-in used to test the pub/sub wiring before a real controller existed. **It's now superseded by `laptop_controller_test`'s `laptop_controller` node** (see below) and its message content (`forward`/`backward`, lowercase) no longer matches the current protocol — don't use it to test against real hardware anymore, it's kept only as a minimal pub/sub example.

**Serial protocol** — implemented in `testing/nano_serial_receiving_test/src/main.cpp` (the actual, current Nano firmware; the older `testing/serial_data_recevinging_test/src/main.cpp` is the retired ESP32 reference and does **not** match this). Plain-word commands, one per line, no numeric codes/magic numbers for anything that isn't a genuine value the hardware needs:
- `FORWARD` / `BACKWARD` / `LEFT` / `RIGHT` / `STOP` — manual driving. Only one action at a time (tank-style: can't turn and drive forward simultaneously) — falls out naturally since the firmware only ever tracks one active command. Turning pivots in place (one side's motors forward, the other side's backward); see the comment above `turnLeft()`/`turnRight()` for the left/right pin assumption, which may need swapping once tested on the real chassis.
- `SPEED,<left>,<right>` — independent per-side PWM (0-255). Manual mode always sends equal values; automatic tracking biases one side faster than the other while driving `FORWARD`, line-follower style, instead of pivoting.
- `CLAW,OPEN` / `CLAW,CLOSE` — servo to its calibrated open/close angle (found via `servo_test`, not 0/180).
- `MODE,AUTO` / `MODE,MANUAL` — a *request*; the Nano is the final authority on whether/when it actually switches, and reports back over serial either way (see below).
- **The Nano also reports back, unprompted**, roughly every 100ms: `MODE,<mode>` and `DISTANCE,<cm>` (from the onboard ultrasonic sensor). This is also the safety backstop for auto-grab — while in `AUTO` mode, if the ultrasonic reading drops under 10cm, the Nano closes the claw and reverts to `MANUAL` on its own, regardless of what commands are still arriving from the RPi, so a stray stale automatic command right at the mode transition can't cause a bad grab.

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

> **Student-facing, but given, not written.** Manual control for Day 3+ *is* this package — students are given this code rather than writing it themselves (unlike `py_pubsub_test`, which they do write, as their Day 3 deliverable). Their job is learning to use it (the keybindings, what the HUD shows), not authoring it. It's still true that the RPi ↔ laptop ↔ hardware chain testing during setup happened through this same package — that's just no longer its *only* purpose.

Runs **on the laptop** (via WSL2 — see `ros2_journey.md` Journey 2), not the RPi. Opens a `pygame` window and reads arrow-key input with real `KEYDOWN`/`KEYUP` events (press = fires once, release = fires once — no flicker, unlike an earlier terminal-based attempt that approximated "held down" with a timeout).

**Keyboard controls:**
| Keys | Action |
|---|---|
| Arrow keys | Drive (held = moving, released = stop) |
| 1 / 2 / 3 / 4 | Set speed, low to high |
| Q / W | Claw open / close |
| 9 / 0 | Camera view: raw / box (detection overlay) |
| O / P | Request automatic / manual mode |

Publishes movement/speed/claw commands as plain-word `String` messages on `ManualDirection` (not `Direction` directly — see `command_switcher_test` below for why), and mode-switch requests on `ModeRequest`. Subscribes to `ControlMode` and `UltrasonicData` to show the robot's actual current mode and distance reading as a HUD overlay in the corner of the video feed — sourced from what the Nano reports, not assumed from whatever was last sent.

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

**This requires cross-machine ROS 2 networking to be set up first** (laptop and RPi are two separate machines, not two nodes on one machine) — see Prerequisites above for the three networking options, and `ros2_journey.md` Journey 2 for the WSL2/ROS 2 side of options 1-2.

### camera_feed_test (testing/ros2_test_workspace/src/camera_feed_test)

Runs **on the RPi**. `camera_feed_publisher` opens the Logitech C310 (`cv2.VideoCapture`, V4L2 backend, hardware MJPG — see the wobble fix above) at 1280x720 and does two things every frame, regardless of view mode:
- **Detects the target**: checks each calibrated color in priority order (`RED` → `GREEN` → `BLUE`, first match wins — sequential, not simultaneous, so two differently-colored objects in frame don't produce two competing detections) and publishes the result on `TargetDetails` as `<color>,<offset>` (offset: -1.0 fully left, 0.0 centered, 1.0 fully right) or `NONE`. Published on `qos_profile_sensor_data` — only the latest detection ever matters, a stale one shouldn't be queued/retried. This runs even while the HUD is showing `RAW`, because `automatic_direction_test` needs it regardless of what's being displayed.
- **Publishes the video frame** as a JPEG-encoded `sensor_msgs/CompressedImage` on `CameraFeed`, same QoS reasoning as `Direction`: on a network hiccup, video should drop stale frames rather than queue them up and add lag. Subscribes to `CameraViewMode` (`RAW`/`BOX`, set by `laptop_controller` on a keypress) to decide whether to draw the detection box + position label onto the frame before publishing.

`laptop_controller_test`'s `laptop_controller` node subscribes to `CameraFeed` and decodes/displays each frame in the same pygame window used for keyboard control, so one window shows the live feed while driving.

```bash
# On the RPi
cd testing/ros2_test_workspace
source install/setup.bash
ros2 run camera_feed_test camera_feed_publisher
```

### color_detection_tool.py (testing/ros2_test_workspace/src/camera_feed_test/camera_feed_test/color_detection_tool.py)

Standalone HSV color-tuning tool — **not a ROS2 node**, run directly with `python3 color_detection_tool.py` (no `colcon build`/`ros2 run` needed). Its only job is finding and saving the HSV threshold range that isolates a target color (e.g. a rescue target) in the camera feed, robust to lighting changes. It doesn't publish anything itself — its only lasting output is `color_ranges.json`, written next to the script, which `camera_feed_publisher` reads via `range_for_color()` instead of re-tuning from scratch.

Uses HSV, not RGB — Hue/Saturation/Value separates a color's identity from lighting brightness, so a threshold tuned once holds up much better than an RGB threshold would as light changes. Red is the one color that needs care: it sits at both ends of OpenCV's Hue wheel (0-179), so a single min/max range only catches one side of it. Green and blue don't have this problem and are generally the easiest, most reliable colors to detect indoors (uncommon in backgrounds/skin tones, no hue wraparound) — worth steering teams toward those if red isn't required by the theme.

**How to use:**
1. Run the script. Three windows open: **Camera** (live feed with a detection box + label), **Mask** (black/white threshold preview), **HSV Tuning** (six sliders).
2. Press **1 / 2 / 3** to load a starting point for RED / GREEN / BLUE onto the sliders — the last saved range for that color if one exists, otherwise a rough default.
3. Adjust the sliders while watching the **Mask** window: the goal is white only where the target object is, black everywhere else. Narrow `H Min`/`H Max` first, then raise `S Min`/`V Min` to kill background noise (shadows, skin tone, walls).
4. Press **S** to save the current sliders under the active color's name into `color_ranges.json`.
5. Press **Q** to quit.

Saved ranges reflect whatever lighting was present at save time — if venue lighting differs on the actual day, budget a few minutes to re-tune and re-save rather than trusting old saved values.

### command_switcher_test (testing/ros2_test_workspace/src/command_switcher_test)

Runs **on the RPi**. `command_switcher` is deliberately dumb — its entire job is one if/else, no vision, no serial. Subscribes to `ManualDirection`, `AutomaticDirection`, and `ControlMode`; forwards whichever source matches the current mode onto `Direction`, the same topic `direction_to_serial` has always relayed.

Mode itself is tracked from two places: `ControlMode` (the Nano's own confirmed mode, always wins eventually) and `ModeRequest` (published the instant a mode-toggle key is pressed, applied optimistically before the Nano's round-trip confirmation arrives) — the optimistic part matters because that round trip is exactly the window where a stray `AutomaticDirection` message could otherwise still get forwarded and undo a manual override.

### automatic_direction_test (testing/ros2_test_workspace/src/automatic_direction_test)

Runs **on the RPi**. `automatic_direction_controller` subscribes to `TargetDetails` and publishes `AutomaticDirection` commands to keep the target centered — `FORWARD` plus `SPEED,<left>,<right>` with one side biased faster than the other proportional to how far off-center the target is (line-follower style steering, not a pivot turn). Publishes `STOP` if the target's `NONE` (out of view). No dedupe on repeated commands here on purpose — `command_switcher` may have been silently dropping every message while this wasn't the active mode, so there's no reliable local memory of what the Nano last actually received; it resends fresh every cycle instead.

**✅ Confirmed working end-to-end (manual + camera):** laptop keypress (pygame) → `Direction` topic over the cross-machine ROS 2 network → RPi's `direction_to_serial` → serial → the Nano → motors actually drive, **at the same time as** the RPi's `camera_feed_publisher` → `CameraFeed` topic → the laptop's pygame window, showing live 720p video while driving. Full chain, both machines, tested and working.

**✅ Confirmed working end-to-end (automatic tracking + claw grab):** the full loop (`camera_feed_publisher` → `TargetDetails` → `automatic_direction_controller` → `AutomaticDirection` → `command_switcher` → `Direction` → Nano) drives the robot toward the tracked target in `AUTO` mode; once the Nano's ultrasonic reading drops under 10cm, it closes the claw and reverts to `MANUAL` on its own, exactly as designed. Tested and working.

