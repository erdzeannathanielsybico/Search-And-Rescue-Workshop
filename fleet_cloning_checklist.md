# Fleet Cloning Checklist

Cloning the source RPi's SD card is the fastest way to get identical ROS2 + Ubuntu + workspace setups onto the other team robots, instead of doing a full manual install on each one. This doc covers what hardware you need, how to make the clone, and — critically — the handful of things cloning duplicates that must be made unique per robot afterward.

## Hardware needed
Just **one USB SD card reader/adapter** — no second physical Pi required.

## Cloning steps (image once, flash N times)
Actual method used (Windows):
1. Shut down the source Pi cleanly, pull its SD card, put it in a USB card reader on a Windows PC.
2. **Win32DiskImager** → "Read" → save the card to a `.img` file (this is the reusable master image).
3. **Raspberry Pi Imager** → "Choose OS" → "Use custom" → select that `.img` → write it to each new SD card, one at a time.
4. Boot each new Pi and run through the checklist below.

The `.img` file doesn't get consumed or modified by writing it — keep it around and reuse it for every future card without re-imaging the source Pi again, as long as nothing on the source changes that you want reflected in future clones.

(Linux/Mac alternative: `dd` for imaging/flashing, or `rpi-clone` for a direct Pi-to-Pi clone with no separate computer needed.)

## Per-robot checklist (run once per new clone)
This board runs Ubuntu Desktop, not Raspberry Pi OS, so `raspi-config` isn't available — commands below are the Ubuntu equivalents.

1. **Hostname**
   ```bash
   sudo hostnamectl set-hostname sar-N
   sudo nano /etc/hosts   # update the 127.0.1.1 line to match
   ```
   The terminal prompt won't update until you open a new terminal or reboot — the change takes effect immediately, the already-open shell just doesn't refresh its prompt string. Confirm with `hostname` in the current session, or just reboot to be sure everything picks it up.

2. **Account password** *(optional)* — unlike the other items here, an identical password across all robots causes no technical conflict, only a "don't reuse passwords" security tradeoff that isn't worth worrying about for a workshop fleet with no internet exposure. Fine to leave every robot on the same password (`fablabuae`). Run `passwd` only if you actually want it to differ per robot.

3. **GNOME keyrings** — changing the account password with `passwd` does **not** automatically resync the GNOME keyrings, so saved secrets end up locked under the old password. Two separate keyrings are involved (Login, and Default — which holds Chrome/VSCode/RDP saved secrets), so don't try to fix this by editing individual saved items. On a clone, the clean fix is to wipe both and let them regenerate fresh against the new password:
   ```bash
   rm -rf ~/.local/share/keyrings/*
   ```
   Reboot — you'll be prompted to set a keyring password on next login, and any saved WiFi/Chrome/RDP secrets will need re-entering once, which is expected on a "new" robot image anyway.

4. **Hotspot SSID/password** — the always-on hotspot here is just a NetworkManager connection profile with `autoconnect` enabled (all other saved WiFi profiles have it disabled) — there's no separate `hostapd.conf`. Editing the SSID/password on that connection via GNOME Wi-Fi settings ("Turn On Wi-Fi Hotspot") *is* what changes what auto-starts on boot. Open that dialog and set:
   - **Network Name:** `SAR_<team-number>`
   - **Password:** `SAR_<team-number>_hotspot`

   e.g. team 1's robot gets SSID `SAR_1`, password `SAR_1_hotspot`.

5. **`ROS_DOMAIN_ID`** — only relevant if robots ever share one network (README networking tier 2, marked hit-or-miss); not needed if using tier-1 isolated per-robot hotspots, which is what's recommended. If used, it must be set directly on the systemd service (`Environment=ROS_DOMAIN_ID=<n>` in the unit file) — `.bashrc`-only exports are invisible to systemd-launched nodes (see Known Issues in `README.md`).

6. **Claude Code credentials** — `~/.claude/` on the source Pi holds personal auth/session state. Clear or re-auth this on each clone rather than leaving one account logged in on every machine.

7. **Static IP config**, if any is hardcoded in netplan rather than DHCP — check for hardcoded addresses that would collide across clones.

Everything else — ROS2 install, workspace, systemd bringup service, dependencies — carries over exactly as-is, which is the point of cloning.

## Verification
- Boot one cloned card standalone first, run through the full checklist on it, confirm hostname/keyring/hotspot are correctly de-duplicated and the ROS2 boot service still comes up automatically.
- Only then flash and configure the remaining cards from the same master image.
