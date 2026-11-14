# status: draft
# owner: Agent C
# depends_on: [docs/qar/QAR_TABLE.md, tests/acceptance_criteria.md, simulation/simulator_design.md, simulation/scenarios/example_scenario.yaml, docs/adr/FMEA_KRITIK_MODULLER.md, infrastructure/risk_register.md]
# open_items: [TBD değerler §10 araç verisi bekleniyor; HIL test setüpü P2 kapısına bağlı; FI referansları simulation/simulator_design.md §5 ile tutarlı tutulacak]

# Doğrulama ve Test Stratejisi — LUNA-AI v1.0

**Belge ID:** LUNA-AI-TEST-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı Belgeler:** LUNA-AI-QAR-001, tests/acceptance_criteria.md, LUNA-AI-FMEA-001, LUNA-AI-SIM-001

---

## Doğrulama Yöntemi Tanımları

| Kod | Yöntem | Açıklama |
|-----|--------|----------|
| **A** | Analysis | Analitik veya matematiksel doğrulama; referans hesap veya model karşılaştırması |
| **T** | Test | Çalışma zamanı ölçümü; gerçek veya simüle sistem üzerinde sayısal hedef ölçümü |
| **I** | Inspection | Kod/tasarım gözden geçirmesi; mimari inceleme veya bağımlılık analizi |
| **D** | Demonstration | Sistematik gösterim; end-to-end senaryo çalıştırma |

## Test Ortamı Tanımları

| Kod | Ortam | Açıklama |
|-----|-------|----------|
| **UT** | Unit Test (pytest) | Modül izole; bağımlılıklar mock/stub |
| **IT** | Integration Test | İki veya daha fazla modül birlikte; FreeRTOS gerektirmez |
| **SIL** | Software-in-the-Loop | Tüm yazılım konak bilgisayarda; ortam + araç modeli simüle |
| **HIL** | Hardware-in-the-Loop | Gerçek OBC + sensörler; simülatör çevre sağlar |
| **FT** | Field Test | Gerçek araç + gerçek ay yüzeyi (P3+ sonrası) |
| **TVAC** | Termal Vakum Testi | Gerçek sıcaklık/vakum ortamı |

---

## QAR Doğrulama Tablosu

### FDIR — Arıza Tespit, İzolasyon ve Kurtarma

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| FDIR-001 | FDIR | Anomali Tespit Süresi | < 50 ms (P95) | T — FI-001..010 anomali enjeksiyonu; zaman damgası farkı ölçümü | SIL (RT-002..006), HIL (P3) | 95. yüzdelik ≤ 50 ms; sıfır tespit atlaması kritik hatalar için (FDIR-004 ile çapraz) | safety/fdir |
| FDIR-002 | FDIR | Recovery Karar Süresi | < 500 ms anomali tespitinden itibaren | T — anomali tespit zaman damgası → `abort_signal=true` [ICD-004] zaman damgası farkı | SIL (RT-002..006), HIL (P3) | %95 oranında ≤ 500 ms; `fdir_confidence` ≥ 80 | safety/fdir |
| FDIR-003 | FDIR | Yanlış Pozitif Oranı | < %1 nominal operasyon saati başına | T — 100 saatlik nominal SIL koşusu; false alarm sayımı | SIL (RT-001 extended) | Toplam false alarm / toplam nominal saat < 0.01 | safety/fdir |
| FDIR-004 | FDIR | Yanlış Negatif Oranı | < %0.1 kritik hatalar için sıfır hedef | T — Her FMEA-top-10 hata modu için 50 tekrar; FDIR tespit oranı | SIL (RT-002..006 + ek), HIL (P3-AC-02) | Her kritik hata modunda tespit oranı = %100 | safety/fdir |
| FDIR-005 | FDIR | Durum Makinesi Geçiş Tutarlılığı | %100 deterministik | A + T — TLA+ formal doğrulama + 1000 tekrarlı SIL testi aynı girdi = aynı geçiş | UT (P0-AC-03), SIL | Formal doğrulama: invariant ihlali yok; 1000 test: sıfır tutarsız geçiş | safety/fdir |

