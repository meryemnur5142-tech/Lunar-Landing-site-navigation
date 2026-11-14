# LUNA-AI Arayüz Kontrol Dokümanı (ICD) Şablonları

**Belge ID:** LUNA-AI-ARCH-002  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı ADR:** ADR-006

---

## Genel ICD Politikası

- Tüm modüller aralarında yalnızca bu belgede tanımlı mesaj formatları üzerinden haberleşir.
- Üretici modül arayüzü değiştirmek istediğinde sürüm numarasını artırır ve tüketici modülü bildirir.
- Geriye dönük uyum: minör sürüm artışı mevcut alanları kırmaz; yalnızca yeni alanlar ekler.
- Alan yokluğu (opsiyonel alan) ile alan değerinin sıfır/boş olması anlam olarak farklıdır.
- Hata semantiği: her mesaj bir `status` alanı taşır; tüketici, `status != OK` durumunda varsayılan güvenli davranışı uygular.

---

## ICD-001: Power Management → Mission Planner

**Arayüz ID:** ICD-001  
**Üretici:** Güç Yönetimi (Power Management)  
**Tüketici:** Mission Planner (Görev Planlayıcı)  
**Güncelleme Frekansı:** 1 Hz (nominal); 10 Hz (CAUTION veya üstü durum)  
**Taşıma:** FreeRTOS message queue (uçuş); CCSDS telemetri (yer segmenti yansıması)  
**Versiyon:** 1.0

### Mesaj Formatı: `energy_state`

| Alan | Tip | Birim | Aralık | Açıklama |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0101 | Mesaj tipi sabiti |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Sistem başlangıcından geçen süre |
| `soc_percent` | float32 | % | 0.0 – 100.0 | Mevcut şarj durumu |
| `soc_uncertainty_pct` | float32 | % | 0.0 – 10.0 | SoC ölçüm belirsizliği (1-sigma) |
| `voltage_v` | float32 | V | **TBD** – **TBD** | Ana batarya voltajı |
| `current_ma` | float32 | mA | **TBD** – **TBD** | Anlık çekim akımı (pozitif=tüketim) |
| `panel_power_w` | float32 | W | 0.0 – **TBD** | Güneş paneli anlık gücü |
| `estimated_return_soc_pct` | float32 | % | 0.0 – 100.0 | Safe haven'a dönüş sonunda tahmini SoC |
| `return_soc_uncertainty_pct` | float32 | % | 0.0 – 20.0 | Tahmin belirsizliği (1-sigma) |
| `power_mode` | uint8 | — | 0=NORMAL, 1=SURVIVAL | Mevcut güç modu |
| `status` | uint8 | — | 0=OK, 1=WARN, 2=ERROR | Mesaj durumu |

**Hata Semantiği:**
- `status == WARN`: Mission Planner CAUTION tetikleyicisini değerlendirir
- `status == ERROR`: Mission Planner son geçerli değeri tutar; FDIR'a hata event'i gönderilir
- Mesaj timeout (> 2 s güncelleme yok): FDIR Güç heartbeat timeout olarak işler

**Sürüm Uyumluluk Politikası:**
- Yeni alan ekleme: minör sürüm artışı (1.0 → 1.1); tüketici yeni alanı görmezden gelir
- Alan tipi/aralık değişikliği: majör sürüm artışı (1.0 → 2.0); tüketici uyumluluğu güncellenmeli

---

## ICD-002: Thermal Management → Mission Planner

**Arayüz ID:** ICD-002  
**Üretici:** Termal Yönetimi (Thermal Management)  
**Tüketici:** Mission Planner (Görev Planlayıcı)  
**Güncelleme Frekansı:** 1 Hz (nominal); 10 Hz (CAUTION veya üstü durum)  
**Taşıma:** FreeRTOS message queue  
**Versiyon:** 1.0

### Mesaj Formatı: `thermal_state`

