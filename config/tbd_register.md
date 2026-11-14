# status: draft
# owner: luna-ai-architecture
# depends_on: [config/open_inputs.md, domain/environment/uncertainty_policy.md, infrastructure/risk_register.md]
# open_items: [TBD'ler §10 araç verisi geldikçe kapanacak; Öncelik 1 TBD'ler P1 kapı koşuludur]

# TBD Kaydı — LUNA-AI v1.1

## Amaç

Tüm `TBD(source: §10)` ve ilgili belirsiz parametreleri tek yerde toplar. §10 araç verisi geldikçe TBD'ler bu belgeden kapanır ve etkilenen modüller güncellenir.

## Öncelik Tanımı

- **P-CRIT:** Bloke edici — kesinleşmeden P1/P2 başlanamaz
- **P-HIGH:** P1 simülasyon aşamasında kalibre edilmeli
- **P-MED:** P2 prototip aşamasında kesinleşmeli
- **P-LOW:** P3 entegrasyon aşamasına kadar ertelenebilir

---

## TBD Tablosu

| ID | Parametre | Varsayılan / Aralık | §10 Kaynağı | Etkilediği Dosyalar | Öncelik |
|----|-----------|--------------------|-----------|--------------------|---------|
| TBD-BAT-001 | Batarya kapasitesi (Wh) | 500–1500 Wh | §10 enerji alt sistemi | power/, HC-006, config/open_inputs.md | P-HIGH |
| TBD-BAT-002 | Batarya kimyası ve şarj/deşarj limitleri | — | §10 enerji alt sistemi | power/, thermal/, HC-006, HC-007 | P-CRIT |
| TBD-SOL-001 | Güneş paneli nominal güç (W) | 300–800 W | §10 enerji alt sistemi | power/, HC-009 | P-HIGH |
| TBD-TRV-001 | Nominal gezinti hızı (m/s) | 0.05–0.15 m/s | §10 hareket alt sistemi | autonomy/global-planner, rota süresi tahmini | P-HIGH |
| TBD-TRV-002 | Maks tırmanma açısı (°) | 20–30° | §10 hareket alt sistemi | HC-001, HC-005, autonomy/global-planner | P-HIGH |
| TBD-MAS-001 | Araç kütlesi (kg) | 100–300 kg | §10 yapı alt sistemi | vehicle/mobility-control, enerji/kg tüketim | P-MED |
| TBD-SNS-001 | Sensör paketi (tip, konfigürasyon) | — | §10 algı alt sistemi | vehicle/localization, QAR-NAV-002, FDIR eşikleri | P-CRIT |
| TBD-SNS-002 | IMU gürültü parametreleri (σ_drift) | — | §10 algı alt sistemi | domain/environment/uncertainty_policy.md §3.1 | P-CRIT |
| TBD-SNS-003 | Odometry hata parametreleri (σ_odo) | — | §10 algı alt sistemi | domain/environment/uncertainty_policy.md §3.1 | P-CRIT |
| TBD-THM-001 | Termal kütle ve yalıtım konfigürasyonu | — | §10 termal alt sistemi | thermal/, HC-007, SC-006, RR-003 | P-CRIT |
| TBD-THM-002 | Termal model sapma toleransı (±%) | ±TBD% | §10 termal alt sistemi | tests/acceptance_criteria.md P1-AC-03, RR-003 | P-HIGH |
| TBD-THM-003 | Kritik termal marj eşiği (°C) | 0°C (uyarı: 5°C) | §10 termal alt sistemi | SC-006, thermal/, FDIR | P-HIGH |
| TBD-COM-001 | İletişim donanımı (anten, bant genişliği) | — | §10 iletişim alt sistemi | communication/, HC-014, SC-002, SC-007 | P-CRIT |
| TBD-COM-002 | Link timeout süresi (s) | — | §10 iletişim alt sistemi | autonomy/autonomy_matrix.md ABT-004, SC-002 | P-HIGH |
| TBD-COM-003 | Link recovery window süresi (s) | — | §10 iletişim alt sistemi | SC-002 ABT-004 bekleme süresi | P-HIGH |
| TBD-GNC-001 | Landing GNC gereksinimleri | — | §10 GNC alt sistemi | vehicle/landing-gnc, P3-AC-03 | P-CRIT |
| TBD-NAV-001 | Lokalizasyon bootstrap σ_pos başlangıç değeri | — | §10 GNC alt sistemi | vehicle/localization, RR-007 | P-HIGH |
| TBD-ENE-001 | Enerji tüketim modeli belirsizliği σ_energy_pct | — | §10 araç profili | domain/environment/uncertainty_policy.md §2.3 | P-HIGH |
| TBD-ENE-002 | Dönüş rezervi eşiği HC-006 (Wh) | — | §10 enerji alt sistemi | HC-006, SC-003, ABT-001, power/ | P-CRIT |
| TBD-HEIGHT-001 | Observer height (anten/sensör mast yüksekliği, m) | 0.5–2.0 m | §10 yapı alt sistemi | simulation/environment-model, communication, SC-009, RR-013 | P-HIGH |
| TBD-TIME-001 | Görev başlangıç tarihi (UTC) | 2024–2035 aralığı | Görev otoritesi | simulation/environment-model, apps/ground-control, RR-012 | P-CRIT |
| TBD-REPO-001 | lunar-navigator entegrasyon yöntemi (submodule vs referans dizin) | — | Proje kararı | infrastructure/repo_placement.md, DR-INT-001 | P-MED |
| TBD-REPO-002 | GPU ray-marching flight segment bridge mimarisi | — | P2 tasarım kararı | apps/ground-control, infrastructure/repo_placement.md | P-LOW |
| TBD-VIS-001 | Marjinal Dünya görünürlük elevation eşiği (°) | — | Ortam modeli analizi | domain/environment/uncertainty_policy.md §7.1, communication/ | P-HIGH |
| TBD-SIM-001 | Regolith yoğunluğu ve zemin tipi (tekerlek-toprak etkileşim modeli) | — | §10 arazi modeli + jeoloji analizi | simulation/simulator_design.md §1.1, §1.4, §2.3 | P-HIGH |
| TBD-SIM-002 | DEM dosyası ve çözünürlüğü (m/px) | — | §10 bölge seçimi + LRO LOLA | simulation/simulator_design.md §1.1, example_scenario.yaml | P-HIGH |
| TBD-SIM-003 | Toz kaplama kaybı faktörü α_dust (panel verimi kaybı) | — | §10 ortam analizi | simulation/simulator_design.md §1.2, §2.4 | P-MED |
| TBD-SIM-004 | Ay yüzeyi albedo (bölgeye özgü) | — | §10 jeoloji + LRO gözlem | simulation/simulator_design.md §1.3 | P-MED |
| TBD-SIM-005 | Regolith termal inersi (J m⁻² K⁻¹ s⁻½) | — | §10 jeoloji analizi | simulation/simulator_design.md §1.3 | P-MED |
| TBD-SIM-006 | OBC + nav işlemci nominal güç tüketimi (W) | — | §10 güç bütçesi | simulation/simulator_design.md §2.1 | P-HIGH |
| TBD-SIM-007 | Motor sürücüleri nominal güç tüketimi (W, hareket halinde) | — | §10 güç bütçesi | simulation/simulator_design.md §2.1 | P-HIGH |
| TBD-SIM-008 | Isıtıcılar nominal güç tüketimi (W) | — | §10 termal bütçe | simulation/simulator_design.md §2.1 | P-HIGH |
| TBD-SIM-009 | Haberleşme modülü güç tüketimi (W, HGA aktif) | — | §10 güç bütçesi | simulation/simulator_design.md §2.1 | P-HIGH |
| TBD-SIM-010 | Bilimsel sensörler güç tüketimi (W) | — | §10 güç bütçesi | simulation/simulator_design.md §2.1 | P-MED |
| TBD-SIM-011 | CI pipeline senaryo çalıştırma timeout (dakika) | — | §10 CI altyapısı kapasitesi | simulation/simulator_design.md §5.3 | P-LOW |
| TBD-SIM-012 | Nominal senaryo maksimum süre (s) | — | §10 görev profili | simulation/simulator_design.md §5.3, example_scenario.yaml | P-HIGH |
| TBD-RED-001 | İkinci IMU modülü ekleme (kütle/hacim) | — | §10 yapı + sensör alt sistemi | docs/architecture/redundancy_matrix.md TBD listesi | P-HIGH |
| TBD-RED-002 | Üçlü OBC (triple voting) fizibilite | — | §10 yapı + güç bütçesi | docs/architecture/redundancy_matrix.md TBD listesi | P-MED |
| TBD-RED-003 | İkinci batarya modülü boyutlandırması | TBD-BAT-001/002 bağımlı | §10 enerji alt sistemi | docs/architecture/redundancy_matrix.md TBD listesi | P-CRIT |
| TBD-RED-004 | UHF omni anten boyutu ve frekans bandı | TBD-COM-001 bağımlı | §10 iletişim + yapı alt sistemi | docs/architecture/redundancy_matrix.md TBD listesi | P-HIGH |
| TBD-RED-005 | Motor sürücü redundancy seviyesi (triple) | — | §10 hareket alt sistemi | docs/architecture/redundancy_matrix.md TBD listesi | P-MED |
| TBD-RED-006 | Termal fallback ısıtıcı güç kapasitesi (W) | TBD-THM-001 bağımlı | §10 termal alt sistemi | docs/architecture/redundancy_matrix.md TBD listesi | P-HIGH |
| TBD-RED-007 | Yedek güneş paneli veya alternatif enerji kaynağı | TBD-SOL-001 bağımlı | §10 yapı + enerji alt sistemi | docs/architecture/redundancy_matrix.md TBD listesi | P-MED |
| TBD-RED-008 | PDU yedeklilik detayı (güç hattı yönlendirme topolojisi) | — | §10 araç mühendisliği | docs/architecture/redundancy_matrix.md TBD listesi | P-MED |

