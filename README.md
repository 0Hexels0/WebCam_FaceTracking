
# WebCam_FaceTracking
Webcam Face Tracking project featuring pan-tilt movement that follows your face using OpenCV.



<img width="200" height="356" alt="face" src="https://github.com/user-attachments/assets/9e2bb505-77fb-4e5f-9a28-25349ae3b202" />  <img width="794" height="500" alt="image" src="https://github.com/user-attachments/assets/fc5b7017-1bd3-4176-bcbb-99829a577830" />


# 🎯 Yüz Takip Eden Pan-Tilt Lazer Taret (Raspberry Pi 4B)

Raspberry Pi 4B, USB webcam, PCA9685 servo sürücü kartı ve 2 eksenli
(pan-tilt) metal dişli servo kullanarak, gördüğü yüzü gerçek zamanlı
takip eden ve yüz merkeze geldiğinde lazer ile işaretleyen bir taret
projesi.

> ⚠️ Bu proje eğitim/hobi amaçlıdır. Lazer modülü olarak yalnızca düşük
> güçlü (5mW altı) göz için güvenli lazer modülleri kullanın ve projeyi
> her zaman gözetim altında test edin.

## Özellikler

- OpenCV Haar Cascade ile gerçek zamanlı yüz tespiti
- PCA9685 üzerinden I2C ile hassas, titremesiz servo kontrolü
- Yüz konumuna göre kademeli (P-kontrolcü mantığıyla) pan/tilt takibi —
  ani sıçrama yapmaz, webcam'in sabit olmadığı durumlarda da stabil çalışır
- Yüz görüntü merkezine yeterince yaklaşınca otomatik lazer tetikleme
- Webcam bağlantısı koparsa otomatik yeniden bağlanma

## Demo Mantığı

```
Kamera görüntüsü → Yüz tespiti → Merkeze göre ofset hesabı
        → Pan/Tilt servo düzeltmesi → Ofset yeterince küçükse lazer AÇIK
```

## 📦 Malzeme Listesi (BOM)

| # | Parça | Not |
|---|---|---|
| 1 | Raspberry Pi 4B | Herhangi bir RAM seçeneği yeterli |
| 2 | USB Webcam | Herhangi bir UVC uyumlu webcam |
| 3 | PCA9685 16 kanal servo sürücü kartı | I2C ile Pi'ye bağlanır |
| 4 | 2x Metal dişli servo (ör. MG90S / MG996R) | Pan ve tilt için |
| 5 | Pan-Tilt bracket kiti | 2 eksenli, kamera + lazer taşıyacak |
| 6 | Lazer diyot modülü (ör. KY-008) | **5mW altı**, göz güvenliği için |
| 7 | Harici 5V/6V güç kaynağı (2-3A+) | **Servolar için zorunlu**, Pi'den beslenmez |
| 8 | Breadboard + jumper kablolar | |
| 9 | microSD kart (Raspberry Pi OS kurulu) | |

## 🔌 Bağlantı Şeması

### Raspberry Pi ↔ PCA9685 (I2C)

| PCA9685 Pin | Raspberry Pi Pin |
|---|---|
| VCC (mantık) | Pi 3.3V (pin 1) |
| GND | Pi GND (pin 6) |
| SDA | Pi GPIO2 / SDA (pin 3) |
| SCL | Pi GPIO3 / SCL (pin 5) |

### PCA9685 ↔ Servolar / Güç

| Bağlantı | Nereye |
|---|---|
| Pan servo | PCA9685 kanal **0** |
| Tilt servo | PCA9685 kanal **1** |
| PCA9685 **V+** terminali | Harici 5V/6V güç kaynağı |
| PCA9685 GND (güç tarafı) | Harici kaynağın GND'si + Pi GND'si (**ortak toprak şart**) |

### Lazer

| Lazer Pin | Raspberry Pi Pin |
|---|---|
| Sinyal | GPIO22 (fiziksel pin 15) |
| VCC / GND | Pi 5V / GND |

> **Neden önemli:** Metal dişli servolar kalkışta yüksek akım çeker. Bu
> akım Pi'nin 5V pininden karşılanamaz ve Pi resetlenir/bozulabilir.
> Servoları PCA9685 üzerinden mutlaka **harici** bir güç kaynağıyla besleyin
> ve tüm GND hatlarını ortaklayın.

