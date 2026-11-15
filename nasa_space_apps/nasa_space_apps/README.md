# LUNA-AI: Ay İniş Alanı Navigatörü (Mons Mouton / VIPER)

NASA Space Apps Challenge 2026 kapsamında geliştirilen; Ay Güney Kutbu (Mons Mouton / VIPER bölgesi) için çok kriterli iniş noktası puanlama, gölge/aydınlanma analizi, Dünya görüş hattı kontrolü ve iniş sonrası A* rota + batarya simülasyonu sunan uçuş mekaniği ve görev analizi motorudur.

## Klasör Yapısı

```text
nasa_space_apps/
├── ay_api.py           # Arayüz (UI) entegrasyonu için tek giriş noktası (JSON + PNG üretir)
├── ay_navigator.py     # Temel fizik, DEM, SPICE güneş/Dünya, A* rota ve enerji simülasyon motoru
├── requirements.txt    # Gerekli Python kütüphaneleri
├── .gitignore          # Önbellek ve geçici çıktı klasörleri filtresi
└── README.md           # Kurulum ve arayüz entegrasyon dokümanı
```

## Kurulum

Python 3.10+ (64-bit) ortamında gerekli kütüphaneleri kurun:

```bash
pip install -r requirements.txt
```

## Arayüz (UI) Entegrasyonu

Arayüz kodu, aynı dizinde veya Python yolunda bulunan `ay_api` modülünü doğrudan içe aktararak tek fonksiyon çağrısıyla tüm analiz sonuçlarını (JSON uyumlu `dict` ve harita görselleri) alabilir:

```python
from ay_api import analiz

# Gerçek NASA LOLA DEM + JPL SPICE verileriyle analiz:
sonuc = analiz("2026-11-27T00:00:00Z", cikti="cikti_arayuz")

# İnternetsiz hızlı arayüz testi (sentetik krater demosu):
# sonuc = analiz("2026-11-27T00:00:00Z", sentetik=True, cikti="cikti_arayuz")

print("En verimli #1 nokta:", sonuc["en_verimli"][0])
print("En riskli #1 nokta:", sonuc["en_riskli"][0])
print("Genel harita yolu:", sonuc["genel_harita_png"])
```

### Çıktı Yapısı (`sonuc` / `cikti_arayuz/arayuz_sonuc.json`)

- `en_verimli`: Kriter ağırlıklarına göre en yüksek puanlı 2 ayrık iniş noktası (`V1`, `V2`), koordinatları, kriter kırılımları ve PNG harita yolları.
- `en_riskli`: En yüksek riskli 2 ayrık nokta (`R1`, `R2`).
- `gorev_ozetleri`: Seçilen en verimli noktalardan en yakın ulaşılabilir karanlık hedefe (PSR adayı) git-dön rota ve batarya SOC simülasyonu.
- `rover_bilgi`: VIPER referans araç parametreleri ve gölgede dayanma/menzil değerleri.
- `ortam`: Seçilen UTC anı için Güneş ve Dünya yükseklik/azimut açıları ile Dünya-Ay mesafesi.
- `genel_harita_png`: Seçilen noktaları gösteren genel bölge haritası.

## Komut Satırı Kullanımı

```bash
# Çevrimdışı birim testleri
python ay_api.py --test

# İnternetsiz demo çalıştırma
python ay_api.py --sentetik

# Belirli bir tarih için gerçek NASA verisiyle analiz
python ay_api.py --tarih 2026-11-27T00:00:00Z
```