### NAV — Navigasyon

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| NAV-001 | Navigasyon | Konum Doğruluğu (düz arazi) | < 0.5 m RMS | T — bilinen DEM referans noktaları üzerinde 50 ölçüm; EKF çıktısı vs referans | SIL (P1-AC-04), HIL (P3-AC-01) | σ_pos < 0.5 m RMS, %95 güven aralığında | vehicle/localization |
| NAV-002 | Navigasyon | Yönelim Doğruluğu | < 0.5° RMS (yaw/pitch/roll) | T — referans yönelim karşılaştırması; 100 örnek | SIL, HIL | σ_yaw, σ_pitch, σ_roll < 0.5° RMS | vehicle/localization |
| NAV-003 | Navigasyon | Konum Güncelleme Frekansı | ≥ 10 Hz hareket, ≥ 1 Hz dur-bekle | T — ICD-003 `vehicle_pose` mesaj zaman damgası analizi | UT, SIL | Hareket halinde: mesajlar arası dt ≤ 100 ms; dur-bekle: dt ≤ 1 s | vehicle/localization |
| NAV-004 | Navigasyon | Lokalizasyon Kayıp Tespiti | < 2 s (EKF ıraksama → alarm) | T — FI-001/FI-009 enjeksiyonu; tespit zaman damgası ölçümü | SIL (RT-003/CT-005), HIL | 20 ıraksama senaryosunun tümünde ≤ 2 s; sıfır tespit atlaması | vehicle/localization |
| NAV-005 | Navigasyon | Dead-Reckoning Kayması | < 2 m/dak (IMU-only) | T — FI-001 (IMU gürültü artışı) ile bilinen yol üzerinde kapalı döngü ölçüm | SIL | 1 dakika dead-reckoning sonrası kümülatif hata < 2 m | vehicle/localization |
| NAV-006 | Navigasyon | PSR İçi Navigasyon Doğruluğu | < 1.0 m RMS (görsel landmark azaldığında) | T — 20 PSR traversi senaryosu; LiDAR-only veya IMU+odometry modu | SIL (CT-005, PSR senaryoları) | σ_pos < 1.0 m RMS, PSR içinde landmark eşleşmesi olmaksızın | vehicle/localization |

### PLAN — Görev Planlayıcı

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| PLAN-001 | Görev Planlayıcı | Global Rota Hesaplama Süresi | < 60 s (500m yol, A*) | T — 10 farklı arazi profili; ortalama ve P99 hesaplama süresi | SIL (P2-AC-01) | %95 oranında < 60 s; P99 < 90 s | autonomy/global-planner |
| PLAN-002 | Görev Planlayıcı | Replanning Süresi | < 30 s (anlık engel sonrası) | T — SIL engel enjeksiyonu → replanning tamamlanma süresi; 50 senaryo | SIL (P2-AC-02, CT-003) | %95 oranında < 30 s | autonomy/replanner |
| PLAN-003 | Görev Planlayıcı | Enerji Bütçe Tahmin Hatası | < %10 (planlanan vs gerçekleşen) | T — 20 nominal görev koşusu; plan_energy vs sim_energy karşılaştırması | SIL (CT-002), Dijital İkiz | |plan_energy - actual_energy| / plan_energy × 100 < %10 | power + autonomy |
| PLAN-004 | Görev Planlayıcı | PSR Giriş Koşulu Değerlendirme Süresi | < 10 s | T — 50 PSR giriş senaryosu; karar üretme süresi ölçümü | SIL | %100 senaryoda < 10 s | autonomy/global-planner |
| PLAN-005 | Görev Planlayıcı | Dönüş Tetikleyici Hesaplama Frekansı | ≥ 1 Hz (sürekli dönüş marjı izleme) | T — `estimated_return_soc_pct` güncelleme zaman damgası analizi [ICD-001] | UT, SIL | Güncelleme aralığı ≤ 1 s her zaman | power |

