# ROS 2 Journey

Three separate journeys to the same destination — "a node is running and talking on a topic" — on three different machines. They're kept as independent sets of steps rather than merged, since the RPi runs Ubuntu natively, the Windows laptop runs it through WSL2, and an Apple Silicon Mac runs it through Docker — the setup steps genuinely differ.

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

## Quick copy-paste install (fleet provisioning)

Steps 1–4 below, broken into individual copy-paste steps — for setting up a batch of new laptops fast rather than reading the narrative version. Assumes **Windows 11**. Safe to run even if WSL/Ubuntu is already partially installed — `wsl --install` just confirms it's already there and does nothing destructive.

Run each block below **one at a time**, waiting for it to finish before pasting the next — especially the update/upgrade and desktop-install steps, which pull hundreds of MB and look "stuck" (rather than just slow) if bundled together with everything else in one paste.

**Phase 1 — PowerShell (as Administrator):**
```powershell
wsl --install -d Ubuntu-24.04
```
Reboot if prompted (first-time WSL enable only), then launch **Ubuntu-24.04** from the Start menu — it'll prompt for a new Unix username and password. Set the **same username and password on every laptop** (e.g. `user`/`user`) directly at this prompt, so every `sudo` prompt in Phase 2 takes the same password and the commands below are identical copy-paste across all 9, no per-machine substitution or password-reset step needed afterward. (`user` is what's actually shown at the prompt on the school laptops so far — e.g. `user@HF-LP-4051` — so match that rather than picking a different name.)

