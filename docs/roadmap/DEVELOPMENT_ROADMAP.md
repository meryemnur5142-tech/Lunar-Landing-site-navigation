# status: draft
# owner: Agent C
# depends_on: [config/tbd_register.md, tests/acceptance_criteria.md, docs/qar/QAR_TABLE.md, docs/adr/FMEA_KRITIK_MODULLER.md, infrastructure/risk_register.md, tests/verification_strategy.md]
# open_items: [P2/P3 tahmini süreler §10 araç verisi ve Agent D çalışmasının hızına bağlı; TBD kapıları config/tbd_register.md'den izleniyor]

# LUNA-AI Geliştirme Yol Haritası — P0–P3

**Belge ID:** LUNA-AI-ROAD-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı Belgeler:** LUNA-AI-TEST-001 (Doğrulama Stratejisi), tests/acceptance_criteria.md, config/tbd_register.md

---

## Yol Haritası Özeti

```
Ön Aşama  ✅ TAMAMLANDI
P0        ✅ TAMAMLANDI (kısmen — lunar-navigator submodule ⏳)
P1        🔄 DEVAM EDİYOR — Agent B/C çıktıları teslim edildi; ODE/SPICE entegrasyon ⏳
P2        🔄 DEVAM EDİYOR — Agent D (feature/faz2-otonomi branch'inde)
P3        🔲 BAŞLAMADI — §10 araç verisi bekleniyor
```

**Önemli Not:** P2 → P3 kapısı 6 kritik TBD'nin kapanmasını zorunlu kılar. Bu TBD'ler §10 araç mühendisliği verisi olmadan kapanamaz.

---

## Ön Aşama — Konsept ve Tasarım Temeli ✅ TAMAMLANDI

**Durum:** Tamamlandı  
**Dal:** main (merge edildi)

### Tamamlanan Çıktılar

| Çıktı | Belge | Durum |
|-------|-------|-------|
| Operasyonel Konsept (ConOps) | `docs/conops/CONOPS.md` | ✅ |
| Kalite Nitelik Gereksinimleri (QAR) | `docs/qar/QAR_TABLE.md` (30 madde) | ✅ |
| Kritik Modüller FMEA | `docs/adr/FMEA_KRITIK_MODULLER.md` (top-10 RPN) | ✅ |
| Mimari Karar Kayıtları | `docs/adr/ADR-001..006` | ✅ |
| Hard Constraints Kataloğu | `domain/mission/constraints/hard_constraints_catalog.md` (18 HC) | ✅ |
| Faz Durum Makinesi | `domain/mission/phase_state_machine.md` | ✅ |
| Güvenlik Durum Makinesi Tasarımı | `docs/architecture/SAFETY_STATE_MACHINE.md` | ✅ |
| ICD Şablonları | `docs/architecture/ICD_TEMPLATES.md` (ICD-001..006) | ✅ |
| Emniyet Bütçesi | `safety/safety_budget.md` | ✅ |
| Otonomi Matrisi | `autonomy/autonomy_matrix.md` | ✅ |
| Risk Kaydı | `infrastructure/risk_register.md` (15 risk) | ✅ |
| Operasyonel Senaryolar | `simulation/scenarios/operational_scenarios.md` (SC-001..009) | ✅ |
| Kabul Kriterleri | `tests/acceptance_criteria.md` (P0-P3 AC + AC-VAL-001..005) | ✅ |
| TBD Kaydı | `config/tbd_register.md` (44+ TBD) | ✅ |

---

## P0 — Mimari Temel ✅ BÜYÜK ÖLÇÜDE TAMAMLANDI

**Durum:** Büyük ölçüde tamamlandı; bir kalemi beklemede  
**Dal:** main (merge edildi)  
**Kabul Kriterleri:** `tests/acceptance_criteria.md` P0-AC-01..07

### Tamamlanan Çıktılar

