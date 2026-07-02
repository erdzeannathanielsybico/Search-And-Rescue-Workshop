# Search-And-Rescue-Workshop
Content for Hashim Search and Rescue Workshop inspired from STEM Competition Robots

Project Context as of 25 June 2026
Title: Save and Rescue Robots (decided by Fablab even though they were not agreeing before)

The adjusted 7-day plan (~90–120 productive min/day):

Day 1 — Brief, Teams & Build. Mission, teams, safety, and straight into assembling the kit chassis: motors, wheels, mount the boards. One guided solder joint as a real taste. Win: a robot they built, and they've held a soldering iron.

Day 2 — Arduino: Make It Move. Wire motors through the driver to the Arduino. Write (from a starter) the drive functions — forward, reverse, turn — understanding the code, not just flashing it. Add and program the servo claw. Win: they coded the robot to drive and grab.

Day 3 — Take Control. Add manual control (Bluetooth + phone app or a USB gamepad). They refine their own driving code, tune speeds and claw angles, and practice picking up objects. Win: a driveable robot they can control and tune.

Day 4 — The Pi Brain: Connect & See. SSH into the Pi (real skill), tour Linux basics, run ros2 node list / topic list / echo, and bring up the live camera stream + camera node. They're now inside the robot's brain and seeing through its eye. Win: they can connect to and operate a ROS robot.

Day 5 — Computer Vision They Build. The core attraction. Working from a provided OpenCV scaffold, they implement/tune the detection themselves — HSV color masking to find a target object, and read out where it is. This is the real "AI vision" skill, authored by them. Win: their code makes the robot recognize the rescue target.

Day 6 — Integrate: Autonomous-Assisted Rescue + Battle Prep. Connect vision to action — the Pi tells the robot where the target is; they drive (or let it assist) to grab and deliver it. Mount the battle pin, practice attack/defend. Win: vision + driving + claw working as one robot.

Day 7 — Competition & Showcase. Two challenges — Rescue (vision-assisted: find and extract the specified objects) and Battle — then judged awards, certificates, and a showcase where each team explains what they built and coded. Win: they compete with a robot whose brain and code are genuinely theirs.

Buffer day: customize as you wish.

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

## Known Issues & Fixes

### Raspberry Pi — WiFi connects but no internet (missing default route)
**Symptom:** wlan0 has an IP address but `ip route show` is empty and pings to external IPs fail with "Network is unreachable." Git, SSH, and anything network-dependent will fail.

**Cause:** DHCP assigned an IP but didn't install the default gateway route — a NetworkManager hiccup on reconnect.

**Fix:** Turn the wifi connection off and on again to force a clean DHCP handshake:
```bash
sudo nmcli connection down "Addi" && sleep 3 && sudo nmcli connection up "Addi"
```
Replace `"Addi"` with your wifi network name if it changes. Verify with `ip route show` — you should see a `default via 192.168.1.x dev wlan0` line.

---

## Confirmed Hardware & Software

### Raspberry Pi 5
- **OS:** Ubuntu 24.04.4 LTS (Noble Numbat)
- **Architecture:** aarch64 (ARM64)
- **ROS:** ROS 2 Jazzy
- **Note:** VS Code snap install does not work on ARM64 — use the `.deb` package from the official VS Code website instead

### Microcontroller
- Arduino Nano (ATmega328P) — handles low-level motor control via serial commands from RPi
- Cannot run micro-ROS (insufficient memory) — communicates with ROS via a serial bridge node on the RPi

### Motor Driver
- 2x L298N motor driver modules
- Motor power: 9V supply into the 12V terminal (5V breadboard PSU insufficient for 4 motors)
- L298N 5V jumper left ON

### Motors
- 4x DC motors (6V, 130 RPM)

---

## ROS2 Workspace — Building & Running

### py_pubsub (testing/ros2_pubsub_test)
Talker/listener test nodes.

**Build** — always `cd` into the workspace directory first. Running `colcon build` from anywhere else (e.g. the repo root) scatters duplicate `build/`, `install/`, `log/` directories outside the workspace:
```bash
cd testing/ros2_pubsub_test
colcon build
```

**Run** — needs `source install/setup.bash` in *every new terminal*, run from the workspace directory (`testing/ros2_pubsub_test/`). Sourcing without `cd`-ing there first will fail to find the package:
```bash
# Terminal 1
cd testing/ros2_pubsub_test
source install/setup.bash
ros2 run py_pubsub talker

# Terminal 2
cd testing/ros2_pubsub_test
source install/setup.bash
ros2 run py_pubsub listener
```