### PWR — Güç Yönetimi

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| PWR-001 | Güç Yönetimi | Min. Dönüş SoC Rezervi | ≥ %15 (safe haven kapısında) | T — Her görev koşusunda safe haven ulaşımında SoC kaydı | SIL (P2-AC-04, CT-002), HIL | SoC ≥ %15 safe haven kapısında; tek ihlal = başarısız | power |
| PWR-002 | Güç Yönetimi | Enerji Tahmin Hatası | < %10 (kalan süre/mesafe için) | T + A — Dijital ikiz: 50 görev senaryosu; tahmin vs gerçek kıyaslaması | SIL (CT-002), Dijital İkiz | Ortalama hata < %5; maks hata < %10 | power |
| PWR-003 | Güç Yönetimi | Yük Kesme Tepki Süresi (Kritik) | < 100 ms (komut → fiili kesim) | T — HIL: komut zaman damgası vs akım sensörü ölçümü; FI-010 (PDU testi) | HIL (P3) | %100 kritik kesim komutu ≤ 100 ms | power |
| PWR-004 | Güç Yönetimi | Yük Kesme Tepki Süresi (SURVIVAL) | < 10 ms (SURVIVAL modu opsiyonel yükler) | T — HIL: SURVIVAL geçişi → tüm opsiyonel yük kesim süresi | HIL (P3) | %100 SURVIVAL kesim ≤ 10 ms | power |
| PWR-005 | Güç Yönetimi | SoC Ölçüm Doğruluğu | ±TBD% (hedef: ±%2; kimyaya bağlı) | T — Kalibrasyon testi: bilinen kapasite Wh karşılaştırması; voltaj + Coulomb çift ölçüm | HIL, TVAC (P3) | |SoC_measured - SoC_true| ≤ TBD-BAT-002 bağımlı eşik | power |
| PWR-006 | Güç Yönetimi | Panel Verimliliği İzleme Periyodu | ≤ 10 s günceleme | T — `panel_power_w` mesaj zaman damgası analizi [ICD-001] | UT, SIL | Güncelleme aralığı ≤ 10 s her zaman | power |

### THM — Termal Yönetimi

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| THM-001 | Termal Yönetim | Sıcaklık İzleme Periyodu | ≤ 1 s (tüm kritik sensörler) | T — `thermal_state` güncelleme zaman damgası analizi [ICD-002]; tüm sensor_ids için | UT, SIL | Her kritik sensör: güncelleme aralığı ≤ 1 s | thermal |
| THM-002 | Termal Yönetim | Isıtıcı Aktivasyon Gecikmesi | < 5 s (komut → ısıtma başlangıcı) | T — HIL: sıcaklık eşik geçişi → ısıtıcı aktivasyon; FI-007 ile test | SIL (CT-006), HIL (P3) | %100 aktivasyon komutu ≤ 5 s | thermal |
| THM-003 | Termal Yönetim | Termal Kritik Tespit Süresi | < 2 s (eşik ihlali → FDIR alarmı) | T — FI-007 enjeksiyonu; tespit zaman damgası ölçümü | SIL (RT-005, CT-006), HIL | %100 kritik termal olay ≤ 2 s FDIR'a iletildi | thermal |
| THM-004 | Termal Yönetim | Min. Operasyon Sıcaklığı (Elektronik) | TBD-THM-001/003 — parça seçimine bağlı | T — TVAC: soğuk kalifikasyon testi | TVAC (P3) | Tüm bileşenler min sıcaklıkta nominal çalışıyor (TBD-THM-003 eşiği) | thermal |
| THM-005 | Termal Yönetim | Maks. Operasyon Sıcaklığı (Elektronik) | TBD-THM-001/003 — parça seçimine bağlı | T — TVAC: sıcak kalifikasyon testi | TVAC (P3) | Tüm bileşenler maks sıcaklıkta nominal çalışıyor (TBD-THM-003 eşiği) | thermal |