| Çıktı | Belge / Modül | Durum |
|-------|---------------|-------|
| ICD Şemaları (10 JSON Schema) | `interfaces/schemas/*.schema.yaml` | ✅ |
| Python TypedDict + JSON Schema uyum | `interfaces/v1/energy_state.py`, `thermal_state.py`, `vehicle_pose.py` | ✅ |
| Yedeklilik Matrisi | `docs/architecture/redundancy_matrix.md` | ✅ |
| Güvenlik Durum Makinesi (PlantUML) | `docs/architecture/PLANTUML_DIAGRAMS.md` (Diyagram 5) | ✅ |
| Hard Constraints Python motoru | `mission_intelligence/constraints/hard_constraints.py` | ✅ |
| Enerji durum sözleşmesi | `interfaces/v1/energy_state.py` | ✅ |
| Termal durum sözleşmesi | `interfaces/v1/thermal_state.py` | ✅ |
| Araç poz sözleşmesi | `interfaces/v1/vehicle_pose.py` | ✅ |
| Bileşen + Dağıtım + Sekans Diyagramları | `docs/architecture/PLANTUML_DIAGRAMS.md` (Diyagram 1-4) | ✅ |

### Bekleyen Kalem

| Kalem | Bağımlılık | Durum |
|-------|-----------|-------|
| lunar-navigator submodule bağlantısı | TBD-REPO-001: submodule vs referans dizin kararı | ⏳ |

### Giriş Koşulları (Karşılandı)

- Ön aşama tüm çıktıları teslim edildi.
- Proje bağlamı ve teknik kısıtlamalar belgelendi.

### Çıkış Kriterleri

- ✅ P0-AC-01..07 unit testleri yeşil (mevcut 29 unit test + ICD şema testleri)
- ✅ Tüm modül arayüzleri ICD şemasına uygun
- ✅ HC motoru HC-001..015 kümesini değerlendiriyor
- ⏳ lunar-navigator entegrasyon kararı (TBD-REPO-001 kapandıktan sonra)

### Kritik Bağımlılıklar

| Bağımlılık | Kaynak | Durum |
|-----------|--------|-------|
| TBD-REPO-001 (submodule vs referans) | Proje kararı | ⏳ AÇIK |

---

## P1 — Bilimsel Platform 🔄 DEVAM EDİYOR

**Durum:** Çekirdek çıktılar teslim edildi; entegrasyon kalemleri beklemede  
**Dal:** feature/faz1-tamamlama (bu branch)  
**Kabul Kriterleri:** `tests/acceptance_criteria.md` P1-AC-01..06  
**Tahmini Süre:** §10 bağımsız: 2–4 hafta tamamlama; §10 bağımlı: §10 sonrası

### Tamamlanan Çıktılar

| Çıktı | Belge / Modül | Durum |
|-------|---------------|-------|
| Veri alım hattı taslakları | `data-platform/ingestion/base_ingestor.py` | ✅ |
| Terrain analyzer | `data-platform/processing/terrain_analyzer.py` | ✅ |
| Krater aday filtreleme + sıralama | `mission_intelligence/scoring/scorer.py`, `hard_constraints.py` | ✅ |
| Domain modelleri | `domain/crater/models.py`, `domain/environment/models.py`, `domain/mission/models.py` | ✅ |
| Dijital İkiz temel altyapısı | `simulation/simulator_design.md` | ✅ |
| Senaryo çalıştırıcısı tasarımı | `simulation/simulator_design.md` §4 | ✅ |
| Örnek senaryo YAML | `simulation/scenarios/example_scenario.yaml` | ✅ |
| Doğrulama ve Test Stratejisi | `tests/verification_strategy.md` | ✅ |

### Bekleyen Kalemler

| Kalem | Bağımlılık | Öncelik |
|-------|-----------|---------|
| ODE API gerçek bağlantısı (LOLAIngestor, ShadowCamIngestor tam impl.) | Ağ erişimi + API key | P-HIGH |
| SPICE kernel entegrasyonu (aydınlanma modeli tam koşu) | TBD-TIME-001 (görev tarihi) | P-CRIT |
| AC-VAL-001..004 aydınlanma doğrulaması (JPL/NASA GSFC karşılaştırması) | SPICE kernel | P-CRIT |
| AC-VAL-005 çözünürlük raporu (80m vs 300m) | ODE + SPICE | P-HIGH |
| SIL baseline koşusu (RT-001 ilk koşu) | Simülatör impl. tamamlanması | P-HIGH |
| RR-002, RR-003, RR-004, RR-007 azaltma doğrulaması (P1-AC-06) | SIL hazır | P-HIGH |

### Giriş Koşulları

