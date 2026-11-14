# status: draft
# owner: Agent C
# depends_on: [simulation/scenarios/operational_scenarios.md, docs/adr/FMEA_KRITIK_MODULLER.md, docs/architecture/SAFETY_STATE_MACHINE.md, domain/environment/uncertainty_policy.md, config/tbd_register.md]
# open_items: [TBD-SIM-001..TBD-SIM-012 — araç parametreleri §10 bekleniyor; HIL donanım listesi P2 kapısına bağlı]

# Dijital İkiz ve Simülatör Tasarımı — LUNA-AI v1.0

**Belge ID:** LUNA-AI-SIM-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı Belgeler:** LUNA-AI-ARCH-001, LUNA-AI-FMEA-001, operational_scenarios.md (SC-001..SC-009)

---

## 1. Çevresel Model (Environment Model)

### 1.1 Ay Yerçekimi ve Yüzey Modeli

Ay yerçekimi sabiti **g_moon = 1.62 m/s²** (referans: IAU lunar gravity model).

| Parametre | Değer | Kaynak / Not |
|-----------|-------|--------------|
| Yerçekimi ivmesi | 1.62 m/s² | IAU sabit |
| Yüzey ivme yereli sapması | ±0.01 m/s² (ekvator-kutup) | LRO veri referansı |
| Yüzey yoğunluğu (regolith) | TBD-SIM-001 (source: §10 arazi modeli) | Tekerlek-toprak etkileşim modeli için |
| DEM çözünürlüğü | TBD-SIM-002 (source: §10 bölge seçimi) | LRO LOLA veya eşdeğeri |
| Hedef bölge referans koordinatı | TBD-TIME-001 bağımlı | Görev otoritesi onayı |

**Yüzey Model Entegrasyonu:**

Dijital yükseklik modeli (DEM) terrain_analyzer modülü (`data-platform/processing/terrain_analyzer.py`) üzerinden yüklenir. Simülatör DEM'i düzlemsel yaklaşımdan gerçek nokta-koordinat tablasına yükseltir:

```
TerrainGrid:
  resolution_m: TBD-SIM-002
  origin_lat, origin_lon: TBD-TIME-001
  elevation_data: float32[N, M]   # LRO LOLA veya eş değer
  slope_map: float32[N, M]        # eğim haritası (°)
  roughness_map: float32[N, M]    # pürüzlülük indeksi
```

### 1.2 Güneş Işınımı Modeli

| Parametre | Değer | Not |
|-----------|-------|-----|
| Güneş sabiti (1 AU) | 1361 W/m² | ASTM E490 |
| Ay mesafesi düzeltmesi | ±3.3% (perigee/apogee) | NASA ephemeris |
| Panel verim katsayısı | TBD-SOL-001 bağımlı (§10) | —  |
| Panel yönelimi (servo açısı) | Araçtan gelen yönelim verisi + güneş açısı | ICD-003 vehicle_pose |
| Gölge modeli | Ray-casting üzerinde DEM tabanlı | PSR = 0 W/m² (kalıcı gölge) |

Işınım modeli formülü:

```
P_panel(t) = P_nominal × cos(θ_incidence(t)) × η_cell × (1 - α_dust)
  θ_incidence: panel normali ile güneş vektörü arası açı
  η_cell: TBD-SOL-001 (hücre verimi, §10)
  α_dust: TBD-SIM-003 (toz kaplama kaybı faktörü, §10 ortam analizi)
```

### 1.3 Termal Ortam Modeli

Ay termal ortamının üç bölgesi simülatörde ayrı modellenir:

| Bölge | Yüzey Sıcaklığı | Simülasyon Yaklaşımı |
|-------|-----------------|----------------------|
| Güneşli yüzey | ~+120 °C | Stefan-Boltzmann ışınım + güneş akısı; termal denge iterasyonu |
| Karanlık/gölge | ~-173 °C | Sadece ışınım kaybı; regolith termal inersi |
| PSR (kalıcı karanlık) | -200 °C ile -173 °C arası | Kalıcı gölge; yer ısısı ihmali (düşük etki) |