### COM — Haberleşme

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| COM-001 | Haberleşme | Komut İşleme Gecikmesi | < 500 ms (komut alındı → icra) | T — End-to-end gecikme ölçümü; 100 TC_IMMEDIATE + 100 TC_PLAN_UPLOAD | SIL (CT-004), HIL (P3) | %95 oranında ≤ 500 ms; TC_IMMEDIATE komutlar %100 ≤ 500 ms | communication |
| COM-002 | Haberleşme | Telemetri Güncelleme Periyodu (Nominal) | ≤ 10 s | T — ICD-006 downlink zaman damgası analizi; nominal güvenlik durumunda | SIL, HIL | Güncelleme aralığı ≤ 10 s, nominal koşullar | communication |
| COM-003 | Haberleşme | Telemetri Güncelleme Periyodu (Kritik Durum) | ≤ 1 s (CAUTION veya üstü) | T — Durum geçişi tetiklenince güncelleme frekansı kontrolü | SIL (CT-004), HIL | CAUTION+ durumda: güncelleme aralığı ≤ 1 s | communication |
| COM-004 | Haberleşme | Otonom Çalışma Süresi (Link Yok) | ≥ TBD-COM-002 saat | D — FI-006 link kaybı; SC-002/SC-007 senaryoları; araç pre-planned protokol | SIL (CT-004), HIL | Araç güvenlik sınırları içinde kaldı; pre-planned abort trigger'lar doğru tetiklendi | communication |
| COM-005 | Haberleşme | Komut Bütünlüğü (CRC) | %100 tek bit flip tespiti | T — 10.000 bozulmuş paket senaryosu; CRC hata tespiti oranı | UT, SIL | %100 hatalı paket reddedildi; sıfır hatalı paket kabul | communication |
| COM-006 | Haberleşme | Link Yeniden Bağlantı Süresi | < TBD-COM-003 dakika | T — SIL link simülasyonu: link penceresi tekrar açılınca bağlantı kurma süresi | SIL (CT-004) | %95 yeniden bağlantı ≤ TBD-COM-003; yer telemetrisi güncellendi | communication |

### SHV — Safe Haven

| Gereksinim ID | Modül | Nitelik | Sayısal Hedef | Doğrulama Yöntemi | Test Ortamı | Kabul Kriteri | Sorumlu |
|--------------|-------|---------|---------------|-------------------|-------------|---------------|---------|
| SHV-001 | Safe Haven | Min. Aydınlanma Süresi | ≥ TBD saat/gün (enerji yeterliliği) | A — SPICE orbital simülasyonu; seçili bölge aydınlanma analizi (AC-VAL-001..004) | Analysis + SIL | Seçili safe haven konumunda günlük aydınlanma ≥ enerji bütçesi gereksinimi | mission_intelligence |
| SHV-002 | Safe Haven | Min. Dönüş Enerjisi Rezervi | ≥ %15 SoC (safe haven kapısında) | T — Her görev koşusunda safe haven ulaşımında SoC kaydı (PWR-001 ile çakışır) | SIL, HIL | SoC ≥ %15; HC-006 ihlali = başarısız | power |
| SHV-003 | Safe Haven | Ulaşım Süresi (Nominal) | ≤ TBD dakika (maks uzaklık) | T — Navigasyon simülasyonu: en uzak görev noktasından nominal hız ile dönüş | SIL (CT-003) | %95 senaryoda ≤ TBD-TRV-001/TBD-TRV-002 bağımlı eşik | autonomy/global-planner |
| SHV-004 | Safe Haven | Ulaşım Süresi (SURVIVAL modu) | ≤ TBD dakika (minimum enerji rotası) | T — SURVIVAL modu simülasyonu; FI-005+FI-003 kombinasyonu | SIL (CT-007) | SURVIVAL modda araç safe haven'a ulaştı; SoC > 0% | autonomy/global-planner |
| SHV-005 | Safe Haven | Zemin Eğim Toleransı | ≤ TBD° (güvenli park) | A + T — Arazi haritası eğim analizi + araç kararlılık analizi | Analysis, SIL | Seçili safe haven konumlarında eğim ≤ HC-001 eğim limiti (TBD-TRV-002) | mission_intelligence |