- ✅ P0 çıkış kriterleri büyük ölçüde karşılandı.
- ✅ Domain modelleri ve ICD şemaları kullanılabilir.

### Çıkış Kriterleri

| Kriter | Yöntem | Hedef |
|--------|--------|-------|
| P1-AC-01: Aydınlanma modeli JPL/NASA GSFC ile doğrulandı | Analysis | AC-VAL-001..004 |
| P1-AC-02: HC filtreleme %100 doğruluk | SIL (100 test adayı) | Sıfır yanlış eleme |
| P1-AC-03: Enerji-termal simülatör §10 profili ile ±TBD% | Analysis + SIL | TBD-THM-002 kapandıktan sonra |
| P1-AC-04: Dijital ikiz SC-001 nominal koşu tamamlıyor | SIL (RT-001) | Waypoint ±1m, SoC ≥ %15 |
| P1-AC-05: temporal_class karışma = sıfır | UT | %100 kapsam |
| P1-AC-06: RR-002/003/004/007 azaltma doğrulandı | SIL | Her risk için azaltma gösterildi |
| AC-VAL-005: Çözünürlük raporu teslim | Analysis | Fark analizi onaylandı |

### Kritik Bağımlılıklar

| Bağımlılık | TBD ID | Durum |
|-----------|--------|-------|
| Görev başlangıç tarihi (SPICE için) | TBD-TIME-001 | P-CRIT ⏳ |
| Araç termal model | TBD-THM-001/002 | P-CRIT ⏳ |

### P1 → P2 Kapı TBD'leri

Aşağıdaki TBD'ler P1 kapısı açılmadan önce kapanmalıdır:

| TBD ID | Parametre | Öncelik |
|--------|-----------|---------|
| TBD-TIME-001 | Görev başlangıç tarihi (UTC) | P-CRIT |
| TBD-THM-001 | Termal kütle + yalıtım konfigürasyonu | P-CRIT |

---

## P2 — Otonomi Prototipi 🔄 DEVAM EDİYOR (Agent D)

**Durum:** Agent D, `feature/faz2-otonomi` branch'inde çalışıyor  
**Dal:** feature/faz2-otonomi (ayrı branch)  
**Kabul Kriterleri:** `tests/acceptance_criteria.md` P2-AC-01..08  
**Tahmini Süre:** 4–8 hafta (P1 kapısı açıldıktan sonra)

### Devam Eden Çalışmalar (Agent D)

| Kalem | Modül | Durum |
|-------|-------|-------|
| Global planner (A* tabanlı rota) | `autonomy/global-planner/` | 🔄 |
| Local planner (engel kaçınma) | `autonomy/local-planner/` | 🔄 |
| FDIR implementasyonu | `safety/fdir/` | 🔄 |
| Navigasyon + EKF sensör füzyonu | `vehicle/localization/` | 🔄 |
| Mission executive | `autonomy/mission-executive/` | 🔄 |

### Bekleyen Kalemler (P2 kapsamında)

| Kalem | Bağımlılık | Öncelik |
|-------|-----------|---------|
| Haberleşme mimarisi (CCSDS impl.) | TBD-COM-001 | P-CRIT |
| FreeRTOS görev önceliklendirme | §10 OBC seçimi | P-CRIT |
| SIL regresyon suite ilk tam koşu (RT-001..006) | Tüm P2 modülleri hazır | P-HIGH |
| CT-001..007 kritik test senaryoları | SIL hazır | P-HIGH |
| HIL köprü tasarımı (SIL/HIL bridge) | §10 OBC arayüzü | P-MED |

### Giriş Koşulları

- P1 çıkış kriterleri tümü yeşil.
- Aşağıdaki P-CRIT TBD'ler kapalı:

| TBD ID | Parametre |
|--------|-----------|
| TBD-BAT-002 | Batarya kimyası |
| TBD-SNS-001 | Sensör paketi |
| TBD-SNS-002 | IMU gürültü parametreleri |
| TBD-SNS-003 | Odometry hata parametreleri |
| TBD-COM-001 | İletişim donanımı |
| TBD-ENE-002 | HC-006 dönüş rezervi eşiği (Wh) |

### Çıkış Kriterleri