---

## Kapanma Prosedürü

Bir TBD §10 verisi geldiğinde:

1. Bu tabloda `Durum` sütunu KAPALTI olarak işaretlenir.
2. Etkilenen modüllerde TBD yer tutucusu gerçek değerle değiştirilir.
3. Değişiklik commit mesajında `closes TBD-XXX-YYY` ile referans verilir.
4. P-CRIT TBD'ler kapanmadan ilgili faz kapısı açılmaz.

---

## P-CRIT TBD'ler Özet

Aşağıdaki TBD'ler kapanmadan P1 → P2 geçiş kapısı açılamaz:

| TBD ID | Parametre |
|--------|-----------|
| TBD-BAT-002 | Batarya kimyası |
| TBD-SNS-001 | Sensör paketi |
| TBD-SNS-002 | IMU gürültü |
| TBD-SNS-003 | Odometry hata |
| TBD-THM-001 | Termal kütle + yalıtım |
| TBD-COM-001 | İletişim donanımı |
| TBD-GNC-001 | Landing GNC gereksinimleri |
| TBD-ENE-002 | HC-006 dönüş rezervi eşiği |
| TBD-TIME-001 | Görev başlangıç tarihi |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — C3 görevi, 24 TBD kaydı |
| 0.2 | 2026-11-14 | Agent C: +20 TBD (TBD-SIM-001..012, TBD-RED-001..008) — C3 simülatör tasarımı ve C1 yedeklilik matrisi |