---

## Kritik Test Senaryoları

Aşağıdaki 7 kritik test senaryosu QAR doğrulamasında önceliklidir. Her senaryo `simulation/simulator_design.md` §5'teki FI-* referansları ile bağlıdır.

### CT-001: FDIR Tepki Süresi — Anomali Enjeksiyonu

**Hedef QAR:** FDIR-001, FDIR-002, FDIR-004  
**Bağlı FI:** FI-001 (IMU gürültü), FI-005 (ani SoC düşüşü), FI-007 (ısıtıcı açık devre), FI-008 (FDIR task freeze)  
**Test Ortamı:** SIL (P1/P2), HIL (P3)

```
Prosedür:
1. Nominal SCN-001 baseline koşusunu çalıştır (RT-001).
2. Zaman t0'da FI-XXX enjekte et.
3. FDIR anomali tespit zaman damgasını (t1) kaydet.
4. FDIR abort_signal=true zaman damgasını (t2) kaydet [ICD-004].
5. Hesapla: detection_latency = t1 - t0; decision_latency = t2 - t1.
Kabul: detection_latency ≤ 50 ms (P95), decision_latency ≤ 500 ms (P95).
Tekrar: Her FI tipi için 50 bağımsız koşu.
Referans regresyon: RT-002, RT-005, RT-006.
```

### CT-002: Enerji Bütçesi Tahmin Doğruluğu — Simüle PSR Traversi

**Hedef QAR:** PLAN-003, PWR-001, PWR-002  
**Bağlı FI:** FI-005 (ani SoC düşüşü — worst-case)  
**Test Ortamı:** SIL (Dijital İkiz), SC-003

```
Prosedür:
1. PSR traversi senaryosu: giriş SoC %85, TBD mesafe PSR içi.
2. Planner'ın başlangıçta tahmin ettiği return_reserve_wh ve actual SoC safe haven kapısında kaydet.
3. Hesapla: tahmin_hatası = |tahmin - gerçek| / tahmin × 100%.
4. 20 bağımsız koşu (farklı arazi ve enerji tüketim varyasyonu).
Kabul: Ortalama tahmin hatası < %5; maks < %10.
         SoC safe haven kapısında ≥ %15 (PWR-001).
Referans regresyon: RT-002.
```

### CT-003: Safe Haven Seçimi Doğruluğu — Bilinen Optimum Karşılaştırma

**Hedef QAR:** SHV-001..005, PLAN-002  
**Bağlı FI:** Yok (arazi enjeksiyonu var)  
**Test Ortamı:** SIL (SC-005)

```
Prosedür:
1. Test senaryosu: Birincil safe haven rotası tıkandı (SC-005 — rota enjeksiyonu).
2. 7 kriter üzerinden aday safe haven'lar değerlendirilir.
3. Referans çözüm: Uzman elle hesaplanmış optimum safe haven koordinatı.
4. Sistem kararını referans çözümle karşılaştır.
5. 10 farklı engelleme konfigürasyonu + 7 kriterden 1 kriterin farklı ağırlıklı olduğu edge case'ler.
Kabul: Sistem seçimi referans ile %80+ örtüşüyor; HC ihlali içeren aday hiçbir zaman seçilmiyor.
Referans: operational_scenarios.md SC-005 §3 7-kriter listesi.
```