| Kriter | Yöntem | Hedef |
|--------|--------|-------|
| P2-AC-01: Global planner < 60s | SIL | %95 başarı |
| P2-AC-02: Replanning < 30s | SIL | %95 başarı |
| P2-AC-03: SC-002 (link kaybı) SIL geçiyor | SIL | Her iki senaryo |
| P2-AC-04: SC-003 (enerji düşüşü) SIL geçiyor | SIL | FDIR 5s, Planner 30s |
| P2-AC-05: SC-004 (lokalizasyon kaybı) SIL | SIL | Detection-Isolation-Recovery |
| P2-AC-06: SC-006 (termal ihlal) SIL | SIL | RETURN_REQUIRED 5s |
| P2-AC-07: 10 kritik senaryo × FDIR tepki | SIL (CT-001..007) | %100 uyum |
| P2-AC-08: Power Mgmt → Planner akış yönü | SIL + Code review | Tek yönlü bağımlılık |

### P2 → P3 Kapı TBD'leri

| TBD ID | Parametre | Öncelik |
|--------|-----------|---------|
| TBD-BAT-002 | Batarya kimyası | P-CRIT |
| TBD-SNS-001 | Sensör paketi | P-CRIT |
| TBD-SNS-002 | IMU gürültü | P-CRIT |
| TBD-SNS-003 | Odometry hata | P-CRIT |
| TBD-COM-001 | İletişim donanımı | P-CRIT |
| TBD-ENE-002 | HC-006 dönüş rezervi eşiği | P-CRIT |

---

## P3 — Araç Entegrasyonu 🔲 BAŞLAMADI

**Durum:** §10 araç verisi bekleniyor  
**Dal:** feature/faz3-entegrasyon (henüz oluşturulmadı)  
**Kabul Kriterleri:** `tests/acceptance_criteria.md` P3-AC-01..05  
**Tahmini Süre:** 8–16 hafta (§10 ve P2 kapısı açıldıktan sonra)

### Planlanan Çalışmalar

| Kalem | Modül | Bağımlılık |
|-------|-------|-----------|
| Güç entegrasyonu (gerçek batarya + PDU) | `power/` | TBD-BAT-001/002 |
| Termal entegrasyon (gerçek ısıtıcı + sensörler) | `thermal/` | TBD-THM-001/003 |
| Lokalizasyon HIL (gerçek sensörler) | `vehicle/localization` | TBD-SNS-001/002/003 |
| SIL/HIL köprü implementasyonu | `simulation/digital-twin/sil_hil_bridge` | §10 OBC arayüzü |
| Landing GNC (ayrı tasarım) | `vehicle/landing-gnc/` | TBD-GNC-001 |
| TVAC testleri (THM-004/005) | Termal vakum tesisi | TBD-THM-001/003 |
| HIL regresyon suite (tüm RT + CT-001..007) | Gerçek OBC + sensörler | TBD-SNS-001 |

### Giriş Koşulları