```
T_surface(t) = f(solar_flux, albedo, emissivity, regolith_thermal_inertia)
  albedo: TBD-SIM-004 (source: §10 bölgeye özgü ölçüm)
  emissivity: ~0.95 (ay regolith ön değeri)
  thermal_inertia: TBD-SIM-005 (source: §10 jeoloji analizi)
```

Araç termal modeli ile yüzey modeli arasındaki ısı değişimi: §2.2 Termal Modeli.

### 1.4 Arazi-Araç Etkileşimi

| Etki | Model | Parametre |
|------|-------|-----------|
| Tekerlek kayması | SCM (Soil Contact Mechanics) basitleştirilmiş | TBD-SIM-001 (zemin tipi + yoğunluk) |
| Engel çarpışması | AABB (Axis-Aligned Bounding Box) + çözüm | TBD-MAS-001 (araç kütlesi) |
| Eğimli arazi tepkisi | Yerçekimi kuvveti + normal kuvvet vektör ayrıştırması | g_moon = 1.62 m/s² |
| Tekerlek-zemin tork | Basit rolling resistance modeli | TBD-SIM-001 |

---

## 2. Araç Modeli (Vehicle Model)

### 2.1 Güç Modeli

Güç modeli üç alt modülden oluşur:

**Panel Üretimi:**
```
P_generated(t) = P_panel(t)  [§1.2 ışınım modelinden]
```

**Batarya Modeli:**
```
SoC(t+dt) = SoC(t) + (P_generated - P_load) × dt / Capacity_Wh
  Capacity_Wh: TBD-BAT-001 (§10)
  SoC_min: TBD-BAT-002 bağımlı (kimyaya göre cut-off voltaj)
  SoC_max: 100% (şarj regülatörü sınırı)
  Coulombic_efficiency: TBD-BAT-002 (kimya §10)
  Capacity_degradation: SoH × Capacity_nominal (SoH: dijital ikiz §3.3)
```

**Yük Tüketimi:**

| Alt Sistem | Nominal Güç (W) | Kaynak |
|------------|-----------------|--------|
| OBC + Navigasyon işlemcisi | TBD-SIM-006 | §10 güç bütçesi |
| Motor sürücüleri (hareket halinde) | TBD-SIM-007 | §10 güç bütçesi |
| Isıtıcılar (nominal) | TBD-SIM-008 | §10 termal bütçe |
| Haberleşme (HGA aktif) | TBD-SIM-009 | §10 güç bütçesi |
| Bilimsel sensörler | TBD-SIM-010 | §10 güç bütçesi |
| Beacon modu (SURVIVAL) | TBD-SIM-009 / 10 | §10 minimum güç |

### 2.2 Termal Model

```
dT_component/dt = (Q_heater + Q_solar_input - Q_radiation - Q_conduction) / (m × Cp)
  m: TBD-MAS-001 (bileşen kütlesi, §10)
  Cp: TBD-THM-001 (ısıl kapasite, §10)
  Q_heater: ısıtıcı güç (termal kontrol sinyalinden)
  Q_radiation: σ × ε × A × (T_component⁴ - T_env⁴)
  Q_conduction: k × A × (T1 - T2) / L   [bileşenler arası]
```

**Kritik Bileşen Termal Parametreleri:**

| Bileşen | Nominal Çalışma Aralığı (°C) | Kritik Alt Sınır | Kaynak |
|---------|------------------------------|------------------|--------|
| Batarya | TBD-THM-001 | TBD-THM-003 | §10 termal |
| OBC işlemcisi | TBD-THM-001 | TBD-THM-003 | §10 termal |
| IMU | TBD-THM-001 | TBD-THM-003 | §10 termal |
| RF modülü | TBD-THM-001 | TBD-THM-003 | §10 termal |

### 2.3 Kinematik Model

Araç diferansiyel tahrik modeli:

```
Diferansiyel Sürüş Kinematiği:
  v_linear = (v_right + v_left) / 2
  ω_angular = (v_right - v_left) / wheel_base
  wheel_base: TBD-MAS-001 bağımlı (araç genişliği, §10)

Pozisyon Güncellemesi (Euler integrasyon, dt = 50 ms):
  x(t+dt) = x(t) + v_linear × cos(θ) × dt
  y(t+dt) = y(t) + v_linear × sin(θ) × dt
  θ(t+dt) = θ(t) + ω_angular × dt

Tekerlek Dinamiği:
  v_wheel_max: TBD-TRV-001 bağımlı (nominal hız §10)
  max_slope: TBD-TRV-002 (°, §10)
  traction_limit: TBD-SIM-001 bağımlı (zemin modeli)
```

