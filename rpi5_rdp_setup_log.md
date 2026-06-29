# RPi 5 Remote Desktop (RDP) Setup Log

**Date completed:** June 2026  
**RPi OS:** Ubuntu Desktop 24.04.4 LTS  
**RPi IP:** 192.168.1.82  
**Connection app (Windows):** Remote Desktop Connection (mstsc)

---

## What Was Set Up

Full GUI remote desktop access from a Windows PC to the Raspberry Pi 5, using RDP (Remote Desktop Protocol) built into Ubuntu 24.04's GNOME desktop.

---

## Steps Done on the RPi (one-time setup)

1. Opened **Settings** (Super key → search "Settings")
2. Went to **System → Remote Desktop**
3. Clicked **Unlock** and entered the system password
4. Enabled **Remote Login** → toggled ON
5. Selected **RDP** as the protocol
6. Set credentials:
   - Username: `nathaniel`
   - Password: `nathaniel`
7. Noted the port: **3389**

> ⚠️ **Desktop Sharing was left OFF** — that's correct. Desktop Sharing mirrors the physical screen; Remote Login creates a fresh independent session which is what we want.

---

## Steps to Connect from Windows (every time)

1. Press `Win + R` → type `mstsc` → hit Enter
2. In the **Computer** field enter: `192.168.1.82:3389`
3. Enter username: `nathaniel`
4. Enter password: `nathaniel`
5. Accept the certificate warning (self-signed, safe on local network) → click **Yes**
6. GNOME desktop loads in the window ✅

---

## Notes

- The certificate warning ("identity cannot be verified") is **normal** — it's self-signed, not from a certificate authority. Safe to accept on a local network.
- If the RPi's IP changes (e.g. router reboot), you may need to find the new IP via `hostname -I` in terminal or check your router's device list.
- This is purely for local network use — not accessible from outside your home network without extra configuration.
- SSH (PowerShell) still works alongside this for terminal-only tasks: `ssh nathaniel@192.168.1.82`