### CT-004: Haberleşme Kesikliğinde Otonom Davranış — Link Drop Simülasyonu

**Hedef QAR:** COM-001, COM-003, COM-004, COM-006  
**Bağlı FI:** FI-006 (link kaybı)  
**Test Ortamı:** SIL (SC-002, SC-007)

```
Prosedür — SURFACE_EXPLORATION senaryosu:
1. FI-006: Link t0'da kesildi. Süre: TBD-COM-002 uyarı eşiği / 2× uyarı eşiği / kritik eşik.
2. FDIR CAUTION tetikleyicisi tespit süresi kaydedilir.
3. Pre-planned abort trigger listesi (ABT-001..006) kontrol edilir.
4. Link geri gelince CAUTION → NOMINAL geçiş süresi kaydedilir.
Prosedür — PSR_OPS senaryosu:
5. PSR içinde FI-006 enjeksiyonu → RETURN_REQUIRED tetiklenmeli.
6. ACL dönüş rotası başlamalı; yer onayı beklenmemeli.
Kabul: Durum geçişleri SC-002 protokolüne uygun; araç pre-planned sınırlar dışına çıkmadı.
        Link geri gelince yer telemetrisi ≤ 1 s güncellendi (COM-003).
Referans regresyon: RT-004.
```

### CT-005: Lokalizasyon Kaybı Recovery — IMU Drift Enjeksiyonu

**Hedef QAR:** NAV-001, NAV-004, NAV-005, NAV-006  
**Bağlı FI:** FI-001 (IMU gürültü artışı), FI-002 (IMU bias kayması), FI-009 (EKF yanlış başlatma)  
**Test Ortamı:** SIL (SC-004), HIL (P3)

```
Prosedür:
1. Nominal gezinti sırasında FI-001 veya FI-002 enjekte et.
2. EKF kovaryans izle: uncertainty_m eşiği aştığında (> 1.0 m) FDIR bildirim süresi.
3. FDIR Detection → Isolation → Recovery adımlarını gözlemle.
4. Recovery başarılı: landmark arama → σ_pos < 0.5 m → NOMINAL dönüş.
5. Recovery başarısız: RETURN_REQUIRED tetiklenmeli; IMU-only navigasyon ile dönüş.
Kabul: Tespit ≤ 2 s (NAV-004); dead-reckoning kayması < 2 m/dak (NAV-005).
         CAUTION → RETURN_REQUIRED geçişi doğru tetiklendi (SC-004 adım 8).
Referans regresyon: RT-003.
```

### CT-006: PSR Traversi Termal Bütçe — Uzun Süreli Karanlık Simülasyonu

**Hedef QAR:** THM-001, THM-002, THM-003, SHV-001  
**Bağlı FI:** FI-007 (ısıtıcı açık devre — worst-case)  
**Test Ortamı:** SIL (SC-006, PSR termal senaryosu)

```
Prosedür:
1. PSR içinde araç TBD saat boyunca kalır (en uzun lunar gece simülasyonu).
2. Isıtıcılar nominal çalışıyor: sıcaklık profili izle.
3. t_mid: FI-007 enjeksiyonu (bir ısıtıcı arızası) → FDIR termal kritik tespit süresi.
4. Fallback ısıtıcı aktivasyonu → sıcaklık stabilizasyonu izle.
5. SoC en düşük noktası kaydedilir.
Kabul: Hiçbir kritik bileşen minimum çalışma sıcaklığının altına düşmedi.
         THM-003: Kritik tespit ≤ 2 s.
         THM-002: Fallback ısıtıcı aktivasyonu ≤ 5 s.
         SoC dönüş rezervi ≥ %15 korundu.
```

### CT-007: Çoklu Eş Zamanlı Hata — Combined Failure