- P2 çıkış kriterleri tümü yeşil.
- §10 araç verisi dondurulmuş (tüm P-CRIT TBD'ler kapalı):

| TBD ID | Parametre |
|--------|-----------|
| TBD-BAT-001 | Batarya kapasitesi (Wh) |
| TBD-BAT-002 | Batarya kimyası |
| TBD-SNS-001 | Sensör paketi |
| TBD-SNS-002 | IMU gürültü |
| TBD-SNS-003 | Odometry hata |
| TBD-THM-001 | Termal kütle + yalıtım |
| TBD-COM-001 | İletişim donanımı |
| TBD-GNC-001 | Landing GNC gereksinimleri |
| TBD-ENE-002 | HC-006 dönüş rezervi eşiği |
| TBD-TIME-001 | Görev başlangıç tarihi |

### Çıkış Kriterleri

| Kriter | Yöntem | Hedef |
|--------|--------|-------|
| P3-AC-01: HIL lokalizasyon σ < 0.5m | HIL | Gerçek sensör altında |
| P3-AC-02: HIL FDIR tepki < 50ms | HIL | 10 anomali tipi |
| P3-AC-03: Landing GNC handover | HIL | σ_pos < bootstrap eşiği |
| P3-AC-04: Tüm QAR-P1 maddeler HIL'de karşılandı | HIL | %100 |
| P3-AC-05: SC-003/004/005/006 HIL geçiyor | HIL | Her senaryo |
| THM-004/005 TVAC kalifikasyonu | TVAC | Min/Maks sıcaklık |
| Dijital ikiz SoH degradasyon doğrulandı | HIL + Dijital İkiz | §3.3 metrikleri |

---

## TBD Kapı Haritası

TBD'lerin hangi faz kapılarını engellediği özet tablosu. Kaynak: `config/tbd_register.md`.

| TBD ID | Parametre | P1 Kapısı | P2 Kapısı | P3 Kapısı |
|--------|-----------|-----------|-----------|-----------|
| TBD-BAT-001 | Batarya kapasitesi | — | — | ✖ BLOKE |
| TBD-BAT-002 | Batarya kimyası | — | ✖ BLOKE | ✖ BLOKE |
| TBD-SNS-001 | Sensör paketi | — | ✖ BLOKE | ✖ BLOKE |
| TBD-SNS-002 | IMU gürültü | — | ✖ BLOKE | ✖ BLOKE |
| TBD-SNS-003 | Odometry hata | — | ✖ BLOKE | ✖ BLOKE |
| TBD-THM-001 | Termal kütle + yalıtım | ✖ BLOKE | ✖ BLOKE | ✖ BLOKE |
| TBD-COM-001 | İletişim donanımı | — | ✖ BLOKE | ✖ BLOKE |
| TBD-GNC-001 | Landing GNC | — | — | ✖ BLOKE |
| TBD-ENE-002 | HC-006 dönüş rezervi | — | ✖ BLOKE | ✖ BLOKE |
| TBD-TIME-001 | Görev başlangıç tarihi | ✖ BLOKE | — | ✖ BLOKE |
| TBD-REPO-001 | lunar-navigator submodule | ✖ P0 bekleyen | — | — |

**P1 kapısı açmak için minimum:** TBD-THM-001 + TBD-TIME-001  
**P2 kapısı açmak için minimum:** 6 P-CRIT TBD (TBD-BAT-002, SNS-001/002/003, COM-001, ENE-002)  
**P3 kapısı açmak için:** Tüm P-CRIT TBD'ler + §10 araç verisi dondurulmuş

---

## Risk–Yol Haritası Kesişimi

Yüksek RPN risklerinin hangi fazda azaltıldığı:

| Risk | RPN | Azaltma Fazı | Yöntem |
|------|-----|--------------|--------|
| RR-003 (Termal model VIPER uyarısı) | 16 | P1 (Analysis) + P3 (TVAC) | §10 termal kütle ile simülatör kalibrasyon |
| RR-002 (Dönüş rezervi belirsizliği) | 15 | P1-AC-06 (SIL), P3 (HIL) | Enerji tahmin hatası < %10 (CT-002) |
| RR-004 (Link timeout uzun) | 12 | P2-AC-03 (SIL SC-002) | FI-006 CT-004 |
| RR-007 (Lokalizasyon bootstrap) | 12 | P3-AC-03 (HIL) | Landing GNC handover testi |
| RR-011 (DEM 80m çözünürlük sınırı) | 12 | P1-AC-02 (SIL), AC-VAL-005 | 80m altı engel local planner testi |

---

## Faz Geçiş Kapıları Özeti

| Geçiş | Kapı Koşulları | Yetkili | Tahmini Tarih |
|-------|----------------|---------|---------------|
| Ön Aşama → P0 | ConOps + QAR + HC onaylandı | luna-ai-architecture | ✅ 2026-11-14 |
| P0 → P1 | P0-AC-01..07 yeşil; TBD-REPO-001 kararı | luna-ai-architecture | ⏳ TBD |
| P1 → P2 | P1-AC-01..06 + AC-VAL-001..005 yeşil; TBD-THM-001 + TBD-TIME-001 kapalı | luna-ai-architecture | ⏳ §10 sonrası |
| P2 → P3 | P2-AC-01..08 yeşil; 6 P-CRIT TBD kapalı | luna-ai-architecture | ⏳ §10 sonrası |
| P3 → Operasyonel | P3-AC-01..05 + TVAC + tüm P-CRIT TBD kapalı | Görev otoritesi | ⏳ §10 + P3 sonrası |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent C, C5 görevi; P0-P3 yol haritası, TBD kapı haritası |