| Alan | Tip | Birim | Aralık | Açıklama |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0201 | Mesaj tipi sabiti |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Sistem başlangıcından geçen süre |
| `num_sensors` | uint8 | — | 1–16 | Aktif sensör sayısı |
| `sensor_temps_c[16]` | float32[16] | °C | **TBD** – **TBD** | Her sensörün sıcaklığı |
| `sensor_ids[16]` | uint8[16] | — | 0–255 | Sensör kimlik numaraları |
| `critical_component_ok` | bool | — | true/false | Tüm kritik bileşenler nominal aralıkta |
| `heater_active_mask` | uint16 | — | bit mask | Aktif ısıtıcılar (bit başına bir ısıtıcı) |
| `thermal_budget_w` | float32 | W | 0.0 – **TBD** | Mevcut termal yük |
| `estimated_time_to_critical_s` | float32 | s | 0.0 – **TBD** | Mevcut hızla kritik eşiğe süre (-1 = hesaplanamaz) |
| `thermal_mode` | uint8 | — | 0=NOMINAL, 1=WARN, 2=CRITICAL | Termal durum özeti |
| `status` | uint8 | — | 0=OK, 1=WARN, 2=ERROR | Mesaj durumu |

**Hata Semantiği:**
- `thermal_mode == WARN`: Mission Planner yüksek güç aktivitelerini kısıtlar
- `thermal_mode == CRITICAL`: Mission Planner FDIR'ı bildirir; FDIR CAUTION/RETURN kararı verir
- Mesaj timeout (> 5 s): FDIR termal heartbeat timeout olarak işler

---

## ICD-003: Navigation → Local Planner

**Arayüz ID:** ICD-003  
**Üretici:** Navigasyon  
**Tüketici:** Yerel Planlayıcı (Local Planner)  
**Güncelleme Frekansı:** ≥ 10 Hz (hareket halinde), ≥ 1 Hz (dur-bekle) [QAR NAV-003]  
**Taşıma:** FreeRTOS message queue (yüksek öncelikli)  
**Versiyon:** 1.0

### Mesaj Formatı: `vehicle_pose`

| Alan | Tip | Birim | Aralık | Açıklama |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0301 | Mesaj tipi sabiti |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Poz tahminin zaman damgası |
| `pos_x_m` | float64 | m | **TBD** koordinat sistemi | Yerel haritada X konumu |
| `pos_y_m` | float64 | m | **TBD** koordinat sistemi | Yerel haritada Y konumu |
| `pos_z_m` | float64 | m | **TBD** koordinat sistemi | Yerel haritada Z (yükseklik) |
| `yaw_rad` | float32 | rad | -π – +π | Sapma açısı (Kuzey referanslı) |
| `pitch_rad` | float32 | rad | -π/2 – +π/2 | Yunuslama açısı |
| `roll_rad` | float32 | rad | -π – +π | Yalpalama açısı |
| `uncertainty_m` | float32 | m | 0.0 – 100.0 | Konum belirsizliği (1-sigma, RMS) |
| `uncertainty_rad` | float32 | rad | 0.0 – π | Yönelim belirsizliği (1-sigma) |
| `velocity_x_ms` | float32 | m/s | **TBD** – **TBD** | X yönünde hız |
| `velocity_y_ms` | float32 | m/s | **TBD** – **TBD** | Y yönünde hız |
| `localization_source` | uint8 | — | 0=EKF_FULL, 1=DEAD_RECKONING, 2=LANDMARK_ONLY | Aktif lokalizasyon kaynağı |
| `localization_valid` | bool | — | true/false | EKF konverjans durumu |
| `status` | uint8 | — | 0=OK, 1=DEGRADED, 2=LOST | Lokalizasyon durumu |

**Kritik Eşik — `uncertainty_m`:**
- `uncertainty_m` > 0.5 m → Yerel Planlayıcı engel yaklaşım hızını yarıya indirir
- `uncertainty_m` > 1.0 m → Yerel Planlayıcı dur, navigasyona yeniden lokalizasyon talebi gönderir
- `status == LOST` → FDIR'a lokalizasyon kaybı event'i gönderilir

**Hata Semantiği:**
- `status == DEGRADED`: Yerel Planlayıcı yalnızca yüksek belirsizlik toleranslı manevralar yapar
- `status == LOST`: Yerel Planlayıcı durma komutu verir; FDIR karar verir
- Mesaj timeout (> 500 ms, hız > 0): FDIR navigasyon heartbeat timeout

---

## ICD-004: FDIR → Mission Executive

