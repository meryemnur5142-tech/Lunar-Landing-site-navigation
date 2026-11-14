# status: draft
# owner: Agent D
# depends_on:
#   - docs/architecture/SAFETY_STATE_MACHINE.md
#   - docs/qar/QAR_TABLE.md
#   - domain/mission/constraints/hard_constraints_catalog.yaml
#   - autonomy/autonomy_matrix.md
#   - autonomy/mission_planner.md
# open_items:
#   - TBD-FDIR-001: IMU/VO çapraz kontrol tutarsızlık eşiği (σ_imu_vo_diff)
#   - TBD-FDIR-002: Tekerlek encoder vs komut sapma eşiği (motor sıkışma tespiti)
#   - TBD-FDIR-003: Batarya SoC sapma anomali eşiği
#   - TBD-FDIR-004: Hücre dengesizlik eşiği (mV fark)
#   - TBD-FDIR-005: FDIR ana döngü frekansı (Hz); donanım bağımlı
#   - TBD-FDIR-006: İletişim kaybı link_timeout eşiği (s); TBD-COM-002 ile örtüşür
#   - TBD-FDIR-007: Lokalizasyon kaybı pozisyon belirsizlik eşiği (m)
#   - TBD-FDIR-008: Lokalizasyon recovery bekleme süresi (s)

# FDIR Implementasyon Detayı — LUNA-AI

**Belge ID:** LUNA-AI-SAF-D2-001
**Versiyon:** 0.1-draft
**Tarih:** 2026-11-14
**Sahip:** Agent D

---

## Mimari Notu: Planlayıcı ≠ Güvenlik (Uyum Notu 1)

FDIR, görev yürütme kararlarını Mission Planner'a bırakır. Güvenlik kararları FDIR'ın münhasır yetkisindedir. İki modül arasında bellek bölgesi paylaşılmaz; iletişim yalnızca ICD-004 üzerinden gerçekleşir (bkz. `docs/architecture/SAFETY_STATE_MACHINE.md` §4).

---

## 1. Sensör Tutarsızlığı

### 1.1 Detection

LUNA-AI üç bağımsız lokalizasyon kaynağından konumunu hesaplar: IMU (atalet ölçüm birimi), görsel odometri (VO) ve tekerlek odometrisi. Tutarsızlık tespiti çapraz kontrol ile yapılır:

**IMU vs Görsel Odometri Çapraz Kontrolü:**
- IMU yüksek frekanslı konum tahmini üretir (integral yoluyla); VO her kare için bağımsız konum farkı üretir.
- Her VO güncellemesinde IMU dead-reckoning tahmini ile VO tahmini karşılaştırılır.
- Fark `σ_imu_vo_diff` eşiğini (TBD-FDIR-001) aşarsa tutarsızlık alarmı tetiklenir.

**Tekerlek Odometrisi Çapraz Kontrolü:**
- Tekerlek odometrisi kaymaya duyarlıdır; PSR kumlu zemininde kayma artabilir.
- IMU ile tekerlek odometrisi arasındaki çizgisel hız farkı izlenir.
- Fark `σ_wheel_imu_diff` eşiğini 3 ardışık ölçümde aşarsa kayma tespiti yapılır.

**Çoklu Sensör Oy Mekanizması:**
- Üç kaynaktan ikisi tutarlıysa: tutarsız olan kaynak güvenilmez ilan edilir.
- Üç kaynak birbirinden farklıysa: lokalizasyon kaybı senaryosuna geçilir (§5).

Tespit süresi: QAR-FDIR-001'e göre < 50 ms (P95).

### 1.2 Isolation

| Durum | Güvenilmez İlan Edilen Sensör | Gerekçe |
|-------|------------------------------|---------|
| IMU ≠ VO, IMU ≠ Wheel, VO ≈ Wheel | IMU | IMU sürüklenmesi başladı |
| VO ≠ IMU, VO ≠ Wheel, IMU ≈ Wheel | VO | Görsel landmark kaybı veya aydınlatma değişimi |
| Wheel ≠ IMU, Wheel ≠ VO, IMU ≈ VO | Tekerlek | Kayma tespit edildi |
| Tüm kaynaklar birbirinden farklı | Hepsi şüpheli | Lokalizasyon kaybı senaryosuna geç (§5) |

