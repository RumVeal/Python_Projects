# Python_Projects

Personal projects written in Python.

| Project | Description |
|---|---|
| [ArduinoDrone](ArduinoDrone) | Kivy app for controlling an Arduino drone via Bluetooth *(in progress)* |
| [VKGameBot](VKGameBot) | Game bot for VK group chats: roulette, rock-paper-scissors, blackjack, points and levels |

## 🚁 ArduinoDrone — mobile controller for an Arduino drone

A Kivy app that controls a homemade Arduino-based drone over Bluetooth (HC-05 module).
Runs on Android (built with Buildozer) and on desktop for UI testing.

> **Status: work in progress.** The app runs and sends commands; the drone hardware is being rebuilt from scratch.

### Features
- Movement controls: up/down, forward/backward, left/right, yaw
- ON/OFF switch
- PID input field (saved between launches)
- Live terminal that shows data coming back from the Arduino
- Bluetooth: Android SPP (pyjnius) and serial port on desktop (pyserial), reading in a background thread

### Command protocol
Each command is sent as a single character followed by `\n` at 9600 baud.

| Command | Action      |
|---------|-------------|
| `Q`     | Up          |
| `E`     | Down        |
| `W`     | Forward     |
| `S`     | Backward    |
| `A`     | Left        |
| `D`     | Right       |
| `L`     | Yaw left    |
| `R`     | Yaw right   |

### Run on desktop
```bash
cd ArduinoDrone
python3 -m venv venv
source venv/bin/activate
pip install kivy pyserial
python main.py
```
Pair the HC-05 first and check the port name with `ls /dev/cu.*` (default in code: `/dev/cu.HC-05`).

### Build for Android
```bash
cd ArduinoDrone
buildozer android debug                 # APK appears in bin/
buildozer android deploy run logcat     # install and run on a connected phone
```
Pair the HC-05 in the phone's Bluetooth settings before launching. The module's MAC address is set in `main.py`.

### Tech stack
Python · Kivy · Buildozer · pyjnius · pyserial · Arduino · HC-05

### Roadmap
- [ ] Rebuild the drone hardware
- [ ] Add the Arduino sketch to the repo
- [ ] Send the ON/OFF state and PID values to the Arduino
- [ ] Bluetooth device picker instead of a hardcoded MAC address
- [ ] Telemetry display (battery, altitude)