### 2.4 Sensör Modeli

**IMU Gürültü Modeli:**

```
a_measured = a_true + bias_a + noise_a
  bias_a ~ N(0, σ_bias)     σ_bias: TBD-SNS-002 (§10 IMU parça)
  noise_a ~ N(0, σ_noise)   σ_noise: TBD-SNS-002 (§10 IMU parça)

ω_measured = ω_true + bias_g + noise_g
  bias_g: TBD-SNS-002
  noise_g: TBD-SNS-002
  drift_rate: TBD-SNS-002 (°/h — parça seçimi ile kesinleşecek)
```

**Kamera FOV Modeli:**

```
Camera:
  horizontal_fov: TBD-SNS-001 (°)
  vertical_fov: TBD-SNS-001 (°)
  resolution: TBD-SNS-001 (px × px)
  noise_sigma: TBD-SNS-001 (SNR modeli)
  landmark_detection_range_m: TBD-SNS-001
```

**LiDAR Nokta Bulutu Modeli:**

```
LiDAR:
  range_m: TBD-SNS-001
  angular_resolution: TBD-SNS-001 (°)
  point_cloud_rate_hz: TBD-SNS-001
  range_noise_sigma_m: TBD-SNS-001
  dropout_probability: TBD-SIM-003 (toz modeli etkisi)
```

**Odometry Modeli:**

```
odometry_error:
  sigma_odo_distance: TBD-SNS-003 (§10 — %/m)
  sigma_odo_heading: TBD-SNS-003 (°/m)
  slip_model: TBD-SIM-001 bağımlı (zemin modeli)
```

---

## 3. Dijital İkiz (Digital Twin)

### 3.1 Gerçek Telemetri ile Simülasyon Karşılaştırması

Dijital ikiz, gerçek araç telemetrisini paralel çalışan simülatör çıktısıyla karşılaştırır:

```
Karşılaştırma Metrikleri:
  position_residual_m: |pos_real - pos_sim| (maks kabul: TBD-THM-002 bağımlı)
  soc_residual_pct: |SoC_real - SoC_sim| (maks kabul: TBD-ENE-001)
  temperature_residual_c: |T_real - T_sim| / komponent (maks kabul: TBD-THM-002)
  nav_uncertainty_ratio: σ_pos_real / σ_pos_sim

Anomali Tespiti:
  residual > threshold → dijital ikiz uyarısı
  → Parametre güncellemesi tetiklenir (§3.3)
  → Yer segmentine bildirim (ICD-006 downlink)
```

### 3.2 Zaman İlerletilebilir Simülasyon

Hızlandırılmış görev önizlemesi için simülatör gerçek zamanlı değil, belirlenmiş hız faktörünü destekler:

```yaml
# Simülasyon zaman parametreleri
time_acceleration_factor: [1x, 10x, 100x, 1000x]
dt_physics_s: 0.05          # fizik motoru adım boyutu (sabit)
dt_telemetry_log_s: 1.0     # telemetri kayıt adımı
dt_snapshot_s: 60.0         # checkpoint kayıt aralığı

# Zaman yönetimi
mission_start_utc: TBD-TIME-001
max_simulation_duration_h: TBD (görev senaryosuna göre)
```

**Kullanım senaryoları:**
- **Görev öncesi önizleme:** 100x hızda 72 saatlik yüzey keşfini ~43 dakikada simüle et.
- **PSR operasyon planlama:** 10x hızda PSR giriş/çıkış enerjisi doğrulaması.
- **Termal validasyon:** 1000x hızda bir lunar gece/gündüz döngüsünü ~90 saniyede simüle et.

### 3.3 Parametre Güncelleme: Araç SoH Degradasyonu

State-of-Health (SoH) gerçek telemetri verisiyle güncellenir:

