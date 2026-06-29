Here's your summary:

---

**Setting up RPi 5 from scratch — what you did**

**1. Flashed the SD card (on laptop)**
- Downloaded Raspberry Pi Imager
- Selected device: Raspberry Pi 5
- Selected OS: Ubuntu Desktop 24.04.4 LTS (64-bit)
- Selected your SD card as storage
- Flashed it

**2. First boot (on RPi with monitor)**
- Inserted SD card into RPi 5
- Connected micro-HDMI monitor, keyboard, power
- Completed Ubuntu setup wizard (language, timezone, username, password, Wi-Fi)

**3. Set up SSH (on RPi terminal)**
```bash
sudo apt update
sudo apt install openssh-server -y
sudo systemctl start ssh
sudo systemctl enable ssh
```

**4. Got the RPi's IP address**
```bash
hostname -I
# Result: 192.168.1.82
```

**5. Connected from laptop**
```bash
ssh nathaniel@192.168.1.82
```

---

I've also saved your RPi details to memory so I can reference them in future chats. Ready to install ROS 2 next?