**Hedef QAR:** FDIR-001..004, PWR-001, NAV-001, THM-003  
**Bağlı FI:** FI-005 + FI-001 + FI-006 kombinasyonu  
**Bağlı RPN:** FMEA-RPN-PWR-001 (30) + FMEA-RPN-NAV-001 (24) kombinasyon  
**Test Ortamı:** SIL (RT-002 + RT-003 + RT-004 kombinasyonu)

```
Prosedür:
1. Nominal PSR operasyonu.
2. t=0: FI-001 (IMU gürültü artışı 3×)
   t=30s: FI-006 (link kaybı)
   t=60s: FI-005 (ani SoC %20 düşüşü)
3. FDIR en yüksek öncelikli tetikleyiciyi doğru seçmeli:
   SoC düşüşü (HC-006) → RETURN_REQUIRED (en kritik).
4. Çoklu hata altında FDIR tek tutarlı karar vermeli.
5. Araç abort başlatmalı ve safe haven'a dönmeli.
Kabul: FDIR çoklu tetikleyici altında deterministik davranıyor (FDIR-005).
         En yüksek öncelikli tetikleyici seçildi (SoC > link > nav, bağlama göre).
         Araç safe haven'a SoC ≥ %15 ile ulaştı.
Referans regresyon: RT-002, RT-003, RT-004 (ayrı ayrı); bu senaryo ek CT.
```

---

## Regresyon Test Suite

Her PR'da otomatik çalışan minimum test seti.

### Mevcut Unit Test Referansı

`tests/unit/test_models.py` — 29 unit test, aşağıdaki alanları kapsar:

| Test Grubu | Kapsam | QAR İlişkisi |
|------------|--------|--------------|
| `ScoringWeights` toplamı 1.0 | Hedef puanlama tutarlılığı | PLAN doğrulama tabanı |
| `HardConstraintEvaluator` pass/fail | HC-001..015 motoru | P0-AC-02 (30 HC testi) |
| `DataProductMetadata` zorunlu alanlar | temporal_class, resolution_m | P0-AC-06, P0-AC-07 |
| `LandingSiteCandidate` yapısı | Alan kısıtları | SHV doğrulama tabanı |
| `BoundingBox` oluşturma | Koordinat tutarlılığı | NAV doğrulama tabanı |
| `CraterRecord` oluşturma | Veri modeli bütünlüğü | Bilimsel veri platform |

**Hedef:** Mevcut 29 test %100 geçiyor; her PR sonrası bu sayı azalmaz.

### PR Regresyon Suite Tanımı

| Seviye | Test | Ortam | Süre (tahmini) | Tetikleyici |
|--------|------|-------|----------------|-------------|
| L1 — Her PR | 29 mevcut unit test | UT (pytest) | < 2 dak | Her commit |
| L1 — Her PR | P0-AC-01..07 (ICD şema, HC motoru, durum makinesi) | UT | < 5 dak | Her commit |
| L2 — Merge önce | RT-001 (nominal SCN-001 koşusu) | SIL | < 15 dak | PR merge onayı |
| L2 — Merge önce | RT-002 (PSR enerji düşüşü, FI-005) | SIL | < 10 dak | PR merge onayı |
| L2 — Merge önce | RT-003 (lokalizasyon kaybı, FI-001) | SIL | < 10 dak | PR merge onayı |
| L2 — Merge önce | RT-004 (link kaybı PSR, FI-006) | SIL | < 10 dak | PR merge onayı |
| L2 — Merge önce | RT-005 (termal kritik, FI-007) | SIL | < 10 dak | PR merge onayı |
| L2 — Merge önce | RT-006 (FDIR watchdog freeze, FI-008) | SIL | < 5 dak | PR merge onayı |
| L3 — Haftalık | CT-001..007 tam senaryo seti | SIL | < 2 saat | Haftalık CI |
| L4 — Faz kapısı | P0-AC..P2-AC tam set | SIL + IT | < 4 saat | Faz geçiş kapısı |

### Kabul / Red Kriterleri