Sensör güvenilmez ilanı ICD-004 üzerinden Mission Planner'a bildirilir.

### 1.3 Recovery

```
SENSÖR TUTARSIZLIĞI TESPİT EDİLDİ:

1. FDIR güvenlik durumunu CAUTION'a yükselt (eğer NOMINAL'deyse)
2. Navigasyon modülünü bilgilendir (ICD-004: sensor_fault_flag)
3. Güvenilmez sensör devre dışı bırakılır (degraded navigation modu):
   a. IMU güvenilmez → VO + Wheel odometry kombinasyonu devam eder
   b. VO güvenilmez (PSR veya aydınlatma kaybı) → IMU + Wheel devam eder
   c. Wheel güvenilmez → IMU + VO devam eder
4. Navigasyon hızı azaltılır: QAR-NAV-005 (dead-reckoning kayması < 2 m/dak)
5. Araç hızı %50 azaltılır (lokal planlayıcıya komut)
6. Lokalizasyon belirsizliği izlenir:
   - σ < 0.5 m (QAR-NAV-001): nominal kabul; CAUTION kaldırılır
   - σ > 2.0 m (QAR-NAV-004): lokalizasyon kaybı senaryosu (§5)
7. Dönüş kararı: σ > 1.0 m ve CAUTION 60 s geçerse → RETURN_REQUIRED
```

---

## 2. Motor Sıkışması / Tekerlek Hatası

### 2.1 Detection

**Encoder Feedback vs Komut Karşılaştırması:**
- Her tekerlek için: `commanded_speed_rpm` ile `encoder_actual_rpm` izlenir.
- Fark `Δrpm` > TBD-FDIR-002 eşiğini 3 ardışık kontrol periyodunda aşarsa sıkışma şüphesi.

**Akım Monitörü:**
- Motor akımı beklenen tork modeline göre izlenir.
- `actual_current > rated_current × 1.5` ise yük aşımı → sıkışma tespiti.
- `actual_current < rated_current × 0.1` ve komut verilmişse → motor sürücü hatası.

**Çoklu Tekerlek Tutarsızlığı:**
- 4 tekerlekten biri sapıyorsa: o tekerlek izole edilir.
- 2+ tekerlek sapıyorsa: hareket kontrolü durdurulur, FDIR müdahale eder.

Tespit süresi: QAR-FDIR-001'e göre < 50 ms (P95).

### 2.2 Isolation

```
Hangi tekerlek?
├── Encoder verisi: her tekerlekten ayrı ayrı izlenir
├── Sıkışan tekerlek N tespit edildi:
│   ├── N = ön sol → araç döndürme stratejisi sol sapmalı engelden etkilenir
│   ├── N = ön sağ → sağ sapmalı manevra kısıtlanır
│   └── N = arka → güç aktarımı kısıtlanır
└── Birden fazla tekerlek → hareket durdurul, FDIR RETURN_REQUIRED
```

**Dönüş Stratejisi Etkisi:**
- Tek tekerlek arızasında araç 3 tekerlek ile devam edebilir (mobilite analizi: TBD-MAS-001 araç kütlesine bağlı).
- 3 tekerlek ile maksimum hız %60 nominal hız; eğim limiti azaltılır.
- Dönüş rotası 3-tekerlek mobilite modeline göre yeniden hesaplanır.

### 2.3 Recovery

