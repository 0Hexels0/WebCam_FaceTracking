#!/usr/bin/env python3
"""
Raspberry Pi 4B - Yuz Takip Eden Pan-Tilt Lazer Taret (PCA9685 versiyonu)
==========================================================================

Donanim:
  - USB Webcam
  - PCA9685 servo surucu karti (I2C: SDA -> GPIO2/pin3, SCL -> GPIO3/pin5)
  - Pan  servo  -> PCA9685 kanal 0
  - Tilt servo  -> PCA9685 kanal 1
  - Lazer       -> Pi GPIO22 (dogrudan, PCA9685'e gerek yok)
  - Metal disli servolar + PCA9685, HARICI 5V/6V guc kaynagindan beslenmeli
    (PCA9685 uzerindeki V+ terminaline). Pi'nin 5V pininden DEGIL.
  - PCA9685'in GND'si, harici gucun GND'si ve Pi'nin GND'si ORTAK olmali.

Gereksinimler:
  sudo raspi-config  ->  Interface Options -> I2C -> Enable  (SDA/SCL'i acar)
  sudo apt update
  sudo apt install -y python3-opencv python3-pip i2c-tools python3-rpi.gpio
  pip3 install adafruit-circuitpython-servokit adafruit-blinka

Baglanti dogrulama:
  i2cdetect -y 1
  -> PCA9685 genelde 0x40 adresinde gorunmeli

Not: Webcam sabit degildir (elde/masada oynayabilir), bu yuzden kod
mutlak pozisyon hesabi yapmaz; her karede mevcut servo acisindan
itibaren, yuzun goruntu merkezine olan ofsetine gore KUCUK ADIMLARLA
duzeltme yapar (basit bir P-kontrolcu mantigi).
"""

import cv2
import time
import RPi.GPIO as GPIO
from adafruit_servokit import ServoKit

# ------------------------------------------------------------------
# AYARLAR
# ------------------------------------------------------------------
PAN_CHANNEL  = 0        # PCA9685 uzerindeki pan servo kanali
TILT_CHANNEL = 1        # PCA9685 uzerindeki tilt servo kanali
LASER_GPIO   = 22       # Lazer dogrudan Pi GPIO'sundan suruluyor

CAM_INDEX = 0           # webcam birden fazlaysa 0,1,2... deneyin
FRAME_W   = 640
FRAME_H   = 480

# Metal disli servolarin (MG90S/MG996R vb.) genelde 0-180 derece araligi
# vardir. Bazi metal servolar 0-270 olabilir; ona gore SERVO_MAX_ANGLE'i
# degistirin.
SERVO_MIN_ANGLE = 0
SERVO_MAX_ANGLE = 180
SERVO_MID_ANGLE = 90

# Baslangic pozisyonu -> merkez (bakis kameraya dik)
pan_angle  = SERVO_MID_ANGLE
tilt_angle = SERVO_MID_ANGLE

# Takip hassasiyeti / hiz ayarlari
DEADZONE_PX  = 25     # yuz merkeze bu kadar piksel yakinsa hareket etme (titremeyi onler)
STEP_GAIN    = 0.030  # ofset piksel basina kac DERECE hareket edilecek -> hassasiyet
MAX_STEP_DEG = 3.0    # tek karede maksimum aci degisimi (ani sicramayi onler)

# Lazer, yuz merkeze bu kadar yakinsa yansin (piksel)
LASER_TRIGGER_RADIUS = 60

# ------------------------------------------------------------------
# PCA9685 BASLATMA (I2C uzerinden - Pi'nin SDA/SCL pinlerini kullanir,
# ekstra GPIO tanimlamaya gerek yok, kutuphane otomatik /dev/i2c-1'i bulur)
# ------------------------------------------------------------------
kit = ServoKit(channels=16)

# Metal servolarin darbe genisligi araligi genelde standart SG90'dan
# farklidir (ornegin 500-2500us yerine 600-2400us gibi). Servonuz
# ucun uctan (0/180 derece) titriyor ya da gitmiyor ise bu degerleri
# servonuzun datasheet'ine gore ayarlayin:
kit.servo[PAN_CHANNEL].set_pulse_width_range(500, 2500)
kit.servo[TILT_CHANNEL].set_pulse_width_range(500, 2500)

def set_servo(channel, angle):
    angle = max(SERVO_MIN_ANGLE, min(SERVO_MAX_ANGLE, angle))
    kit.servo[channel].angle = angle
    return angle

