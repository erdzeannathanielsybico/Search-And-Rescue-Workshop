# ROS 2 Journey

Two separate journeys to the same destination — "a node is running and talking on a topic" — on two different machines. They're kept as two independent sets of steps rather than merged, since the RPi runs Ubuntu natively and the laptop runs it through WSL2, and the setup steps genuinely differ.

---

# Journey 1 — RPi (native Ubuntu)

This is the top-down path actually followed to get from "RPi with Ubuntu on it" to "a node is running and talking on a topic." It's a reference for retracing the steps, not a record of the exact commands typed at the time — the ROS 2 install itself wasn't logged when it happened, and was done by following the official docs directly rather than a fixed script.

---

## 1. Prerequisite: Ubuntu

ROS 2 Jazzy needs **Ubuntu 24.04 (Noble)**. The RPi 5 has this as its actual OS (see `inital_setup_history.md` for the SD card flash + first boot + SSH setup).

Everything below happens **inside a terminal on the RPi** (SSH or the RDP desktop session — see `rpi5_rdp_setup_log.md`).

---

## 2. Install ROS 2 Jazzy (once per machine)

Done by following the official installation guide:
**https://docs.ros.org/en/jazzy/index.html**

This is a system-wide install — it lands in `/opt/ros/jazzy/`, not inside any project folder. Broadly, the official docs walk through: setting a UTF-8 locale, enabling the Ubuntu `universe` repo, adding the ROS 2 apt repository + signing key, then `sudo apt install ros-jazzy-desktop` (or `ros-jazzy-ros-base` for a lighter, no-GUI install).

**Source it** so every terminal knows ROS 2 exists:
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Verify: `ros2 --version` should print something referencing Jazzy.

If the exact steps followed diverge from the official docs at any point, **the official docs win** — treat this section as "go there," not as a frozen transcript.

---

## 3. Create a workspace (once per machine)

A **workspace** is just a folder convention — a folder with a `src/` subfolder where packages live; `colcon build` generates `build/`, `install/`, and `log/` next to `src/` when you build.

In this repo, the workspace root is `testing/ros2_test_workspace/`. To create a new one from scratch anywhere:
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build   # builds an empty workspace successfully — just proves the tool works
```

---

## 4. Create a package (once per group of related nodes)

A **package** is a folder inside `src/` that bundles related nodes together (like `serial_bridge_test` bundling `direction_publisher` and `direction_to_serial`).

```bash
cd testing/ros2_test_workspace/src   # always from inside the workspace's src/
ros2 pkg create --build-type ament_python --dependencies rclpy std_msgs my_package_name
```

This generates:
- `my_package_name/my_package_name/` — where actual node `.py` files go
- `setup.py` — declares the package and which files are runnable nodes
- `package.xml` — declares dependencies (e.g. `rclpy`, `std_msgs`, `python3-serial`)
- `resource/`, `test/` — boilerplate ROS 2 expects

`--build-type ament_python` is what every package in this repo uses (as opposed to `ament_cmake`, which is for C++ packages).

---

## 5. Write a node

A **node** is a Python class extending `rclpy.node.Node`, as a `.py` file inside `my_package_name/my_package_name/`. `direction_to_serial.py` and `direction_publisher.py` are real examples already in this repo:
- `__init__` sets up publishers/subscriptions
- a callback method handles incoming messages (if subscribing)
- a `main()` function does `rclpy.init()` → create the node → `rclpy.spin()` → `rclpy.shutdown()`

---

## 6. Register the node as a runnable command

Writing the `.py` file isn't enough — `ros2 run` needs to know it exists. That's declared in `setup.py`'s `entry_points`:
```python
entry_points={
    'console_scripts': [
        'my_node = my_package_name.my_node_file:main',
    ],
},
```
This is exactly how `direction_publisher.py` becomes runnable as `ros2 run serial_bridge_test dir_pub` — see `setup.py` in `serial_bridge_test/`.

---

## 7. Build and run

```bash
cd testing/ros2_test_workspace       # always the workspace root, never inside src/
colcon build