```
MOTOR SIKIŞMASI TESPİT EDİLDİ (tekerlek N):

1. Tekerlek N sürücüsüne sıfır komut gönder (güvenli durdurma)
2. FDIR CAUTION tetikle; Mission Planner'a bildir (ICD-004)
3. 3 tekerlek ile devam kararı:
   IF mobilite_analizi_OK AND dönüş_enerjisi_yeterli:
     a. Hız %60'a düşür
     b. Eğim limiti azalt (HC-005 güncellenmesi)
     c. Replanning talebi: Mission Planner'a 3-tekerlek moda geçiş bildirimi
     d. Dönüş rotası onceliklendir
   ELSE:
     a. Araç durdur (sıfır hız komutu)
     b. FDIR RETURN_REQUIRED tetikle
     c. Yardım çağrısı: acil haberleşme paketi gönder
4. 2+ tekerlek arızası: SURVIVAL modu → dead-reckoning ile safe haven dön
```

---

## 3. Batarya/Panel Anomalisi

### 3.1 Detection

**SoC Sapma Kontrolü:**
- Beklenen SoC tüketim modeline göre her 10 saniyede (QAR-PWR-006) hesaplanır.
- `|actual_soc - predicted_soc| > σ_soc_threshold` (TBD-FDIR-003) → anomali şüphesi.
- Ani SoC düşüşü (Δt süresinde %X SoC kaybı): TBD-FDIR-003.

**Voltaj/Akım Tutarsızlığı:**
- Ohm yasası tutarlılığı: `V_terminal = V_ocv - I × R_internal`.
- `R_internal` beklenen değerden %30 sapıyorsa hücre degradasyonu.

**Hücre Dengesizliği:**
- Bireysel hücre voltajları izlenir.
- En yüksek - en düşük hücre voltajı farkı > TBD-FDIR-004 mV → dengesizlik alarmı.

**Panel Anomalisi:**
- Güneş açısına göre beklenen panel çıkış gücü hesaplanır.
- `actual_power < expected_power × 0.7` ise panel verimliliği düşmüş.

### 3.2 Isolation

| Semptom | Olası Neden | İzolasyon Yöntemi |
|---------|-------------|-------------------|
| Ani SoC düşüşü | Şort devre veya hücre hasarı | Bireysel hücre voltaj taraması |
| Yüksek R_internal | Hücre yaşlanması veya soğuk | Sıcaklık korelasyonu |
| Hücre dengesizliği | Hatalı hücre grubu | Grup bazlı izolasyon (BMS destekliyorsa) |
| Düşük panel gücü | Panel kiri, hasar, açı hatası | Servo açı doğrulaması + güneş sensörü |

**Hatalı Hücre Grubu İzolasyonu:**
Araç BMS (Batarya Yönetim Sistemi) hücre grubu izolasyon özelliğine sahipse (donanım bağımlı: TBD-BAT-002), hasarlı grup devre dışı bırakılabilir. Bu durumda kullanılabilir kapasite düşer ve enerji bütçesi güncellenir.

### 3.3 Recovery — Yük Kesme Sırası

Enerji anomalisinde yük kesme sırası (önce bilimsel, sonra navigasyon, son güvenlik):

```
Yük Kesme Sırası (öncelik sırasıyla):

ADIM 1 — Bilimsel yükler (en önce):
  a. Kamera ve görüntüleme sistemleri
  b. Spektroskopi ve analiz sensörleri
  c. PSR aktif aydınlatma (enerji yoğun)

ADIM 2 — Navigasyon yardımcı yükleri:
  a. Yüksek çözünürlüklü LiDAR (temel navigasyon için değil)
  b. Stereo kamera (lokal engel haritası; kritik olmayan mod)
  c. Panel servo (son pozisyonda kilitlenir)

ADIM 3 — İletişim azaltma:
  a. Yüksek güçlü downlink → minimum beacon moduna geç

ADIM 4 (SURVIVAL) — Yalnızca yaşam destek:
  a. IMU + minimal navigasyon
  b. FDIR çekirdek
  c. Minimum ısıtma (pil koruma: HC-007)
  d. Beacon modu haberleşme
```

**QAR-PWR-003:** Yük kesme tepki süresi < 100 ms.
**QAR-PWR-004:** SURVIVAL modu tüm opsiyonel yük kesimi < 10 ms.

---

## 4. Haberleşme Kesintisi

### 4.1 Detection

