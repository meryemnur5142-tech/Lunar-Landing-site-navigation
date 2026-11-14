# status: draft
# owner: Agent D
# depends_on:
#   - docs/conops/CONOPS.md
#   - docs/qar/QAR_TABLE.md
#   - domain/mission/phase_state_machine.md
#   - safety/fdir_implementation.md
#   - docs/architecture/SAFETY_STATE_MACHINE.md
# open_items:
#   - TBD-NAV-002: EKF süreç gürültüsü kovaryansı (Q) IMU için
#   - TBD-NAV-003: EKF ölçüm gürültüsü kovaryansı (R) odometri için
#   - TBD-NAV-004: LiDAR menzil ve çözünürlük özellikleri
#   - TBD-NAV-005: Görsel odometri özellik çıkarma parametreleri
#   - TBD-NAV-006: Güneş sensörü doğruluk özellikleri
#   - TBD-NAV-007: DEM çözünürlüğü ve güncelleme frekansı
#   - TBD-NAV-008: PSR navigasyonu son bilinen iyi konumdan max mesafe
#   - TBD-SNS-001: Sensör paketi konfigürasyonu (P-CRIT)
#   - TBD-SNS-002: IMU gürültü parametreleri σ_drift (P-CRIT)
#   - TBD-SNS-003: Odometri hata parametreleri σ_odo (P-CRIT)

# Navigasyon ve Lokalizasyon Mimarisi — LUNA-AI

**Belge ID:** LUNA-AI-VEH-D3-001
**Versiyon:** 0.1-draft
**Tarih:** 2026-11-14
**Sahip:** Agent D

---

## Mimari Genel Bakış

LUNA-AI yüzey navigasyonu, çoklu-sensör füzyon tabanlı bir Genişletilmiş Kalman Filtresi (EKF) üzerine kuruludur. Temel tercih EKF olmakla birlikte, sensör arızası ve PSR gibi zorlu ortamlar için graceful degradation stratejileri tanımlanmıştır.

**Uyum Notu 4 — Landing GNC ≠ Yüzey Navigasyon:**
İniş GNC sistemi ve yüzey navigasyon sistemi ayrı modüllerdir. Handover protokolü §5'te tanımlanmıştır. İniş GNC, yüzey navigasyonunun kontrolüne dahil edilmez.

---

## 1. Sensör Füzyon Mimarisi

### 1.1 Sensör Envanterleri ve Rolleri

| Sensör | Güncelleme Frekansı | Birincil Rol | Kısıtlar |
|--------|--------------------|-----------|---------| 
| IMU | 100–1000 Hz | Yüksek frekans attitude ve hızlanma; dead-reckoning taşıyıcısı | Drift birikir; tek başına uzun süre kullanılamaz (QAR-NAV-005: < 2 m/dak) |
| Tekerlek odometrisi | 50–100 Hz | Çizgisel yer değiştirme; EKF için sık güncelleme | Kayma hatası: PSR kumu, yumuşak zemin, dik iniş |
| Görsel odometri (VO) | 1–10 Hz (hesap yoğun) | Göreli konum değişimi; landmark eşleştirme | PSR içi karanlıkta çalışmaz; hesaplama yükü yüksek |
| Stereo kamera / LiDAR | 1–5 Hz | Yerel harita, landmark eşleştirme, 3D engel haritası | PSR içinde aydınlatma gerektirir; LiDAR aktif ışık (enerji tüketir) |
| Güneş sensörü | 1 Hz | Mutlak yönelim (yaw referansı) | PSR içinde geçersiz (güneş görünmüyor) |
| Orbital DEM karşılaştırma | Seyrek (dakikada 1 veya daha az) | Global drift düzeltme; uzun dönem konum önyargısını gider | Veri aktarım gecikmesi; yüksek hesap yükü; DEM çözünürlüğüne bağlı (TBD-NAV-007) |

### 1.2 Temel Algoritma Seçimi: EKF vs UKF vs Particle Filter