# ------------------------------------------------------------------
# LAZER (dogrudan GPIO, PCA9685 disinda)
# ------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(LASER_GPIO, GPIO.OUT)

def laser(on: bool):
    GPIO.output(LASER_GPIO, GPIO.HIGH if on else GPIO.LOW)

# Baslangicta servolari merkeze al, lazeri kapat
pan_angle  = set_servo(PAN_CHANNEL, pan_angle)
tilt_angle = set_servo(TILT_CHANNEL, tilt_angle)
laser(False)
time.sleep(0.5)

# ------------------------------------------------------------------
# YUZ TESPIT (Haar Cascade - Pi 4B'de hizli calisir)
# ------------------------------------------------------------------
face_cascade = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml")

# ------------------------------------------------------------------
# KAMERA BASLATMA (webcam sabit degil / bazen kopabilir -> yeniden
# baglanma mantigi ekliyoruz)
# ------------------------------------------------------------------
def open_camera():
    cap = cv2.VideoCapture(CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    return cap

cap = open_camera()

frame_center_x = FRAME_W // 2
frame_center_y = FRAME_H // 2

print("Baslatildi. Cikmak icin 'q' tusuna basin.")

try:
    while True:
        if not cap.isOpened():
            print("Kamera bagli degil, yeniden deneniyor...")
            time.sleep(1)
            cap = open_camera()
            continue

        ret, frame = cap.read()

        # Webcam bazen tek kare cikaramayabilir (baglanti/USB hatasi) -
        # bu durumda kilitlenmeden devam et
        if not ret or frame is None:
            print("Kare okunamadi, yeniden deneniyor...")
            cap.release()
            time.sleep(0.5)
            cap = open_camera()
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=6, minSize=(60, 60)
        )

        face_found = False

        if len(faces) > 0:
            # En buyuk yuzu (kameraya en yakin/en belirgin) sec
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces[0]
            face_cx = x + w // 2
            face_cy = y + h // 2
            face_found = True

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (face_cx, face_cy), 4, (0, 0, 255), -1)

            offset_x = face_cx - frame_center_x   # + ise yuz saga kaymis
            offset_y = face_cy - frame_center_y   # + ise yuz asagi kaymis

            # --- PAN (sol/sag) ---
            if abs(offset_x) > DEADZONE_PX:
                step = offset_x * STEP_GAIN
                step = max(-MAX_STEP_DEG, min(MAX_STEP_DEG, step))
                # Yuz saga kaydiysa (offset_x > 0) kamera saga donmeli.
                # Servo yonu montaja gore ters olabilir; ters calisirsa
                # asagidaki "+" isaretini "-" ile degistirin.
                pan_angle = set_servo(PAN_CHANNEL, pan_angle - step)

            # --- TILT (yukari/asagi) ---
            if abs(offset_y) > DEADZONE_PX:
                step = offset_y * STEP_GAIN
                step = max(-MAX_STEP_DEG, min(MAX_STEP_DEG, step))
                # Yuz asagi kaydiysa kamera asagi bakmali.
                # Servo yonu montaja gore ters olabilir; ters calisirsa
                # "-" yerine "+" kullanin.
                tilt_angle = set_servo(TILT_CHANNEL, tilt_angle + step)

            # --- LAZER ---
            distance = (offset_x ** 2 + offset_y ** 2) ** 0.5
            if distance < LASER_TRIGGER_RADIUS:
                laser(True)
            else:
                laser(False)

        if not face_found:
            laser(False)

        cv2.line(frame, (frame_center_x, 0), (frame_center_x, FRAME_H), (255, 0, 0), 1)
        cv2.line(frame, (0, frame_center_y), (FRAME_W, frame_center_y), (255, 0, 0), 1)

        cv2.imshow("Yuz Takip Tareti (PCA9685)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    pass

finally:
    print("Kapatiliyor, servolar merkeze aliniyor ve lazer kapatiliyor...")
    laser(False)
    try:
        set_servo(PAN_CHANNEL, SERVO_MID_ANGLE)
        set_servo(TILT_CHANNEL, SERVO_MID_ANGLE)
        time.sleep(0.3)
        # PWM sinyalini kesmek icin kanali None'a ayarla (servo gevser)
        kit.servo[PAN_CHANNEL].angle = None
        kit.servo[TILT_CHANNEL].angle = None
    except Exception:
        pass
    GPIO.cleanup()
    cap.release()
    cv2.destroyAllWindows()