source install/setup.bash            # needed in every NEW terminal
ros2 run my_package_name my_node
```

## 8. Sanity-check it's alive

```bash
ros2 node list      # is your node running?
ros2 topic list     # what topics exist?
ros2 topic echo /some_topic   # watch messages flow live
```

---

## Summary of the hierarchy

```
Ubuntu (OS)
 └─ ROS 2 install (/opt/ros/jazzy — one per machine)
     └─ Workspace (a folder with src/ — one per project, e.g. ros2_test_workspace)
         └─ Package (a folder in src/ — groups related nodes, e.g. serial_bridge_test)
             └─ Node (a .py file — one running program, e.g. direction_to_serial.py)
```

Each layer is only set up once, then everything above it in this list is reused: no reinstalling ROS 2 per workspace, no remaking the workspace per package.

---

# Journey 2 — Windows Laptop (via WSL2)

The same destination, but the laptop is Windows, and ROS 2 doesn't run natively there. This journey adds a layer underneath everything in Journey 1: getting a real Ubuntu environment running inside Windows first.

---

## 1. Install WSL2 + Ubuntu 24.04

In an **Administrator PowerShell**:
```powershell
wsl --install -d Ubuntu-24.04
```
This enables the Windows features WSL needs and downloads the Ubuntu 24.04 image (matching the RPi's Noble/Jazzy pairing). A restart is required after this step.

If, after restarting, `wsl -l -v` still shows no distributions installed, the feature-enable step consumed the restart but the distro itself didn't finish downloading — just run the same install command again; it resumes from "download Ubuntu" without needing another restart.

## 2. First launch and account setup

Launch **Ubuntu-24.04** from the Start menu (or run `wsl`). First boot asks you to create a Unix username/password — separate from both your Windows login and the RPi's account, though there's no harm reusing the same username/password for convenience on a local dev machine.

Verify the version:
```bash
lsb_release -a
```
Should show `Release: 24.04`, `Codename: noble`.

## 3. Install ROS 2 Jazzy

Identical to Journey 1, step 2 — same official docs (**https://docs.ros.org/en/jazzy/index.html**), same `ros-jazzy-desktop` package, same `source /opt/ros/jazzy/setup.bash` and `~/.bashrc` line. Nothing about this step is laptop-specific.

## 4. Install colcon

`ros-jazzy-desktop` doesn't include colcon. Install the full extension set (not just bare `colcon`, which apt suggests by default):
```bash
sudo apt install python3-colcon-common-extensions
```

## 5. The WSL-specific gotcha: symlinks on `/mnt/c/`

Building an existing repo checked out on the Windows side (reachable from WSL at `/mnt/c/...`) can fail with:
```
error: [Errno 1] Operation not permitted
```
This happens because `ament_python` packages create a symlink during install, and Windows only allows admins to create symlinks by default — `/mnt/c/` is a real Windows-managed drive, so this restriction applies even though the command is run from Linux.

**Fix:**
1. Windows Settings → search **"developer"** → **Use developer features** → toggle **Developer Mode** ON.
2. Fully restart the WSL VM (closing the terminal window is *not* enough — the VM keeps running in the background). From a plain Windows PowerShell:
   ```powershell
   wsl --shutdown
   ```
3. Reopen the Ubuntu terminal and retry `colcon build`.

If it still fails after this, the fallback is to stop building against `/mnt/c/` and `git clone` the repo into WSL's own native filesystem (`~/...`) instead — native Linux filesystem never hits this symlink restriction, at the cost of maintaining a second checkout that needs its own `git pull`/`push`.

## 6. Build and run — same as Journey 1

Once the symlink issue is resolved, everything from Journey 1 steps 3 onward applies identically:
```bash
cd /mnt/c/Development/My_Projects/Search-And-Rescue-Workshop/testing/ros2_test_workspace
colcon build