| Yöntem | Artıları | Eksileri | LUNA-AI Kararı |
|--------|---------|---------|---------------|
| **EKF** (Genişletilmiş Kalman Filtresi) | Hesap etkin, deterministik, iyi belgelenmiş | Yüksek nonlinearity'de linearizasyon hatası | **Temel seçim** |
| **UKF** (Unscented Kalman Filtresi) | Nonlineer modellerde EKF'den iyi; türev hesabı gerekmez | EKF'den ~3× daha fazla hesap yükü | PSR içinde veya yüksek belirsizlikte yedek |
| **Particle Filter** | Çok modlu dağılımları temsil eder; tam nonlineer | O(N_parçacık) bellek ve hesap; gerçek zamanlı zorluktur | Lokalizasyon recovery senaryosunda lokal landmark arama için |

**Tercih gerekçesi:** EKF, IMU gibi yüksek frekanslı sensörler için hesap etkin ve QAR-NAV-003 (≥ 10 Hz güncelleme) hedefini karşılayabilir. Sensör arızası durumunda EKF iç yapısı kolay degrade edilir (kovaryans matrisini genişletme veya daraltma). UKF yedek olarak PSR fazına tahsis edilir çünkü PSR navigasyonu LiDAR-only modunda yüksek nonlinearity içerir.

### 1.3 EKF Durum Vektörü

```
x = [p_x, p_y, v_x, v_y, θ, ω, b_acc, b_gyro]^T

p_x, p_y  : konum (m), yerel harita çerçevesi
v_x, v_y  : hız (m/s)
θ          : yaw açısı (rad)
ω          : yaw hız (rad/s)
b_acc     : ivmeölçer sapma (m/s²); TBD-SNS-002
b_gyro    : jiroskop sapma (rad/s); TBD-SNS-002
```

**Süreç gürültüsü Q:** TBD-NAV-002 (IMU gürültü parametrelerine bağlı; TBD-SNS-002 kapandıktan sonra kesinleşir).
**Ölçüm gürültüsü R:** TBD-NAV-003 (odometri ve VO hata parametrelerine bağlı; TBD-SNS-003).

### 1.4 Sensör Füzyon Stratejisi

**Nominalde çalışan füzyon (tam sensör seti):**

```
Her 100 ms (10 Hz minimum, QAR-NAV-003):
  PREDICT:
    1. IMU hızlanma + jiroskop verisi → kinematik model ile konum tahmini
    2. Kovaryans P güncelleme (süreç gürültüsü Q eklenir)

  UPDATE (mevcut sensöre göre):
    - Tekerlek odometrisi geldi: hız güncellemesi (Kalman kazanı hesapla)
    - VO güncellemesi (1-10 Hz): göreli konum düzeltmesi
    - LiDAR landmark eşleştirme (1-5 Hz): mutlak konum düzeltmesi
    - Güneş sensörü (1 Hz): yaw düzeltmesi (PSR dışında)
    - DEM karşılaştırma (seyrek): global drift düzeltme; büyük konum güncelleme
      → Büyük DEM güncellemesi Kalman kazanı ile ağırlıklandırılır; ani sıçrama engellenir
```

**Sensör ağırlıkları:** Kovaryans matrisleri (Q, R) sensör güvenilirliğini otomatik ağırlıklandırır. Güvenilmez ilan edilen sensörün R değeri büyütülür → o sensörün etkisi azalır.

### 1.5 Graceful Degradation

| Aktif Sensörler | Navigasyon Modu | Konum Doğruluğu |
|----------------|-----------------|-----------------|
| IMU + VO + Wheel + LiDAR + Güneş | Tam füzyon | QAR-NAV-001: < 0.5 m RMS |
| IMU + VO + Wheel (güneş yok / PSR) | 3-sensör füzyon | ~0.5–1.0 m |
| IMU + Wheel (VO çalışmıyor) | 2-sensör; sık drift düzeltme gerekir | ~1.0 m; hız azalt |
| IMU + LiDAR (PSR içi, karanlık) | LiDAR-only; UKF'e geç | QAR-NAV-006: < 1.0 m RMS |
| Yalnızca IMU | Dead-reckoning | QAR-NAV-005: < 2 m/dak kayma |