| Durum | Kriter | Sonuç |
|-------|--------|-------|
| **Geçer** | L1 + L2 testlerin tümü yeşil | PR merge onayı verilebilir |
| **Kırmızı bayrak** | Herhangi bir L1 testi başarısız | PR merge yapılamaz; hata düzeltilmeli |
| **Kırmızı bayrak** | Herhangi bir L2 FDIR/güvenlik testi başarısız | PR merge yapılamaz |
| **Sarı bayrak** | L2 performans testi (PLAN-001/002) eşiği aştı | Kabul edilebilir; risk kaydına eklenir |
| **Faz kapı engeli** | L4 herhangi AC başarısız | Faz geçişi yapılamaz |

### Metrik Toplama

Her CI koşusunda şu metrikler loglanır:

```yaml
regression_metrics:
  - safety_state_transitions_correct: bool
  - fdir_detection_latency_p95_ms: float
  - fdir_decision_latency_p95_ms: float
  - soc_min_pct: float
  - nav_uncertainty_max_m: float
  - thermal_min_temp_c: float
  - plan_energy_error_pct: float
  - waypoints_reached_count: int
  - false_alarm_count: int
```

---

## Repo Doğrulama Kabul Kriterleri (AC-VAL-001..005)

Kaynak: `tests/acceptance_criteria.md` §Repo Doğrulama Kabul Kriterleri (B4-EK).

| Kriter ID | Kriter | Kaynak | Hedef | Test Ortamı | QAR İlişkisi |
|-----------|--------|--------|-------|-------------|--------------|
| AC-VAL-001 | Güneş/Dünya açıları JPL Horizons ile uyumlu | JPL Horizons | ±0.001° içinde | Analysis | SHV-001, COM-004 (link penceresi) |
| AC-VAL-002 | Aydınlanma oranı NASA GSFC ile korelasyon | NASA GSFC | r ≥ 0.988, RMS ≤ 2.7 puan | Analysis + SIL | SHV-001, P1-AC-01 |
| AC-VAL-003 | Dünya görünürlüğü NASA GSFC ile korelasyon | NASA GSFC | r ≥ 0.993 | Analysis | COM-004, RR-014 |
| AC-VAL-004 | Shackleton ridge aydınlanma: 2m gözlem %92.29, 10m %95.69 | Gläser et al. (2014) | ±0.05 puan | Analysis | P1-AC-01, SHV-001 |
| AC-VAL-005 | Çözünürlük doğrulama raporu: 80m vs 20m vs 300m fark analizi | B3-EK RR-011/015 | Rapor teslim + onay | Analysis | NAV-006, PLAN-001 |

**Faz uygulaması:** AC-VAL-001..004 P1 kapısı koşuludur. AC-VAL-005 P1 çıkış raporu kapsamındadır.

---

## Doğrulama Traceability Matrisi (Özet)

| Doğrulama Yöntemi | Kapsanan QAR Sayısı | Test Ortamı | Faz |
|-------------------|--------------------|-----------|----|
| Analysis (A) | SHV-001, SHV-005, AC-VAL-001..005 | — | P1 |
| Unit Test (T/UT) | FDIR-005, NAV-003, PWR-005/006, THM-001, COM-002/005 | pytest | P0 |
| Integration Test (IT) | P0-AC-01..07 kombinasyon | IT | P0 |
| SIL (T/D/SIL) | FDIR-001..004, NAV-001/004..006, PLAN-001..005, PWR-001..003, THM-002/003, COM-001/003/004/006, SHV-002..004 | SIL | P1/P2 |
| HIL (T/HIL) | FDIR-001/002, NAV-001, PWR-003/004, THM-004/005, COM-001 | HIL | P3 |
| TVAC (T) | THM-004, THM-005, PWR-005 | TVAC | P3 |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent C, C4 görevi; 30 QAR maddesi, 7 kritik senaryo, regresyon suite |