```python
# SoH güncelleme döngüsü (konsept — simge kod)
class SoHUpdater:
    """
    Gerçek telemetri ile simülatör parametrelerini senkronize eder.
    """
    def update_battery_soh(self, real_capacity_wh: float, nominal_capacity_wh: float):
        """
        SoH = C_measured / C_nominal
        Her şarj-deşarj döngüsünde güncellenir.
        """
        self.soh_battery = real_capacity_wh / nominal_capacity_wh  # 0.0–1.0

    def update_motor_efficiency(self, real_torque_nm: float, cmd_torque_nm: float):
        """Motor mekanik verimi degradasyonu."""
        self.eta_motor = real_torque_nm / cmd_torque_nm

    def update_panel_efficiency(self, real_power_w: float, expected_power_w: float):
        """Panel verimi: toz, radyasyon hasarı etkisi."""
        self.eta_panel = real_power_w / expected_power_w

    def apply_to_simulator(self, sim: 'VehicleSimulator'):
        """Güncel SoH değerlerini simülatör modellerine uygula."""
        sim.battery.capacity_wh *= self.soh_battery
        sim.motor.efficiency = self.eta_motor
        sim.solar_panel.efficiency = self.eta_panel
```

---

## 4. Senaryo Çalıştırıcısı (Scenario Runner)

### 4.1 Senaryo Formatı (YAML)

Her senaryo YAML dosyası üç ana bölümden oluşur: başlangıç koşulları, olaylar, bitiş kriterleri.

```yaml
# Senaryo YAML Şeması — LUNA-AI v1.0
scenario_id: "SC-XXX"
name: "Senaryo Adı"
description: "Kısa açıklama"
version: "1.0"
created: "YYYY-MM-DD"
references:
  - operational_scenarios: "SC-XXX"
  - safety_state_machine: "LUNA-AI-ARCH-001"

# --- Başlangıç Koşulları ---
initial_conditions:
  position:
    x_m: 0.0
    y_m: 0.0
    z_m: 0.0            # DEM'den hesaplanır
    uncertainty_m: 0.3  # başlangıç konum belirsizliği
  heading_deg: 0.0
  velocity_ms: 0.0
  soc_percent: 85.0
  safety_state: "NOMINAL"
  mission_phase: "SURFACE_EXPLORATION"
  thermal_state:
    battery_temp_c: TBD    # §10 termal model
    obc_temp_c: TBD
    nominal_all: true
  time_utc: TBD-TIME-001   # görev başlangıç tarihi

# --- Olaylar (zaman veya koşul tetiklemeli) ---
events:
  - id: "EVT-001"
    trigger:
      type: "time"           # "time" | "condition" | "command"
      time_offset_s: 0.0
    action:
      type: "waypoint_set"
      waypoints: []          # koordinat listesi

# --- Bitiş Kriterleri ---
termination_criteria:
  success:
    - condition: "all_waypoints_reached"
    - condition: "soc_above_threshold"
      threshold_pct: 20.0
  failure:
    - condition: "soc_below_critical"
      threshold_pct: 10.0
    - condition: "safety_state_equals"
      state: "SURVIVAL"
    - condition: "max_time_exceeded"
      max_duration_s: TBD

# --- Kabul Kriterleri ---
acceptance_criteria:
  - id: "AC-001"
    description: "Tüm waypoint'lere ±1m içinde ulaşıldı"
  - id: "AC-002"
    description: "SoC hiçbir zaman %10'un altına düşmedi"
  - id: "AC-003"
    description: "Nav belirsizliği 1.0m RMS'i aşmadı"
```

### 4.2 Mevcut Senaryolarla Tutarlılık

`simulation/scenarios/operational_scenarios.md` (SC-001..SC-009) ile karşılık tablosu:

| Operasyonel Senaryo | YAML Dosyası | Test Türü |
|---------------------|--------------|-----------|
| SC-001 (Normal Keşif) | `nominal_surface_exploration.yaml` | SIL |
| SC-002 (Link Kaybı) | `comm_loss_surface.yaml`, `comm_loss_psr.yaml` | SIL |
| SC-003 (PSR Enerji Düşüşü) | `psr_energy_emergency.yaml` | SIL |
| SC-004 (Lokalizasyon Kaybı) | `localization_loss_recovery.yaml` | SIL |
| SC-005 (Safe Haven Erişilemiyor) | `safe_haven_blocked.yaml` | SIL |
| SC-006 (Termal Limit İhlali) | `thermal_critical.yaml` | SIL |
| SC-007 (Uzun İletişim Kesintisi) | `long_comm_outage.yaml` | SIL |
| SC-009 (Observer Height) | `observer_height_sensitivity.yaml` | Analysis + SIL |