**If `sudo` says `Sorry, try again` later on:** Windows admin rights and the WSL Linux user's password are two separate things — being a Windows admin doesn't set or override the Linux password, so a mistyped password at the first-launch prompt (easy to do, since nothing is echoed while typing) leaves `sudo` rejecting every attempt with no indication why. This came up on one of the school laptops. Fix, from PowerShell (doesn't need Administrator):
```powershell
wsl -u root
```
Then, at the `root@...` prompt inside WSL:
```bash
passwd user   # replace 'user' with the actual username shown in the prompt if different
```
Type the new password twice (blind, as usual), then `exit` back out and reopen the normal WSL terminal — `sudo` should accept it now.

**Phase 2 — inside the Ubuntu (WSL) terminal:**

**2a. Locale — check first, only fix if needed:**
```bash
locale
```
If `en_US.UTF-8` isn't in the output:
```bash
sudo apt update && sudo apt install locales -y
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```
(`locale-gen en_US en_US.UTF-8` is often listed as part of this step, but wasn't needed on this laptop — `update-locale` alone fixed it and everything downstream worked fine. Only add it back in if `locale` still doesn't show UTF-8 after the above.)

**2b. Enable the `universe` repo:**
```bash
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y
```

**2c. Add the ROS 2 apt repository.** This originally used the `ros2-apt-source_*.deb` package method from the official docs, but that consistently left `ros-jazzy-desktop` unable to be located in step 2e (apt couldn't see the package at all) — switching to the older GPG-key + `sources.list.d` method fixed it.

**First, prime `sudo` so the block below doesn't stall on a password prompt mid-paste:**
```bash
sudo -v
```
Run this alone and enter the password when asked. This matters because the block below is the *first* `sudo` call in a fresh terminal on a brand-new laptop — if all three lines get pasted at once, the terminal is still sitting at a blind password prompt when lines 2 and 3 arrive, so their text gets fed into the password field instead of run as commands, and everything comes out garbled (this is exactly what broke one of the school laptops). `sudo -v` alone gets the password prompt out of the way first; `sudo` then stays authenticated for the next few minutes, so the paste below runs straight through.
```bash
sudo apt update && sudo apt install curl -y
sudo curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```
The `-f` on `curl` matters: on one school laptop the URL got typo'd (`rosdistro` → `rodistro`), which 404'd — and *without* `-f`, `curl -sSL` silently saved GitHub's 404 error page into the keyring file instead of failing loudly (it was 14 bytes; a real key is ~1KB+). Everything downstream (`apt update`, `ros-dev-tools`) then failed with no obvious cause, because apt just silently ignored the malformed keyring/repo rather than erroring. With `-f`, a bad URL now makes `curl` itself fail instead of writing garbage.

**Verify before moving on:**
```bash
ls -la /usr/share/keyrings/ros-archive-keyring.gpg   # should be ~1KB+, not a few bytes
cat /etc/apt/sources.list.d/ros2.list                # should print the deb [...] packages.ros.org line
```

**2d. Update + upgrade (large download — let it finish before moving on):**
```bash
sudo apt update
sudo apt upgrade -y
```
In the `apt update` output, look for a `Hit:` or `Get:` line mentioning `packages.ros.org` — if it's missing, the repo from 2c isn't actually registered (re-check the two files above) and `ros-dev-tools`/`ros-jazzy-desktop` will fail to locate in the next steps.

**2e. Install the ROS 2 Jazzy desktop package (the other large download):**
```bash
sudo apt install ros-jazzy-desktop -y
```

**2f. Dev tools + colcon:**
```bash
sudo apt install ros-dev-tools -y
sudo apt install python3-colcon-common-extensions -y
```

**2g. rosdep init/update:**
```bash
sudo rosdep init
rosdep update
```

**2h. Source ROS 2 and set the domain ID:**
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source ~/.bashrc
```
`ROS_DOMAIN_ID=42` matches the RPi (Journey 2, step 8b) so each laptop can see its own RPi's nodes. Safe to reuse `42` on all 9 here specifically because each laptop connects to its *own* RPi's hotspot network — they're physically separate networks, not one shared LAN, so the "different teams need different IDs" crosstalk risk doesn't apply.

**Phase 3 — verify:**
```bash
rviz2
rqt
```
Both should open GUI windows — WSLg (built into Windows 11) handles the display automatically, no X server setup needed. Close them once they open; that confirms the install. If a laptop is still on Windows 10, WSLg needs a manual install first — don't run this script on one without checking that first.

The narrative steps below (1–4) cover the same ground with more explanation; step 5 onward covers things this script doesn't handle (the `/mnt/c/` symlink gotcha, and cross-machine networking).

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

If `sudo apt install ros-jazzy-desktop` can't locate the package, the official docs' `ros2-apt-source_*.deb` repo-setup method is the likely cause — see steps 2a–2g in the quick copy-paste script above for the GPG-key + `sources.list.d` method that fixed it here.

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

---

# Journey 3 — Apple Silicon Mac (M-series, via Docker)

Same destination again, but macOS is **Tier 3** for ROS 2 — there are no official binaries, and Jazzy targets Ubuntu 24.04 specifically. Rather than fight a source build, the lowest-friction path is to run the exact same Ubuntu 24.04 + Jazzy environment inside a Docker container. This adds a layer underneath Journey 1, the same way WSL2 does for Journey 2: get a real Ubuntu running first, then Journey 1 applies inside it.

**Two limitations to know up front:**
- **GUI apps (RViz, rqt) are painful.** They need XQuartz forwarding and run slowly. Foxglove (via `foxglove-bridge`, in a browser) or the project's own pygame/OpenCV windows are better bets — but note those still hit the same X-forwarding wall, so a Mac is best used as a *headless* ROS 2 node, not the machine you drive from.
- **USB/serial devices do not pass through** to the container at all on macOS — Docker Desktop has no host USB access. Anything touching the Nano over `/dev/ttyUSB*` (the serial bridge) has to run on the RPi, not here.

## 1. The critical gotcha: image architecture (read before pulling anything)

The obvious image, `osrf/ros:jazzy-desktop`, is **amd64-only**. On Apple Silicon, `docker pull`/`docker run` won't error — it silently falls back to x86 emulation via Rosetta, which makes *everything* (builds, node startup, vision) painfully slow. This is the single biggest trap on Mac.

The official `ros` images (e.g. `ros:jazzy-ros-base`) **are multi-arch** and have a native `arm64` variant. The fix is to build a custom image `FROM ros:jazzy-ros-base` and `apt install ros-jazzy-desktop` ourselves — the arm64 Debian packages for the desktop metapackage exist, even though a prebuilt arm64 *desktop image* doesn't.

After building (step 4), always verify:
```bash
docker image inspect <img> --format '{{.Architecture}}'
```
This **must** print `arm64`. If it prints `amd64`, you're on the emulated path — rebuild from `ros:jazzy-ros-base`, not `osrf/ros:jazzy-desktop`.

## 2. Install Docker Desktop for Mac

Install the **Apple Silicon** build of Docker Desktop (not the Intel one) from https://www.docker.com/products/docker-desktop/. Launch it once and let it finish starting, then confirm the CLI works:
```bash
docker version
```

## 3. Create the workspace on the Mac side

Make the workspace on the host, so git and VS Code operate natively on macOS (the container will mount it in step 5):
```bash
mkdir -p ~/ros2_ws/src
```

## 4. Write the Dockerfile and build a native arm64 desktop image

Create `~/ros2_ws/Dockerfile`:
```dockerfile
FROM ros:jazzy-ros-base

# Desktop metapackage + Foxglove bridge + build tooling.
# The arm64 Debian packages exist even though the prebuilt desktop image doesn't.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-desktop \
        ros-jazzy-foxglove-bridge \
        python3-colcon-common-extensions \
        ros-dev-tools \
    && rm -rf /var/lib/apt/lists/*

# Bake sourcing + domain ID into .bashrc so it survives container recreation.
# Sourcing the workspace is conditional — it won't exist until the first colcon build.
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc \
    && echo "[ -f /ros2_ws/install/setup.bash ] && source /ros2_ws/install/setup.bash" >> /root/.bashrc \
    && echo "export ROS_DOMAIN_ID=42" >> /root/.bashrc
```

Build it as native arm64, then verify the architecture (step 1):
```bash
cd ~/ros2_ws
docker build --platform linux/arm64 -t sar-jazzy .
docker image inspect sar-jazzy --format '{{.Architecture}}'   # MUST print: arm64
```

> Match `ROS_DOMAIN_ID=42` to whatever the rest of the fleet uses (see Journey 2, step 8b) — every machine on the same DDS network needs the same number.

## 5. Create the container (once)

Run it **detached** (`-dit`), mounting the host workspace to `/ros2_ws` and naming it `ros2` so it's easy to reopen:
```bash
docker run -dit \
    --name ros2 \
    -v ~/ros2_ws:/ros2_ws \
    -w /ros2_ws \
    sar-jazzy
```
This creates the container **once**. `docker run` is not how you open each terminal — that would spawn a *new* container every time. To open additional shells into this *same* running container you use `docker exec` (next step). ROS 2 workflows routinely need several shells at once (a node running in one, `ros2 topic echo` in another), and they must all be in the same container to see each other.

## 6. Add an `rs` alias for opening shells

Add to `~/.zshrc` on the Mac:
```bash
alias rs='docker start ros2 >/dev/null && docker exec -it ros2 bash'
```
Reload it (`source ~/.zshrc` or open a new terminal). Now every `rs` starts the container if it's stopped, then drops you into a fresh bash shell inside it — run `rs` in as many terminal tabs as you need, all sharing the one container.

## 7. Verify with ROS 2's own demo nodes

Two `rs` shells, same container:
```bash
# Terminal 1
rs
ros2 run demo_nodes_cpp talker

# Terminal 2
rs
ros2 run demo_nodes_py listener
```
Success is the listener printing `I heard: [Hello World: N]`. If that works, the environment is good and Journey 1 (steps 3 onward) applies inside the container unchanged.

## 8. Day-to-day workflow

Clone repos into `~/ros2_ws/src` **from the macOS side** so git and VS Code run natively (the mount makes them instantly visible inside the container — same-files-on-disk, like WSL's `/mnt/c`):
```bash
# On the Mac (native git / VS Code)
cd ~/ros2_ws/src
git clone <repo-url>
```
Then, **inside the container** (`rs`), build and run:
```bash
cd /ros2_ws
rosdep install --from-paths src --ignore-src -r -y   # pull package deps
colcon build --symlink-install                        # --symlink-install: edit Python without rebuilding
source install/setup.bash                             # every new shell (baked into .bashrc in step 4)
ros2 run <pkg> <executable>
ros2 launch <pkg> <launch-file>
```
Not sure what an executable is called? List them:
```bash
ros2 pkg executables <pkg>
```

**Recurring dependencies belong in the Dockerfile.** Anything you `apt install` *inside* the running container is lost the moment the container is removed (`docker rm ros2`) — the image is what persists, not the container. If you find yourself reinstalling the same package after a rebuild, add it to the Dockerfile's `apt-get install` line (step 4) and rebuild instead.