**Link Timeout Sayacı:**
- Son başarılı uplink/downlink onayından itibaren süre sayılır.
- Telemetri güncellemesi QAR-COM-002: ≤ 10 s (nominal), QAR-COM-003: ≤ 1 s (kritik durum).
- Link timeout eşiği: TBD-FDIR-006 (TBD-COM-002 ile örtüşür).

**Ayırt edici testler:**
- Yeniden bağlantı girişimi (ping + konum talebi): her TBD-COM-003 saniyede retry.
- Uplink sinyal gücü telemetrisi izlenir.

### 4.2 Isolation: Araç mı, Relay mi, Dünya İstasyonu mu?

```
İzolasyon Ağacı:

link_timeout tetiklendi:
├── Araç haberleşme modülü heartbeat: OK?
│   ├── HAYIR → Araç dahili haberleşme arızası → FDIR araç modülü hatası işle
│   └── EVET ↓
├── Lunar relay (varsa) üzerinden alternatif kanal dene:
│   ├── BAŞARILI → Relay üzerinden bağlantı kuruldu (yer sorunu)
│   └── BAŞARISIZ ↓
└── Dünya istasyonu sorunu veya orbital geometri süresi:
    └── Pre-planned otonom davranış devreye girer
```

Araç kendi haberleşme modülünün sağlığını watchdog üzerinden izler (heartbeat: 5 s, timeout: 30 s; bkz. `docs/architecture/SAFETY_STATE_MACHINE.md` §3.1).

### 4.3 Recovery

```
HABERLEŞMEKESİNTİSİ RECOVERY (CONOPS Senaryo A):

A.1: link_timeout < TBD-FDIR-006 (uyarı eşiği):
  → CAUTION tetikle (NOMINAL'deyse)
  → Mevcut görev planı devam (OTN; otonomi matrisi)
  → Retry başlat (her TBD-COM-003 saniyede)
  → PSR girişi BEKLE (otonomi matrisi BEKLE⁴)

A.2: link_timeout > TBD-FDIR-006 (kritik eşik, COM-004):
  → RETURN_REQUIRED tetikle
  → Safe haven dönüş rotasına geç
  → Link penceresi açılınca tamponlanmış telemetri boşalt

PSR içinde + link yok + enerji kritik:
  → ABT-004 tetikle: ACL acil dönüş (otonomi matrisi)
  → FDIR → RETURN_REQUIRED → Güç Yönetimi dönüş rezervi onaylar → Planner rota üretir
```

**Belirli süre sonra güvenli mod:** CONOPS §6.3 Kural 1 — link yokken araç yeni risk almaz. QAR-COM-004 (otonom çalışma süresi): ≥ TBD saatlik görev günü beklentisi.

---

## 5. Lokalizasyon Kaybı

### 5.1 Detection

**EKF Iraksama Tespiti:**
- EKF (Extended Kalman Filter) inovasyon vektörü `ν = z - h(x̂)` izlenir.
- `|ν|² > χ²_threshold` (ki-kare eşiği) ise EKF uyumsuz → lokalizasyon kaybı şüphesi.
- Tespit süresi: QAR-NAV-004'e göre < 2 saniye.

**Pozisyon Belirsizliği Eşikleri (QAR-NAV-001):**

| Sigma (m) | Durum | Eylem |
|-----------|-------|-------|
| σ < 0.5 m | Nominal | Normal navigasyon devam |
| 0.5 m < σ < 2.0 m | CAUTION | Hız azalt, landmark arama modu |
| σ > 2.0 m | Lokalizasyon kaybı | Dur, FDIR bildir |

### 5.2 Isolation

```
Lokalizasyon Kaybı Kaynağı Belirleme:

1. IMU Drift:
   - IMU tek başına kalırsa dead-reckoning kayması QAR-NAV-005: < 2 m/dak
   - Uzun süre VO/Wheel yoksa IMU drift birikimi şüpheli
   - Test: statik durmak → IMU pozisyon sabit mı?

2. Visual Landmark Kaybı:
   - PSR içi veya aşırı toz → VO çalışmıyor
   - Stereo kamera görüntü kalitesi metrikleri izlenir
   - PSR modunda VO zaten devre dışı (§navigation §3)

3. Harita Uyuşmazlığı:
   - Orbital DEM ile lokal LiDAR haritası karşılaştırılır
   - Büyük sapma (> TBD-FDIR-007 m) → harita güncellenmesi gerekebilir
   - Orbital DEM hatası veya araç büyük sürüklenme yaşamış olabilir
```

