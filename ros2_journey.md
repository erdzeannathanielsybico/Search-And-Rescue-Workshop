# ROS 2 Journey — From Ubuntu on the RPi to a Running Node

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

## Note on the laptop

Doing this same journey on the Windows laptop (rather than the RPi) hasn't been attempted yet. WSL2 + Ubuntu was discussed as a likely route, but that's unconfirmed — nothing about the laptop setup should be treated as established until it's actually done.