---

## 2. Belirsizlik Yönetimi

### 2.1 Eşikler ve Eylemler

Pozisyon belirsizliği sigma değeri (EKF kovaryans matrisinden çıkarılan Tr(P)^0.5):

| Sigma (m) | Durum | Navigasyon Eylemi | FDIR Bildirimi |
|-----------|-------|-------------------|----------------|
| σ < 0.5 m | Nominal | Normal navigasyon; QAR-NAV-001 uyum | Yok |
| 0.5 m < σ < 2.0 m | Dikkat | Hız %50 azalt; aktif landmark arama; DEM karşılaştırma tetikle | FDIR CAUTION (eğer NOMINAL'deyse) |
| σ > 2.0 m | Lokalizasyon kaybı | Araç DUR; lokalizasyon recovery başlat (FDIR §5) | FDIR RETURN_REQUIRED tetikle |

Tespit süresi: QAR-NAV-004'e göre < 2 saniye (EKF uyumsuzluk → alarm).

### 2.2 Belirsizlik Yayımı

Navigasyon sistemi yayımlanan her konum mesajına kovaryans bilgisini ekler:
```
vehicle_pose:
  position: {x, y}
  position_uncertainty_m: σ_pos   # QAR izleme için
  orientation: {yaw, pitch, roll}
  orientation_uncertainty_deg: σ_att
  timestamp_ns: ...
```

CONOPS §7 "Belirsizlik Görünür" ilkesi: tüm tahmin ve hesaplamalar belirsizlik bandıyla yayımlanır.

### 2.3 Landmark Arama Stratejisi

Belirsizlik artışında aktif landmark arama:
1. LiDAR ile 180° yelpaze tarama; orbital DEM yüzey özellikleri ile karşılaştır
2. Tanımlayıcı arazi özelliği (kaya, krater kenarı) bulunursa: EKF landmark güncelleme
3. Landmark bulunamazsa: seyahat hızını yarıya düşür; mevcut rotada ilerle
4. σ > 2.0 m → dur, §FDIR Senaryo 5 prosedürü

---

## 3. PSR Navigasyonu (Işık Yok)

### 3.1 PSR İçinde Çalışan Sensörler

PSR (Kalıcı Gölge Bölgesi) içinde güneş ışığı bulunmaz. Sensör uygulanabilirliği:

| Sensör | PSR İçi Durum | Gerekçe |
|--------|--------------|---------|
| IMU | Çalışır | Pasif; ışıktan bağımsız |
| Tekerlek odometrisi | Çalışır (kayma riski artar) | Pasif; PSR kumu kayma etkisi büyüyor |
| Görsel odometri | Çalışmaz (karanlık) | Görsel bilgi yok; aktif aydınlatma pahalı |
| Stereo kamera | Yalnızca aktif aydınlatmayla | Yüksek enerji tüketimi; kısıtlı kullanım |
| **LiDAR** | **Çalışır (aktif ışık)** | Kendi ışığını gönderir; PSR navigasyonun temel sensörü |
| Güneş sensörü | Çalışmaz | Güneş görünmüyor |
| Orbital DEM | Kullanılabilir (seyrek) | Veri önceden yüklenmiş; güncelleme mümkün değil |

### 3.2 PSR İçi Navigasyon Stratejisi

**Temel:** LiDAR-based navigasyon + IMU füzyon.

```
PSR içi EKF konfigürasyonu:
  - Aktif sensörler: IMU + Tekerlek Odometrisi + LiDAR
  - Devre dışı: VO, Güneş sensörü (ölçüm gürültüsü R → ∞)
  - Algoritma: Temel EKF yerine UKF'e geç (LiDAR+IMU nonlinearity)
  - Landmark kaynak: orbital DEM'den PSR öncesi yüklenmiş kaya/krater listesi
  - Güncelleme frekansı: QAR-NAV-003 uyumu için ≥ 10 Hz (IMU), ≥ 1 Hz (LiDAR)

LiDAR tabanlı landmark eşleştirme (PSR içinde):
  1. LiDAR nokta bulutu üret (her tarama)
  2. Normal Distribution Transform (NDT) veya ICP ile önceki taramaya kayıt
  3. Orbital DEM yüzey özellikleriyle seyrek eşleştirme (global drift düzeltme)
  4. EKF/UKF güncelleme: LiDAR konum gözlemi ile kovaryans düzelt
```

**Doğruluk hedefi:** QAR-NAV-006'ya göre PSR içi navigasyon doğruluğu < 1.0 m RMS.

### 3.3 PSR Giriş Öncesi Bootstrap Noktası

PSR girişinde last-known-good pozisyon kaydı yapılır:

```
PSR_ENTRY_BOOTSTRAP:
  1. PSR sınırına ulaşmadan 10 m önce: konum ve kovaryansı kaydet
  2. EKF kovaryansını sıfırla (σ_pos → 0.3 m başlangıç; TBD-NAV-001 kapatılınca güncellenir)
  3. Bootstrap noktası: araç hafızasında sabit referans olarak tutulur
  4. PSR içinde DEM karşılaştırması bu noktadan ölçülür
  5. Acil dönüş senaryosunda: bootstrap noktası last-known-good waypoint olarak kullanılır
```

Bootstrap noktasından maksimum mesafe: TBD-NAV-008 (§10 araç güç modeline bağlı; bu mesafenin ötesinde DEM karşılaştırma güvenilirliği düşer).

---

## 4. Harita Yönetimi

### 4.1 Global Harita (Orbital Veri)

**Kaynak:** Orbital kameralar (örn. LRO, Chandrayaan-3 benzeri) tarafından üretilen DEM (Dijital Yükseklik Modeli) ve ortofoto.

| Özellik | Değer |
|---------|-------|
| Çözünürlük | TBD-NAV-007 (orbital misyon çıktısına bağlı) |
| Güncelleme | Görev öncesi yüklenir; görev sırasında güncelleme mümkün değil (yer-araç bant genişliği kısıtı) |
| Kapsam | Tüm operasyon alanı + güvenli mesafe tamponu |
| Kullanım | Global planlayıcı rota hesabı, PSR landmark kaynağı, DEM karşılaştırma |

**Öngörü hatası:** DEM çözünürlük sınırı < araç boyutu olan kayaları gösteremez. Global harita lokal engelleri temsil etmez → lokal harita zorunlu.

### 4.2 Lokal Harita (Gerçek Zamanlı)

**Kaynak:** Araç sensörleri: LiDAR + stereo kamera + tekerlek odometrisi.

| Özellik | Değer |
|---------|-------|
| Çözünürlük | Araç çevresinde ~0.1 m/piksel |
| Güncelleme frekansı | LiDAR: 1–5 Hz; kamera: 5–10 Hz |
| Kapsam | Araç çevresinde ±50 m yarıçap |
| Kullanım | Lokal planlayıcı engel haritası, anlık replanning |

**Veri yapısı:** OccupancyGrid (doluluk ızgarası); her hücre `obstacle_fraction` değeri taşır (HC-003 ile tutarlı: 0.20 üstü geçilemez).

### 4.3 Füzyon ve Tutarsızlık Tespiti

```
Harita Füzyon Stratejisi:

1. Global harita zemin katmanı (statik)
2. Lokal harita üstüne bindirme (dinamik):
   - Lokal harita bir kaya tespit ederse: global harita güncellenmez
   - Lokal harita güncel tutulur (kayan pencere)
3. Tutarsızlık tespiti:
   - Lokal harita engebesi orbital DEM'in öngördüğünden >TBD m farklıysa:
     → Navigasyon sistemi uyarısı: DEM güvenilirliği düştü
     → Planlayıcı lokal haritayı ön plana al
4. PSR içinde lokal harita güncelleme: LiDAR only (kamera çalışmıyor)
5. PSR dışına çıkınca: kamera lokal haritayı yeniden doğrular
```

---

## 5. Landing GNC → Yüzey Navigasyon Handover

### 5.1 Mimari Ayrım (Uyum Notu 4)

İniş GNC sistemi ve yüzey navigasyon sistemi ayrı donanım ve yazılım birimleridir:

| Özellik | Landing GNC | Yüzey Navigasyon |
|---------|------------|-----------------|
| Aktif faz | LANDING | SURFACE_EXPLORATION, PSR_OPS, RETURN |
| Birincil referans | Radar altimetre, IMU, landing camera | IMU, VO, LiDAR, tekerlek odometrisi |
| Koordinat çerçevesi | İniş elipsi merkezli | Yerel yüzey haritası çerçevesi |
| Güç modu | GNC tam aktif | Navigasyon tam aktif |

**Paylaşılan veri:** Yalnızca son konum ve kovaryans mesajı; ICD üzerinden tek yönlü.

### 5.2 Bootstrap Süreci: İlk Konum Kestirimi

```
LANDING GNC → YÜZEY NAVİGASYON HANDOVER:

T_land: Araç yüzeyle temas
  1. Landing GNC son konum tahmini: (x_land, y_land, σ_land) kaydet
  2. Landing GNC → Yüzey Navigasyon: handover mesajı (ICD-GNC-NAV)
     içerik: {last_gnc_position, gnc_covariance, timestamp}

T_land + 30 s: Araç stabilite onayı (phase_state_machine §4.2)
  3. Yüzey Navigasyon EKF başlatılır:
     - Başlangıç konum: GNC son konum kestirimi
     - Başlangıç kovaryansı: GNC kovaryansı × güvenlik faktörü
       [σ_pos_init = TBD-NAV-001; GNC kovaryansından alınır]
  4. IMU boot kalibrasyonu (statik; 10–30 s): sapma offsetleri ölçülür
  5. Tekerlek odometrisi sıfırlanır (referans noktası: iniş konumu)

T_land + 60–120 s: İlk lokalizasyon doğrulaması
  6. LiDAR ile çevre taraması; orbital DEM ile eşleştirme
  7. Eğer eşleştirme başarılıysa: EKF kovaryansı düşer; σ_pos < 0.5 m
  8. Güneş sensörü (PSR dışında): yaw doğrulama
  9. Handover doğrulama kriterleri karşılanırsa:
     → `navigation_ready = true` mesajı FDIR'a gönderilir
     → Faz makinesi LANDING → SURFACE_EXPLORATION geçişine izin verilir

Handover doğrulama kriterleri:
  - σ_pos ≤ QAR-NAV-001 hedefi (< 0.5 m RMS)
  - EKF kovaryans azalıyor (ıraksamıyor)
  - IMU kalibrasyonu tamamlandı
  - Telemetri nominal (haberleşme HC-014)
```

### 5.3 Bootstrap Başarısız Senaryosu

```
Bootstrap doğrulaması TBD-NAV-001 bekleme süresinde tamamlanamazsa:

1. FDIR CAUTION tetikle (navigasyon bootstrap başarısız)
2. Yüzey keşfi başlamaz; faz makinesi SURFACE_EXPLORATION'a geçmez
3. Yer segmentine bildir: manuel müdahale veya yeniden bootstrap dene
4. Yeniden bootstrap: IMU yeniden kalibrasyon + DEM eşleştirme yeniden dene
5. İkinci deneme de başarısız olursa: SAFE_STATE (yer kararı beklenir)
```

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent D görev D3 |