**Arayüz ID:** ICD-004  
**Üretici:** FDIR  
**Tüketici:** Mission Executive (Görev Yürütücü / Mission Planner üst katmanı)  
**Güncelleme Frekansı:** Durum değişiminde (event-driven) + 1 Hz kalp atışı  
**Taşıma:** FreeRTOS message queue (en yüksek öncelikli kuyruk)  
**Versiyon:** 1.0

### Mesaj Formatı: `safety_status`

| Alan | Tip | Birim | Aralık | Açıklama |
|------|-----|-------|--------|----------|
| `msg_id` | uint16 | — | 0x0401 | Mesaj tipi sabiti |
| `timestamp_ms` | uint64 | ms | 0 – 2^64 | Zaman damgası |
| `safety_state` | uint8 | — | 0=NOMINAL, 1=CAUTION, 2=RETURN_REQUIRED, 3=SURVIVAL | Mevcut güvenlik durumu |
| `previous_state` | uint8 | — | 0–3 | Önceki güvenlik durumu |
| `transition_reason` | uint16 | — | bit mask | Geçiş tetikleyicileri (her bit bir tetikleyici) |
| `abort_signal` | bool | — | true/false | true ise Mission Planner tüm operasyonları dondurur |
| `allowed_actions_mask` | uint32 | — | bit mask | Mevcut durumda izin verilen eylemler |
| `time_in_state_ms` | uint32 | ms | 0 – 2^32 | Mevcut durumda geçen süre |
| `fdir_confidence` | uint8 | — | 0–100 | FDIR kendi iç güven skoru (teşhis kalitesi) |
| `status` | uint8 | — | 0=OK, 1=DEGRADED | FDIR kendi durumu |

### Abort Yayılma Mekanizması

`abort_signal == true` alındığında Mission Executive:
1. Tüm aktif görev adımlarını dondurur (çalışan eylemi güvenli durumda bitirir veya keser)
2. Hareket Kontrolüne "dur" komutu gönderir
3. FDIR'a abort_acknowledged mesajı gönderir
4. Durum değişikliği bekler

Mission Executive abort'u görmezden **gelemez**. Bu kısıt yazılım mimarisinde zorunlu kılınır (bloklu mesaj kuyruğu, kuyruk taşması yok).

---

## ICD-005: Ground → Flight (Uplink)

**Arayüz ID:** ICD-005  
**Üretici:** Yer Segmenti (Ground Station)  
**Tüketici:** Araç Haberleşme + Mission Planner  
**Taşıma:** CCSDS Telecommand (TC) protokolü  
**Versiyon:** 1.0

### Komut Tipleri

| Komut Tipi | Kod | Öncelik | Timeout | Açıklama |
|------------|-----|---------|---------|----------|
| `TC_IMMEDIATE_ABORT` | 0x01 | P1 | Yok (en kısa sürede işle) | Tüm operasyonları durdur |
| `TC_IMMEDIATE_RETURN` | 0x02 | P1 | Yok | Dönüşü başlat |
| `TC_IMMEDIATE_POWER_OFF` | 0x03 | P1 | Yok | Belirtilen subsistemi kapat |
| `TC_CONDITIONAL` | 0x10 | P2 | 1 saat | Koşullu eylem paketi |
| `TC_PLAN_UPLOAD` | 0x20 | P3 | 24 saat | Günlük görev planı (CFDP ile) |
| `TC_PARAM_UPDATE` | 0x30 | P3 | 1 saat | Parametre güncelleme |
| `TC_QUERY` | 0x40 | P4 | 30 dak | Telemetri/durum isteği |

### Uplink Paket Yapısı (CCSDS Space Packet)

| Alan | Tip | Birim | Açıklama |
|------|-----|-------|----------|
| `primary_header` | 6 byte | — | CCSDS birincil başlık (APID, sekans, uzunluk) |
| `secondary_header` | 10 byte | — | Zaman damgası (CCSDS CUC formatı), komut tipi, öncelik |
| `cmd_sequence_no` | uint32 | — | Komut sıra numarası (tekrar tespit) |
| `checksum_crc32` | uint32 | — | CRC-32 bütünlük kodu |
| `payload` | değişken | — | Komut gövdesi (komut tipine göre yapı değişir) |

**Link Yok Kuralı:** Araç link yokken TC_PLAN_UPLOAD beklemede tutulur; sonraki pencerede işlenir. TC_IMMEDIATE komutlar işleme kuyruğu başına geçer.

