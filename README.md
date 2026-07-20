
# WebCam_FaceTracking
Webcam Face Tracking project featuring pan-tilt movement that follows your face using OpenCV.



<img width="200" height="356" alt="face" src="https://github.com/user-attachments/assets/9e2bb505-77fb-4e5f-9a28-25349ae3b202" />


# 🎯 Face-Tracking Pan-Tilt Laser Turret (Raspberry Pi 4B)

A turret project that uses a Raspberry Pi 4B, a USB webcam, a PCA9685
servo driver board, and a 2-axis (pan-tilt) metal-gear servo setup to
track a detected face in real time, and triggers a laser once the face
is centered.

> ⚠️ This project is for educational/hobby purposes. Only use a
> low-power (under 5mW) eye-safe laser module, and always test the
> project under supervision.

## Features

- Real-time face detection using OpenCV Haar Cascade
- Precise, jitter-free servo control over I2C via the PCA9685
- Incremental (proportional/P-controller style) pan/tilt tracking based
  on face position — no sudden jumps, and it stays stable even though
  the webcam isn't assumed to be fixed in place
- Automatic laser trigger once the face is close enough to the image center
- Automatic webcam reconnection if the connection drops

## How It Works

```
Camera frame → Face detection → Offset from center calculated
        → Pan/Tilt servo correction → Laser ON if offset is small enough
```

## 📦 Bill of Materials (BOM)

| # | Part | Notes |
|---|---|---|
| 1 | Raspberry Pi 4B | Any RAM variant works |
| 2 | USB Webcam | Any UVC-compatible webcam |
| 3 | PCA9685 16-channel servo driver board | Connects to the Pi via I2C |
| 4 | 2x Metal-gear servo (e.g. MG90S / MG996R) | For pan and tilt |
| 5 | Pan-Tilt bracket kit | 2-axis, holds the camera + laser |
| 6 | Laser diode module (e.g. KY-008) | **Under 5mW**, for eye safety |
| 7 | External 5V/6V power supply (2-3A+) | **Required for the servos**, don't power them from the Pi |
| 8 | LOGITECH C270 HD 720p WebCam | |
| 9 | Breadboard + jumper wires | |
| 10 | microSD card (with Raspberry Pi OS installed) | |

## 🔌 Wiring Diagram

### Raspberry Pi ↔ PCA9685 (I2C)

| PCA9685 Pin | Raspberry Pi Pin |
|---|---|
| VCC (logic) | Pi 3.3V (pin 1) |
| GND | Pi GND (pin 6) |
| SDA | Pi GPIO2 / SDA (pin 3) |
| SCL | Pi GPIO3 / SCL (pin 5) |

### PCA9685 ↔ Servos / Power

| Connection | To |
|---|---|
| Pan servo | PCA9685 channel **0** |
| Tilt servo | PCA9685 channel **1** |
| PCA9685 **V+** terminal | External 5V/6V power supply |
| PCA9685 GND (power side) | External supply GND + Pi GND (**common ground required**) |

### Laser

| Laser Pin | Raspberry Pi Pin |
|---|---|
| Signal | GPIO22 (physical pin 15) |
| VCC / GND | Pi 5V / GND |

<img width="600" height="320" alt="image" src="https://github.com/user-attachments/assets/0e1efb9f-91cd-43b6-b9c2-a05e3c5120a9" />


> **Why this matters:** Metal-gear servos draw significant current on
> startup. The Pi's 5V pin cannot supply this current, and doing so can
> reset or damage the Pi. Always power the servos through the PCA9685
> from an **external** power supply, and tie all GND lines together.

## 🛠️ Installation

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3-opencv python3-pip python3-rpi.gpio i2c-tools git
```

### 2. Enable I2C

```bash
sudo raspi-config
```
`Interface Options` → `I2C` → `Enable` → reboot the Pi.

Verify the connection:

```bash
i2cdetect -y 1
```

The PCA9685 should typically appear at address **0x40**.

### 3. Clone the repo

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 4. Install Python dependencies

```bash
pip3 install -r requirements.txt
```

> On newer Raspberry Pi OS versions (Bookworm), `pip3 install` may fail
> with an "externally managed environment" error. In that case, use:
> ```bash
> pip3 install -r requirements.txt --break-system-packages
> ```
> or set up a virtual environment (`python3 -m venv venv`).

### 5. Run it

```bash
python3 src/face_tracking_turret.py
```

Press `q` while the video window is focused to quit.

## ⚙️ Libraries

| Library | Purpose |
|---|---|
| `opencv-python` (or `python3-opencv`) | Capturing frames from the camera, face detection |
| `adafruit-circuitpython-servokit` | Controlling the PCA9685 over I2C using simple degree-based angles |
| `adafruit-blinka` | Compatibility layer that lets Adafruit CircuitPython libraries run on the Raspberry Pi |
| `RPi.GPIO` | Driving the laser module directly through a GPIO pin |

## 🔧 Tuning

You can tweak the following parameters in `src/face_tracking_turret.py`:

| Variable | What it does |
|---|---|
| `DEADZONE_PX` | If the face is within this many pixels of center, don't move (prevents jitter) |
| `STEP_GAIN` | Degrees of movement per pixel of offset (sensitivity) |
| `MAX_STEP_DEG` | Maximum angle change per frame (prevents sudden jumps) |
| `LASER_TRIGGER_RADIUS` | How close to center the face must be for the laser to trigger |
| `kit.servo[...].set_pulse_width_range(...)` | Adjust this if your servo's pulse-width range differs from the default |

## 🩺 Troubleshooting

| Issue | Fix |
|---|---|
| Servo jitters or won't reach the end of its range | Adjust `set_pulse_width_range()` values to match your servo's datasheet |
| Servo moves in the wrong direction | Flip the `+`/`-` sign in the `PAN`/`TILT` blocks in the code |
| `i2cdetect` doesn't show the PCA9685 | Make sure I2C is enabled and the wiring is correct |
| Pi resets when the servos move | Make sure the servos are powered externally and all GNDs are common |
| Webcam connection keeps dropping | The code will auto-reconnect; check your USB cable/hub |
| Poor face detection | Improve lighting, or switch from Haar Cascade to a DNN-based detector |

## 📁 Repo Structure

```
.
├── src/
│   └── face_tracking_turret.py   # Main executable script
├── requirements.txt              # Python dependencies
├── LICENSE
└── README.md
```

## ⚠️ Safety Note

This project includes a laser aimed at a human face. Only use a
low-power (under 5mW), eye-safe class (Class 1/2) laser module. Never
leave the project unattended, and don't let anyone stare directly into
the laser for an extended period.

## License

This project is licensed under the [MIT License](LICENSE).
