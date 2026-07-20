# ROS 2 Jazzy — Native Windows Install (via pixi)

**Why this exists:** bypasses WSL2 entirely. Windows 10 can't do WSL2 mirrored networking (Windows 11 22H2+ only), which was blocking direct ROS 2 communication between laptop and RPi — this was forcing you into RDP as a workaround. This path skips that problem completely: ROS 2 runs natively on Windows, same LAN/hotspot as the RPi.

✅ Confirmed working — talker/listener demo tested successfully across the RPi hotspot, 19 July 2026.

---

## Step 1 — Create a workspace folder

In PowerShell:
```
mkdir C:\pixi_ws
cd C:\pixi_ws
```
Keep the path short — Windows has path-length limits.

## Step 2 — Install conda-forge

ROS 2 uses conda-forge as a backend for packages, with pixi as the frontend — conda-forge needs to be installed first.

Go to https://conda-forge.org/download/, download the **Windows** installer, and run it.

> **Note:** the conda-forge installer may trigger Windows Defender to flag it as a threat. This can be safely ignored — click "More info" then "Run anyway."

## Step 3 — Install pixi

In PowerShell, as of 20 July 2026 the install command is:
```powershell
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```
If this stops working on a future laptop, check https://pixi.sh/latest/ for the current one-liner.

Close and reopen PowerShell afterwards so `pixi` is on your PATH.

## Step 4 — Download the pixi config file

Still in PowerShell:
```
cd C:\pixi_ws
irm https://raw.githubusercontent.com/ros2/ros2/refs/heads/jazzy/pixi.toml -OutFile pixi.toml
```

## Step 5 — Install dependencies

```
pixi install
```

## Step 6 — Download the ROS 2 Windows binary

- Go to https://github.com/ros2/ros2/releases
- **Pick "ROS 2 Jazzy Jalisco - Patch Release 7" specifically** (released 28 Jan 2026) — later patches dropped the Windows binary because Windows 10 (the only supported Windows version for Jazzy) hit end-of-life
- Download `ros2-jazzy-20260128-windows-release-amd64.zip`

## Step 7 — Unpack

Unzip the contents into `C:\pixi_ws\ros2-windows`

## Step 8 — Activate the environment (every new session)

⚠️ **Must be Command Prompt (`cmd`), not PowerShell** — `call` doesn't exist in PowerShell and will error out.

```
cd C:\pixi_ws
pixi shell
call C:\pixi_ws\ros2-windows\local_setup.bat
```

## Step 9 — Test it

```
ros2 run demo_nodes_cpp talker
```
In a **second** Command Prompt window (repeat Step 8 first):
```
ros2 run demo_nodes_py listener
```

## Step 10 — Set ROS_DOMAIN_ID to match the RPi fleet

This window only:
```
set ROS_DOMAIN_ID=42
```
Permanent, for all new windows going forward:
```
setx ROS_DOMAIN_ID 42
```
(Only applies to windows opened *after* running this — restart Command Prompt to pick it up.)

## Step 11 — Join the robot's network

- Laptop WiFi must connect to the **RPi's own hotspot**, not venue/home WiFi — needs to be the same subnet
- Confirm with `ipconfig` — should show an address like `10.42.0.x`
- Sanity check: `ping 10.42.0.1`
- Note: no internet while on the hotspot — the RPi *is* the network, expected behaviour

## Optional — Firewall rule (fallback only)

Not needed on the first laptop tested — Windows appears to treat the hotspot as a Private network profile and doesn't block DDS discovery by default. Keep this in your back pocket in case an IT-managed/domain-joined laptop behaves differently. Run in an **elevated (Admin) PowerShell**:
```powershell
New-NetFirewallRule -DisplayName "Allow ROS2 DDS (domain 42)" -Protocol UDP -LocalPort 17900-17930 -Direction Inbound -Action Allow
```

## Known risks

- Some users report Python path / "failed to create process" errors with this Windows binary (GitHub ros2/ros2 issue #1675) — hasn't hit yet on the tested laptop, but worth testing on each machine early, not on workshop day
- Untested whether other/IT-managed laptops need the firewall rule above