**Sürüm Uyumluluk:** Araç tanımadığı komut tipini `NACK` ile yanıtlar; görmezden gelmez.

---

## ICD-006: Flight → Ground (Downlink)

**Arayüz ID:** ICD-006  
**Üretici:** Araç (Flight Segment)  
**Tüketici:** Yer Segmenti (Ground Station)  
**Taşıma:** CCSDS Space Packet (TM — Telemetry)  
**Versiyon:** 1.0

### Telemetri Paket Yapısı

| Alan | Tip | Birim | Güncelleme Frekansı | Açıklama |
|------|-----|-------|---------------------|----------|
| `primary_header` | 6 byte | — | Her paket | CCSDS birincil başlık |
| `secondary_header` | 10 byte | — | Her paket | Zaman damgası + paket tipi |
| `safety_state` | uint8 | — | Durum değişiminde + 1 Hz | Mevcut güvenlik durumu |
| `soc_percent` | float32 | % | 1 Hz / 10 Hz (CAUTION) | Şarj durumu |
| `pos_x_m` | float64 | m | 1 Hz / 10 Hz (CAUTION) | Araç X konumu |
| `pos_y_m` | float64 | m | 1 Hz / 10 Hz (CAUTION) | Araç Y konumu |
| `pos_uncertainty_m` | float32 | m | 1 Hz | Konum belirsizliği |
| `avg_temp_c` | float32 | °C | 1 Hz | Ortalama kritik bileşen sıcaklığı |
| `max_temp_c` | float32 | °C | 1 Hz | En sıcak ölçülen bileşen |
| `link_quality` | uint8 | % | 1 Hz | Alınan sinyal gücü göstergesi |
| `active_faults_mask` | uint32 | — | Değişimde | Aktif arıza bayrakları |
| `mission_step_id` | uint16 | — | 1 Hz | Mevcut görev adımı |
| `science_data_pending_kb` | uint32 | KB | 1 Hz | İletilmeyi bekleyen bilimsel veri |
| `checksum_crc32` | uint32 | — | Her paket | CRC-32 bütünlük kodu |

### Downlink Önceliklendirme

| Paket Tipi | Öncelik | Frekans | Açıklama |
|-----------|---------|---------|----------|
| Acil durum telemetrisi | P1 | Anlık | Güvenlik durumu geçişi, kritik arıza |
| Temel sistem telemetrisi | P2 | ≤ 10 s | SoC, konum, sıcaklık |
| Görev durumu | P3 | ≤ 60 s | Adım ID, bilimsel veri özeti |
| Bilimsel ham veri | P4 | Link izin verdiğince | Görüntü, spektroskopi |

**Tamponlama:** Link yokken tüm telemetri onboard tampon belleğe yazılır. Tampon dolduğunda en düşük öncelikli paketler üzerine yazılır. P1 paketler hiçbir zaman üzerine yazılmaz.

**Hata Semantiği:**
- CRC hatası: yer segmenti paketi atar ve yeniden talep eder (TC_QUERY)
- Paket kayıp: sıra numarası boşluğu tespit edilirse yer segmenti kayıp aralığı bildirir

---

## Arayüz Versiyon Matrisi

| ICD ID | Mevcut Sürüm | Üretici Modülü | Tüketici Modülü | Son Güncelleme |
|--------|-------------|----------------|-----------------|----------------|
| ICD-001 | 1.0 | Güç Yönetimi | Mission Planner | 2026-11-14 |
| ICD-002 | 1.0 | Termal Yönetimi | Mission Planner | 2026-11-14 |
| ICD-003 | 1.0 | Navigasyon | Yerel Planlayıcı | 2026-11-14 |
| ICD-004 | 1.0 | FDIR | Mission Executive | 2026-11-14 |
| ICD-005 | 1.0 | Yer Segmenti | Araç Haberleşme | 2026-11-14 |
| ICD-006 | 1.0 | Araç | Yer Segmenti | 2026-11-14 |

---

*TBD değerleri donanım parametreleri ve orbital analiz tamamlandığında güncellenecektir. Her ICD değişikliği en az 48 saat öncesinden tüketici modül sahibine bildirilir.*