### 4.3 Nominal Görev Senaryosu

Bak: `simulation/scenarios/example_scenario.yaml` (bu belgede Ek A).

---

## 5. Hata Enjeksiyonu (Fault Injection)

### 5.1 Enjekte Edilebilir Hata Tipleri

| Hata ID | Tipi | Parametreler | FMEA Referansı |
|---------|------|--------------|----------------|
| FI-001 | Sensör gürültüsü artışı (IMU) | scale_factor × σ_noise (ör: 5×) | FMEA-RPN-NAV-001 |
| FI-002 | IMU bias kayması | bias_offset_dps (°/s) | FMEA-RPN-NAV-001 |
| FI-003 | LiDAR toz filtresi (dropout artışı) | dropout_pct (%) | FMEA-RPN-NAV-002 |
| FI-004 | Motor sıkışma (bir tekerlek) | wheel_id, stall_torque_nm | FMEA-RPN-MOT-001 |
| FI-005 | Ani batarya kapasitesi düşüşü | delta_soc_pct (örn: -20%) | FMEA-RPN-PWR-001 (RPN:30) |
| FI-006 | Link kaybı | duration_s | SC-002, SC-007 |
| FI-007 | Isıtıcı açık devre | heater_id | FMEA-RPN-THM-001 (RPN:20) |
| FI-008 | FDIR task freeze (watchdog testi) | freeze_duration_ms | FMEA-RPN-FDIR-001 |
| FI-009 | EKF yanlış başlatma | initial_cov_scale (ör: 10×) | FMEA-RPN-NAV-003 |
| FI-010 | PDU tek kanal kaybı | channel_id | redundancy_matrix SPF-001 |

### 5.2 FDIR Tepkisini Test Etme Yöntemi

```
Adım 1: Nominal senaryo çalıştır → baseline oluştur (tüm metrikler)
Adım 2: Hata enjekte et (FI-XXX parametreleri ile)
Adım 3: FDIR tepki süresini ölç:
         detection_latency_ms ≤ kabul kriteri (SC-004: < 5s)
Adım 4: Durum geçişi doğrulaması:
         güvenlik_durum_geçişi = beklenen_geçiş (ör: NOMINAL → CAUTION)
Adım 5: Kurtarma testi:
         recovery_süresi ≤ kabul kriteri
Adım 6: Sonuç kaydı: hata_enjeksiyonu / FDIR_tepkisi / kurtarma / metrikler
```

**FDIR Test Metrikleri:**

| Metrik | Kabul Kriteri | Kaynak |
|--------|---------------|--------|
| Lokalizasyon kaybı tespit süresi | < 5 s | SC-004 |
| HC-006 ihlali RETURN_REQUIRED geçiş süresi | < 5 s | SC-003 |
| Termal kritik RETURN_REQUIRED geçiş süresi | < 5 s | SC-006 |
| Motor sıkışma tespit süresi | < 500 ms | FMEA-RPN-MOT-001 |
| Batarya anomali tespit süresi | < 2 s | FMEA-RPN-PWR-001 |
| FDIR HW watchdog kick miss → reset | < 30 s | SAFETY_STATE_MACHINE §3.1 |

### 5.3 Regresyon Test Suite'i (Her PR)

Her pull request CI pipeline'ında otomatik çalışan test suite'i:

```yaml
# regression_test_suite.yaml — CI tetiklemeli
test_suite: "LUNA-AI Regression Tests v1.0"
trigger: "every_PR"
timeout_minutes: TBD-SIM-011   # §10 CI altyapısı kapasitesine göre

test_cases:
  - id: "RT-001"
    scenario: "nominal_surface_exploration.yaml"
    fault_injection: none
    expected_result: "success"
    max_duration_s: TBD-SIM-012

  - id: "RT-002"
    scenario: "psr_energy_emergency.yaml"
    fault_injection: "FI-005"   # Ani SoC düşüşü
    expected_result: "RETURN_REQUIRED_triggered"
    acceptance: "detection_latency < 5s"

  - id: "RT-003"
    scenario: "localization_loss_recovery.yaml"
    fault_injection: "FI-001"   # IMU gürültü artışı
    expected_result: "CAUTION_then_recovery OR RETURN_REQUIRED"
    acceptance: "FDIR_state_matches_expected"

  - id: "RT-004"
    scenario: "comm_loss_psr.yaml"
    fault_injection: "FI-006"   # Link kaybı
    expected_result: "RETURN_REQUIRED_triggered"
    acceptance: "pre_planned_abort_activated"

  - id: "RT-005"
    scenario: "thermal_critical.yaml"
    fault_injection: "FI-007"   # Isıtıcı açık devre
    expected_result: "CAUTION_then_RETURN_REQUIRED"
    acceptance: "heater_fallback_activated"

  - id: "RT-006"
    scenario: "nominal_surface_exploration.yaml"
    fault_injection: "FI-008"   # FDIR task freeze
    expected_result: "HW_watchdog_reset"
    acceptance: "system_reboots_to_CAUTION_in_30s"

metrics_collected:
  - safety_state_transitions
  - fdir_detection_latency_ms
  - recovery_time_ms
  - soc_min_pct
  - nav_uncertainty_max_m
  - thermal_min_temp_c
```

---

## 6. SIL/HIL Stratejisi

### 6.1 SIL (Software-in-the-Loop) — P1 Aşaması

SIL'de tüm araç yazılımı konak bilgisayarda çalışır; donanım yoktur. Çevresel ve araç modelleri bu belgede tanımlanmıştır.

**SIL'de önce yürütülecek modüller:**

| Modül | SIL Önceliği | Neden SIL Önce |
|-------|--------------|----------------|
| FDIR durum makinesi | P1 — kritik | Formal doğrulama başlamadan HIL anlamlı değil |
| Navigasyon EKF | P1 — kritik | Sensör füzyon algoritması donanımdan bağımsız |
| Global planner (rota) | P1 | Hesaplama ağırlıklı; donanım bağımsız |
| Power management mantığı | P1 | Enerji bütçe hesapları donanım bağımsız |
| Thermal management mantığı | P1 | Kontrol döngüsü algoritmik |
| Mission executive | P1 | Durum mantığı; ICD uyumluluğu |
| Senaryo regresyon testleri | P1 | Her PR'da SIL ile çalışır |

### 6.2 HIL (Hardware-in-the-Loop) — P2/P3 Aşaması

HIL'de gerçek araç bilgisayarı (OBC + Navigasyon işlemcisi) simülatör ile gerçek zamanlı arayüzler üzerinden bağlanır.

**HIL gerektiren modüller:**

| Modül | HIL Gerekçesi | P2/P3 |
|-------|---------------|-------|
| FDIR donanım watchdog | HW timer bağımsızlığı yalnızca gerçek HW'da test edilebilir | P2 |
| FreeRTOS görev önceliklendirme | Gerçek RTOS zamanlama testleri | P2 |
| IMU sensör arayüzü (SPI) | Gerçek sensör gürültüsü + timing | P2 |
| Motor sürücü kontrol döngüsü | Gerçek CAN bus latency | P2 |
| RF haberleşme zinciri | Gerçek CCSDS paket iletimi | P3 |
| Güç dağıtım arayüzü (I2C/CAN) | Gerçek PDU komut gecikmesi | P3 |
| Termal ısıtıcı donanım | Failback devre aktivasyon testi | P3 |

**HIL Arayüz Köprüsü:**

```
SIL/HIL Bridge (simulation/digital-twin/sil_hil_bridge):
  - Simülatör sensör çıktıları → Araç HW sensör arayüz formatına çevrilir
  - Araç HW aktuatör komutları → Simülatör model girişlerine çevrilir
  - Timing: 50 ms adım senkronizasyonu (ayarlanabilir)
  - Protokol: TBD (§10 OBC arayüzü belirlendikten sonra)
```

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent C, C3 görevi |