### 5.3 Recovery (CONOPS Senaryo C)

```
LOKALİZASYON KAYBI RECOVERY:

C.1: Araç DUR (sıfır hız komutu → Hareket Kontrolü)
     FDIR CAUTION tetikle

C.2: Son bilinen iyi pozisyon referans alınır (last-known-good kayıt sistemi)

C.3: Yeniden lokalizasyon girişimi (TBD-FDIR-008 saniye boyunca):
     a. IMU dead-reckoning devam (QAR-NAV-005: < 2 m/dak kayma)
     b. Görsel landmark eşleştirme:
        - LiDAR ile orbital DEM karşılaştırması
        - Yakın çevredeki tanımlayıcı arazi özelliklerini ara
        - 360° tarama rotasyonu (enerji bütçesi izin veriyorsa)
     c. EKF yeniden başlat: son bilinen iyi konumdan kovaryans sıfırla

C.4: Lokalizasyon geri geldi (σ < 0.5 m) → CAUTION kaldır, harekete devam
     [QAR-NAV-004: tespit → recovery < 2 s hedefi; recovery süresi TBD-FDIR-008]

C.5: TBD-FDIR-008 saniye içinde lokalizasyon geri gelmediyse:
     → RETURN_REQUIRED tetikle
     → Last-known-good waypoint üzerinden safe haven'a dön
     → Dead-reckoning ile navigasyon (IMU + Wheel odometry)
     → Yer segmentine lokalizasyon kaybı bildir

C.6: Dönüş sırasında da lokalizasyon geri gelmediyse:
     → SURVIVAL tetikle
     → Yalnızca IMU dead-reckoning ile safe haven yönünde hareket
     → Hız minimum (kayma ve çarpışma riski yüksek)
```

---

## 6. Watchdog Tasarımı

### 6.1 Her Kritik Modül İçin Heartbeat Timer

Watchdog mimarisi `docs/architecture/SAFETY_STATE_MACHINE.md` §3'te tanımlanmıştır. Bu bölüm uygulama detaylarını tamamlar.

| Modül | Heartbeat Periyodu | Timeout Eşiği | Timeout Sonucu |
|-------|-------------------|---------------|----------------|
| Navigasyon | 100 ms | 500 ms | CAUTION → nav heartbeat kaybı |
| Güç Yönetimi | 500 ms | 2 s | CAUTION → güç heartbeat kaybı |
| Termal Yönetimi | 1 s | 5 s | CAUTION → termal heartbeat kaybı |
| Hareket Kontrolü | 100 ms | 500 ms | CAUTION → hareket heartbeat kaybı |
| Mission Planner | 2 s | 10 s | CAUTION (planlayıcı donduruldu) |
| Haberleşme | 5 s | 30 s | CAUTION → haberleşme heartbeat kaybı |

**Mission Planner heartbeat timeout:** Planlayıcı donduğunda FDIR bağımsız çalışır (Uyum Notu 1; `SAFETY_STATE_MACHINE.md` §4.3). FDIR, temel hareket durdurma ve güç kesme komutlarını doğrudan subsistem arayüzleri üzerinden gönderir.

### 6.2 FDIR Ana Döngüsü Frekansı

FDIR ana döngüsü frekansı: TBD-FDIR-005 (donanım bağımlı; FreeRTOS gerçek zamanlı OS hedef).

Mevcut tasarım hedefleri:
- Heartbeat monitor loop: her 50 ms kontrol (`SAFETY_STATE_MACHINE.md` §3.2)
- Donanım watchdog kick: her 25 ms
- Anomali tespit (QAR-FDIR-001): < 50 ms P95
- Recovery karar (QAR-FDIR-002): < 500 ms anomali tespitinden itibaren

