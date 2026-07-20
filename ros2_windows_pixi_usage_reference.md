# ROS 2 Windows (pixi) — Command Reference vs RPi (Ubuntu)

Quick-glance equivalents between the RPi's native Ubuntu ROS 2 workflow and this Windows/pixi setup. See `ros2_windows_pixi_install.md` for the one-time install steps.

Updated 19 July 2026 after a full successful end-to-end test (laptop_controller ↔ RPi camera feed, live over the hotspot).

---

## ⭐ Full activation sequence — every new terminal, in order

Two separate things need sourcing every time, not one. Paste this whole block:

```
cd C:\pixi_ws
pixi shell
call C:\pixi_ws\ros2-windows\local_setup.bat
cd C:\dev\Search-And-Rescue-Workshop\testing\ros2_test_workspace
call install\setup.bat
```

- Must be **Command Prompt**, not PowerShell — `call` doesn't work there
- `pixi shell` only works if you're inside `C:\pixi_ws` (where `pixi.toml` lives) when you run it
- `call install\setup.bat` only works if you're inside the workspace root (relative path) — that's why the second `cd` matters
- Skipping the last two lines is exactly what causes `Package 'laptop_controller_test' not found`
- Once all 5 lines have run, you can `ros2 run` anything in the workspace for the rest of that terminal session — no need to repeat any of this until you open a new window

## Setting ROS_DOMAIN_ID

| RPi | Windows |
|---|---|
| `export ROS_DOMAIN_ID=42` | `set ROS_DOMAIN_ID=42` (this window only) |
| Added to `~/.bashrc` for permanence | `setx ROS_DOMAIN_ID 42` (permanent) |

✅ Confirmed — `setx` genuinely persists across a full VS Code close/reopen with zero re-typing (`echo %ROS_DOMAIN_ID%` still printed `42` in a brand new window).

## Creating a workspace / package

⚠️ Still untested on Windows — same commands as Linux, expected to work once the environment above is active, but hasn't been run yet:
```
mkdir C:\dev\ros2_ws\src
cd C:\dev\ros2_ws
ros2 pkg create --build-type ament_python my_package_name
```

## Building the workspace

| RPi | Windows |
|---|---|
| `colcon build` | `colcon build` (identical) |

✅ **Confirmed working, no issues.** All 7 packages built clean on the first try. Use plain `colcon build` — **not** `--symlink-install`, which is known to break on Windows without Developer Mode. Confirmed Developer Mode was **off** on the test laptop and the plain build still worked fine, so this isn't a concern either way.

## Sourcing your own workspace after building

| RPi | Windows |
|---|---|
| `source install/setup.bash` | `call install\setup.bat` |

✅ Confirmed — see the full activation sequence at the top.

## Running a node

| RPi | Windows |
|---|---|
| `ros2 run my_package_name my_node` | Identical |

⚠️ **No tab-completion on Windows.** `ros2 run <Tab>` autocompletes on the RPi's bash; Command Prompt has no equivalent. Type package and node names out in full.

## Sanity-check commands (identical on both)

```
ros2 node list
ros2 topic list
ros2 topic echo /some_topic
```

**Use `ros2 node list` to check for duplicate nodes** if commands seem to be arriving twice on the RPi (see Known Issues below) — if `laptop_controller` shows up more than once, an old terminal/VS Code window is still running it in the background.

## Installing pygame (needed for laptop_controller)

| RPi/Ubuntu | Windows |
|---|---|
| `sudo apt install python3-pygame` (not pip — PEP 668 blocks it) | `pip install pygame opencv-python` |

✅ Confirmed working, with one caveat: the first attempt(s) may fail with `WinError 10054` (connection forcibly closed) partway through downloading pygame's `.whl` file — this is a flaky/inspected connection issue, not a real error. **Fix:** add retries:
```
pip install pygame opencv-python --retries 10 --timeout 100
```
Took 9 retries to succeed on the test laptop — expect it to take a minute or two, don't panic and cancel it early.

---

## Known issues

**Commands arriving doubled on the RPi (e.g. every keypress fires twice)**
- Very likely caused by two instances of `laptop_controller` running at once — e.g. one left running in an old terminal/VS Code window that never got closed, plus a new one started fresh
- Fix: `ros2 node list`, check for duplicates, close every old terminal window (check the taskbar, not just the visible one) and re-check

**`New-NetFirewallRule` for the DDS port range**
- Not needed on either laptop tested so far — Windows appears to treat the RPi hotspot as a Private network profile by default, which doesn't block DDS discovery
- Still worth knowing as a fallback for IT-managed/domain-joined laptops that may have different default policies — keep this in your back pocket, don't run it pre-emptively unless a laptop fails to connect:
```powershell
New-NetFirewallRule -DisplayName "Allow ROS2 DDS (domain 42)" -Protocol UDP -LocalPort 17900-17930 -Direction Inbound -Action Allow
```

**Pip download resets during `pip install`**
- Not a hotspot/no-internet issue (confirmed happened while on real WiFi with internet) — most likely antivirus/firewall doing HTTPS inspection on these IT-managed laptops
- Fix: `--retries 10 --timeout 100`, see pygame section above

---

## Status summary

✅ **Confirmed working end-to-end (19 July 2026):**
- Full activation sequence (pixi shell → local_setup.bat → workspace cd → install\setup.bat)
- `ROS_DOMAIN_ID` via `setx`, persists across sessions
- `colcon build` — clean, no Developer Mode needed
- `pip install pygame opencv-python` (with `--retries`)
- Cross-machine discovery over the RPi hotspot — no firewall rule needed on either laptop tested
- Full pipeline: `laptop_controller` (Windows) ↔ `camera_feed_publisher` + `command_switcher` + `direction_to_serial` (RPi) — live video, mode requests, and CLAW commands all confirmed both directions

⚠️ **Not yet tested — verify before relying on it with students:**
- `ros2 pkg create` / building a brand-new package from scratch on Windows
- Whether "no firewall rule needed" holds on the remaining laptops
- Root cause of the doubled-command issue (workaround known, cause not fully confirmed)