source install/setup.bash
ros2 run py_pubsub_test talker      # terminal 1
ros2 run py_pubsub_test listener    # terminal 2 (new WSL window/tab — needs its own `source` too)
```

## 7. The actual day-to-day workflow

- **Editing node code**: normal VS Code on the Windows side (`c:\Development\...`), same as always.
- **Running anything ROS 2** (`colcon build`, `ros2 run`, etc.): must happen in a WSL Ubuntu terminal — `ros2` doesn't exist as a Windows command.
- These aren't two different copies of the code — `/mnt/c/Development/...` (WSL) and `c:\Development\...` (Windows) are the same files on disk. Saving in VS Code is instantly visible to WSL, no syncing needed.
- Every **new** WSL terminal window/tab needs ROS 2 sourced before `ros2` commands work, unless the `~/.bashrc` line from step 3 is in place — if a fresh terminal says `ros2: command not found`, that's why.

## 8. Cross-machine networking (laptop ↔ RPi)

Everything above gets ROS 2 running *on* the laptop. None of it makes the laptop's nodes able to see the RPi's nodes — that's a separate problem, because two machines talking to each other over a real LAN is fundamentally different from two nodes on the same machine talking over `localhost`.

**8a. Enable WSL2 mirrored networking.** By default WSL2 sits behind its own private NAT subnet, invisible to the rest of the LAN. Check support first:
```powershell
wsl --version   # needs 2.0.0+
```
Then edit (or create) `%UserProfile%\.wslconfig` on the **Windows** side:
```ini
[wsl2]
networkingMode=mirrored
```
Restart WSL for it to take effect:
```powershell
wsl --shutdown
```
Verify it worked — `hostname -I` inside WSL should now show an IP on your actual home LAN (e.g. `192.168.1.x`, matching the RPi's subnet), not a `172.x.x.x` NAT address.

**8b. Match `ROS_DOMAIN_ID` on both machines.** This is the number DDS uses to group nodes into the same "network" — nodes with different domain IDs never see each other, even on the same physical LAN (see the note below on why this matters with multiple teams). Run on **both** the laptop and the RPi:
```bash
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source ~/.bashrc
```

**8c. Open two Windows Firewall holes.** Windows blocks unsolicited inbound traffic by default — this is what actually blocked cross-machine discovery, not WSL2 or ROS itself. In an **elevated PowerShell** on the laptop:
```powershell
# Lets other devices ping this machine (diagnostic only, not required by ROS 2 itself)
New-NetFirewallRule -DisplayName "Allow ICMPv4-In" -Protocol ICMPv4 -IcmpType 8 -Direction Inbound -Action Allow

# Lets ROS 2's actual DDS discovery/data traffic (UDP) reach this machine.
# Port range is calculated from ROS_DOMAIN_ID: base = 7400 + 250 * domain_id.
# For domain 42: base = 17900, so open a small range above it for a few nodes.
New-NetFirewallRule -DisplayName "Allow ROS2 DDS (domain 42)" -Protocol UDP -LocalPort 17900-17930 -Direction Inbound -Action Allow
```
The RPi side (native Ubuntu, no Windows Firewall) didn't need an equivalent rule in this setup — if the RPi ever has `ufw` or another firewall enabled, the same UDP range would need opening there too.

**8d. Verify with ROS 2's own demo nodes** (not custom code yet — isolates "is the network right" from "is my code right"):
```bash
# On the RPi
ros2 run demo_nodes_py talker

# On the laptop
ros2 run demo_nodes_py listener
```
Success looks like the laptop printing `I heard: [Hello World: N]` messages coming from the RPi.

**Why each team needs a different `ROS_DOMAIN_ID`:** if multiple robots (e.g. multiple workshop teams) share the same WiFi network with the *same* domain ID, DDS discovery groups them all together — every team's `Direction` topic would be the same shared topic, so one team's controller could accidentally drive another team's robot, or a listener could receive a mix of everyone's messages. Domain ID is exactly the mechanism that keeps separate ROS 2 systems on the same physical network from crosstalking. Each team needs its own number (e.g. 42, 43, 44, ...), and — since the firewall port range is calculated *from* the domain ID — each team's controller laptop needs its own matching UDP rule for its own domain ID's port range, not a shared one.

---

**✅ Confirmed end-to-end, after all 8 steps above:** laptop (`laptop_controller_test`, pygame keypresses) → `Direction` topic over the cross-machine network → RPi (`serial_bridge_test`'s `direction_to_serial`) → serial → ESP32 (`main.cpp`) → motors actually turning. The full two-machine ROS 2 chain works.