## 🛠️ Kurulum

### 1. Sistem paketleri

```bash
sudo apt update
sudo apt install -y python3-opencv python3-pip python3-rpi.gpio i2c-tools git
```

### 2. I2C'yi etkinleştir

```bash
sudo raspi-config
```
`Interface Options` → `I2C` → `Enable` → Pi'yi yeniden başlat.

Bağlantıyı doğrula:

```bash
i2cdetect -y 1
```

PCA9685 genelde **0x40** adresinde görünmelidir.

### 3. Repoyu klonla

```bash
git clone https://github.com/<kullanici-adiniz>/<repo-adi>.git
cd <repo-adi>
```

### 4. Python bağımlılıklarını kur

```bash
pip3 install -r requirements.txt
```

> Raspberry Pi OS'un yeni sürümlerinde (Bookworm) `pip3 install` komutu
> "externally managed environment" hatası verirse:
> ```bash
> pip3 install -r requirements.txt --break-system-packages
> ```
> ya da bir sanal ortam (`python3 -m venv venv`) kullanın.

### 5. Çalıştır

```bash
python3 src/face_tracking_turret.py
```

Çıkmak için görüntü penceresindeyken `q` tuşuna basın.

## ⚙️ Kütüphaneler

| Kütüphane | Amaç |
|---|---|
| `opencv-python` (veya `python3-opencv`) | Kameradan görüntü alma, yüz tespiti |
| `adafruit-circuitpython-servokit` | PCA9685'i I2C üzerinden derece cinsinden kontrol etmek için |
| `adafruit-blinka` | Adafruit CircuitPython kütüphanelerinin Raspberry Pi'de çalışmasını sağlayan uyumluluk katmanı |
| `RPi.GPIO` | Lazer modülünü doğrudan GPIO üzerinden sürmek için |

## 🔧 İnce Ayar

Kod içindeki (`src/face_tracking_turret.py`) şu parametrelerle oynayabilirsiniz:

| Değişken | Ne işe yarar |
|---|---|
| `DEADZONE_PX` | Yüz merkeze bu kadar piksel yakınsa hareket etmez (titremeyi önler) |
| `STEP_GAIN` | Piksel başına kaç derece dönüleceği (hassasiyet) |
| `MAX_STEP_DEG` | Tek karede maksimum açı değişimi (ani sıçramayı önler) |
| `LASER_TRIGGER_RADIUS` | Lazerin tetiklenmesi için yüzün merkeze ne kadar yakın olması gerektiği |
| `kit.servo[...].set_pulse_width_range(...)` | Servonuzun darbe genişliği aralığı standarttan farklıysa buradan ayarlayın |

## 🩺 Sorun Giderme

| Sorun | Çözüm |
|---|---|
| Servo uç noktalarda titriyor/gitmiyor | `set_pulse_width_range()` değerlerini servonuzun datasheet'ine göre ayarlayın |
| Servo ters yöne dönüyor | Kod içinde `PAN`/`TILT` bloklarındaki `+`/`-` işaretini değiştirin |
| `i2cdetect` PCA9685'i göstermiyor | I2C'nin etkin olduğundan ve kabloların doğru olduğundan emin olun |
| Pi, servo hareket edince resetleniyor | Servoları harici güçten beslediğinizden ve GND'lerin ortak olduğundan emin olun |
| Webcam bağlantısı kopuyor | Kod otomatik yeniden bağlanır; USB kablosunu/hub'ı kontrol edin |
| Yüz tespiti zayıf | Ortam ışığını artırın; gerekirse Haar Cascade yerine DNN tabanlı tespite geçin |

## 📁 Repo Yapısı

```
.
├── src/
│   └── face_tracking_turret.py   # Ana çalıştırılabilir kod
├── requirements.txt              # Python bağımlılıkları
├── LICENSE
└── README.md
```

## ⚠️ Güvenlik Notu

Bu proje insan yüzüne yönelen bir lazer barındırır. Yalnızca düşük güçlü
(5mW altı), göz için güvenli sınıfta (Class 1/2) lazer modülleri kullanın.
Projeyi asla gözetimsiz bırakmayın ve başkalarının doğrudan lazer ışığına
uzun süre bakmasına izin vermeyin.

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