### 6.3 Mission Planner'dan İzole Bellek Bölgesi (Uyum Notu 1)

FDIR, aşağıdaki verileri Mission Planner ile paylaşmaz:

| Kaynak | Neden Ayrı |
|--------|-----------|
| FDIR durum makinesi çalışma zamanı | Planner hatası FDIR'ı etkilememeli |
| Watchdog timer kayıtları | Tamper riski; sadece FDIR okur |
| SURVIVAL modu güç kesim listesi | Planner devre dışıyken de çalışmalı |
| Donanım watchdog kick sinyali | FDIR kendi döngüsüne ait |

ICD-004 üzerinden paylaşılan veriler (tek yönlü mesaj kuyruğu):
- `safety_status` (FDIR → Planner)
- `abort_signal` (FDIR → Planner; Planner operasyonları dondurur)
- `fdir_caution_event` (FDIR → Planner)
- Planner heartbeat (Planner → FDIR)

---

## 7. Abort Sequence

### 7.1 Abort Komutu Geldiğinde Adım Adım Yayılma

Abort, iki kaynaktan gelebilir: (a) yer segmentinden TC-IMMEDIATE komutu, (b) FDIR iç tetikleyicisi (ABT-001..ABT-006).

```
ABORT SEQUENCE (tüm kaynaklardan):

T+0 ms: Abort kaynağı tespit edildi
   - FDIR abort_flag = true
   - Abort türü kaydedilir (yer komutu / iç tetikleyici)

T+0–50 ms: FDIR durum geçişi (QAR-FDIR-001: < 50 ms tespit)
   - Mevcut durumdan RETURN_REQUIRED veya SURVIVAL'a geçiş
   - Durum geçişi deterministik (QAR-FDIR-005: %100)

T+0–500 ms: Recovery kararı (QAR-FDIR-002: < 500 ms)
   FDIR bağımsız olarak şu komutları iletir:
   ├── Hareket Kontrolü: acil dur (sıfır hız) → T+100 ms
   ├── Güç Yönetimi: bilim yükleri kes → T+100 ms (QAR-PWR-003: < 100 ms)
   ├── Navigasyon: minimum moda geç (IMU + dead-reckoning) → T+200 ms
   ├── Haberleşme: acil beacon modu + abort paketini kuyruğa al → T+200 ms
   └── Mission Planner: abort_signal gönder → T+200 ms (Planner operasyonları dondurur)

T+500 ms–2 s: Güvenli durum koşullarını doğrula
   - Araç hareketi sıfırlandı mı?
   - Tüm bilim yükleri kesildi mi?
   - Dönüş enerjisi hesaplandı mı (Güç Yönetimi'nden)?
   - Dönüş rotası hazır mı?

T+2 s: Dönüş moduna geç (RETURN_REQUIRED sağlanmışsa)
   - Navigasyon safe haven koordinatlarına rota hesapla
   - Hareket Kontrolü dönüş rotasını icra et
   - Her güvenli konuma ulaşımda checkpoint kaydet

SURVIVAL modunda (SoC < %10 veya kritik donanım arızası):
   - Yalnızca: IMU + FDIR çekirdek + ısıtma + beacon
   - Hareket: minimum hızda safe haven yönünde
   - Planlayıcı ve replanning hesaplamaları kesilir
   - Panel servo son pozisyonda kilitlenir
```

### 7.2 Güvenli Durum Koşulları

Abort başarılı sayılabilmesi için:

| Koşul | Kaynak |
|-------|--------|
| Araç hızı = 0 (3 saniye boyunca) | Hareket Kontrolü |
| Bilim yükleri akım çekimi = 0 | Güç Yönetimi |
| FDIR RETURN_REQUIRED veya SURVIVAL durumunda | FDIR durum makinesi |
| Abort paketi haberleşme kuyruğuna alındı | Haberleşme |
| Dönüş enerjisi > HC-006 eşiği VEYA SURVIVAL modu aktif | Güç Yönetimi |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent D görev D2 |
