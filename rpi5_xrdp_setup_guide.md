# RPi 5 Remote Desktop via xrdp — Working Setup Guide

**Date confirmed working:** 19 July 2026 (sar-1)
**RPi OS:** Ubuntu Desktop 24.04.4 LTS
**Connection app (Windows):** Remote Desktop Connection (mstsc) — unchanged
**Hotspot IP (all robots):** `10.42.0.1` (NetworkManager hotspot default — same on every clone)

> ⚠️ **This supersedes `rpi5_rdp_setup_log.md`.** GNOME's built-in Remote Login (gnome-remote-desktop) was abandoned after it connected but delivered only a black screen with a mouse cursor — a known, widely reported bug on Ubuntu 24.04, not a configuration mistake. xrdp is the replacement and worked first try once installed correctly.

---

## Why the switch

- GNOME Remote Login on 24.04 accepted RDP connections (blue connection bar appeared, no errors) but hung forever on a black screen at the session-handover step. Logs showed `Aborting handover, removing remote client`.
- This happened with correct credentials, with the console logged out, over the hotspot — every variable was eliminated. It is a software bug in gnome-remote-desktop on this Ubuntu version.
- xrdp is the standard, battle-tested Linux RDP server. Same `mstsc` workflow on the Windows side; nothing changes for the person connecting.

---

## One-time setup per RPi (add to the clone checklist)

xrdp needs internet to install, and the hotspot provides none (the Pi *is* the network, it isn't *on* one). So the install involves a temporary WiFi swap.

**1. Connect the RPi to a real WiFi network** (venue WiFi, not its own hotspot). Do this from the console (monitor + keyboard) — easier than juggling nmcli over an SSH session that will drop mid-switch.

**2. Fix the clock first if it's been set manually.** apt refuses repo files that appear to be "from the future", failing with `Release file ... is not valid yet (invalid for another XXmin)`. With internet now available, let NTP handle it:

```bash
sudo timedatectl set-ntp true
# wait ~30 seconds, then confirm "System clock synchronized: yes"
timedatectl
```

**3. Install xrdp and swap the services:**

```bash
sudo apt update
sudo apt install xrdp -y
sudo systemctl disable --now gnome-remote-desktop.service
sudo systemctl enable --now xrdp
```

- `disable --now gnome-remote-desktop` stops the broken GNOME service and frees port 3389 so the two never fight over it.
- `enable --now xrdp` starts xrdp immediately *and* makes it auto-start on every boot.

**4. Switch WiFi back to hotspot mode** (top-right menu → WiFi → Turn On Wi-Fi Hotspot).

**5. Log out on the console.** Leave the RPi at the login screen.

---

## Connecting from Windows (every time)

1. Connect the laptop to the robot's hotspot WiFi.
2. `Win + R` → `mstsc` → Enter.
3. Computer: `10.42.0.1`
4. Connect → the **xrdp login page** appears (distinct look — has a "Session" dropdown; leave it on Xorg).
5. Username: `nathaniel` — Password: the **Linux account password** (standard: `fablabuae`).
6. Desktop loads. It may look slightly plainer than the console session (some GNOME effects disabled under xrdp) — normal, nothing is broken.

> **Credential note:** xrdp authenticates against the **Linux account password** directly. The separate `grdctl` RDP credential from the GNOME setup is no longer involved. One password, the Linux one.

---

## The one rule that matters

**Console logged out = RDP works. Console logged in = RDP instantly closes.**

xrdp cannot open a session for a user who is already logged in on the physical monitor. The symptom is unmistakable: the mstsc window opens and closes again within a second or two, no error shown. If that happens, walk to the robot, log out on the monitor, retry.

On competition day this is a non-issue — the robots run headless (no monitor), so nobody is ever logged in on the console. It only bites during bench testing with a monitor attached.

---

## Troubleshooting reference (all hit and solved on 19 July 2026)

| Symptom | Cause | Fix |
|---|---|---|
| mstsc window opens then closes within seconds, no login page | Same user logged in on the RPi's physical console | Log out on the monitor, leave at login screen, retry |
| `apt install xrdp` fails: `Temporary failure resolving 'ports.ubuntu.com'` | RPi is in hotspot mode — no internet | Swap to venue WiFi for the install, swap back after |
| `apt update` fails: `Release file ... is not valid yet (invalid for another XXmin)` | Pi's clock is behind real time (manually-set clock drift; hotspot has no NTP) | `sudo timedatectl set-ntp true` while on a network with internet |
| Connects but black screen forever, mouse cursor only | That's the GNOME Remote Login bug — it's still answering port 3389 | Confirm `gnome-remote-desktop` is disabled and `xrdp` is active: `sudo systemctl status xrdp` |
| Login page appears but session drops right after entering password | Wrong password (xrdp wants the **Linux** password), or console still logged in | Use the Linux account password; check the monitor |

---

## Additions to the per-clone checklist

Add these to the existing post-clone steps (hostname, ROS_DOMAIN_ID, SSH host keys):

- [ ] Install xrdp + disable gnome-remote-desktop + enable xrdp (steps above — needs the temporary venue-WiFi swap)
- [ ] Confirm the Linux password for `nathaniel` is the standard one (`passwd nathaniel` if it diverged)
- [ ] **Settings → Power → Automatic Suspend → Off** — sar-1 was still auto-suspending despite this supposedly being disabled on the source image; verify on every clone. A robot that sleeps mid-mission is a showstopper.
- [ ] Verify end-to-end: hotspot on, console logged out, mstsc from a laptop to `10.42.0.1`, desktop loads
- [ ] *(Better long-term: bake xrdp into the master image before the next cloning pass so this whole section happens once, not per-unit)*

---

## Known open issues (not yet solved)

- **Camera not visible / ROS nodes not starting inside the xrdp session** — observed on sar-1 immediately after first successful xrdp login; not yet investigated. First things to check next session: does `/dev/video0` exist (`ls /dev/video*`)? Does `camera_feed_publisher` give a specific error when run from an xrdp terminal? Is the workspace sourced in that terminal (`source install/setup.bash` from the workspace root)? Note the xrdp session is a fresh login — `.bashrc` sourcing applies, but any manually-exported variables from console sessions do not carry over.
