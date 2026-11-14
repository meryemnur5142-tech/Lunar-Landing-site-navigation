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
| TBD-NAV-002 | EKF süreç gürültüsü kovaryansı Q (IMU) | — | §10 algı alt sistemi (TBD-SNS-002 sonrası) | vehicle/localization/navigation_architecture.md §1.3 | P-HIGH |
| TBD-NAV-003 | EKF ölçüm gürültüsü kovaryansı R (odometri/VO) | — | §10 algı alt sistemi (TBD-SNS-003 sonrası) | vehicle/localization/navigation_architecture.md §1.3 | P-HIGH |
| TBD-NAV-004 | LiDAR menzil ve çözünürlük özellikleri | — | §10 algı alt sistemi | vehicle/localization/navigation_architecture.md §3, autonomy/ | P-CRIT |
| TBD-NAV-005 | Görsel odometri özellik çıkarma parametreleri | — | §10 algı alt sistemi | vehicle/localization/navigation_architecture.md §1.1 | P-HIGH |
| TBD-NAV-006 | Güneş sensörü doğruluk özellikleri | — | §10 algı alt sistemi | vehicle/localization/navigation_architecture.md §1.1 | P-MED |
| TBD-NAV-007 | Orbital DEM çözünürlüğü ve güncelleme frekansı | — | Orbital misyon verisi | vehicle/localization/navigation_architecture.md §4.1 | P-HIGH |
| TBD-NAV-008 | PSR navigasyonu son bilinen iyi konumdan max mesafe | — | §10 araç güç modeli | vehicle/localization/navigation_architecture.md §3.3 | P-HIGH |
| TBD-FDIR-001 | IMU/VO çapraz kontrol tutarsızlık eşiği (σ_imu_vo_diff) | — | §10 algı alt sistemi | safety/fdir_implementation.md §1.1, safety/fdir_decision_tree.md | P-HIGH |
| TBD-FDIR-002 | Tekerlek encoder vs komut sapma eşiği (motor sıkışma tespiti) | — | §10 hareket alt sistemi | safety/fdir_implementation.md §2.1, safety/fdir_decision_tree.md | P-HIGH |
| TBD-FDIR-003 | Batarya SoC sapma anomali eşiği | — | §10 enerji alt sistemi | safety/fdir_implementation.md §3.1 | P-HIGH |
| TBD-FDIR-004 | Hücre dengesizlik eşiği (mV fark) | — | §10 enerji alt sistemi | safety/fdir_implementation.md §3.1 | P-HIGH |
| TBD-FDIR-005 | FDIR ana döngü frekansı (Hz); donanım bağımlı | — | §10 OBC/RTOS konfigürasyonu | safety/fdir_implementation.md §6.2, docs/architecture/SAFETY_STATE_MACHINE.md §3 | P-HIGH |
| TBD-FDIR-006 | İletişim kaybı link_timeout eşiği (s); TBD-COM-002 ile örtüşür | — | §10 iletişim alt sistemi | safety/fdir_implementation.md §4.1, safety/fdir_decision_tree.md | P-HIGH |
| TBD-FDIR-007 | Lokalizasyon kaybı pozisyon belirsizlik eşiği (m) | 2.0 m (QAR-NAV-004 referans) | §10 algı alt sistemi | safety/fdir_implementation.md §5.1 | P-HIGH |
| TBD-FDIR-008 | Lokalizasyon recovery bekleme süresi (s) | — | §10 görev parametresi | safety/fdir_implementation.md §5.3, safety/fdir_decision_tree.md | P-HIGH |
| TBD-PLAN-001 | Weighted A* heuristik ağırlık faktörü (w) | 1.0–3.0 | §10 hesap bütçesi + QAR-PLAN-001 | autonomy/mission_planner.md §1.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-PLAN-002 | Maksimum lokal replanning iterasyon sayısı | — | §10 OBC hesap kapasitesi | autonomy/mission_planner.md §3.2 | P-MED |
| TBD-PLAN-003 | Arazi tipine göre enerji tüketim modeli (Wh/m) | — | §10 enerji + hareket modeli | autonomy/mission_planner.md §2.3, autonomy/global_planner_pseudocode.py | P-HIGH |
| TBD-PLAN-004 | Termal maliyet katsayısı (cost fonksiyonu) | — | §10 termal model | autonomy/mission_planner.md §2.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-PLAN-005 | Risk maliyet katsayısı (eğim, engel yakınlığı) | — | §10 arazi veri | autonomy/mission_planner.md §2.3, autonomy/global_planner_pseudocode.py | P-MED |
| TBD-PLAN-006 | Safe haven minimum aydınlanma eşiği (saat) | — | Orbital mekanik sim (SHV-001) | autonomy/mission_planner.md §5.2, HC-009 | P-HIGH |
| TBD-PLAN-007 | Safe haven minimum yeniden şarj kapasitesi (Wh/sol) | — | §10 enerji + orbital | autonomy/mission_planner.md §5.2, HC-011 | P-HIGH |
| TBD-PLAN-008 | İletişim kaybı bekleme süresi — planlayıcı davranışı (s) | — | §10 iletişim alt sistemi (TBD-COM-002) | autonomy/mission_planner.md §6.3 | P-HIGH |
| TBD-PLAN-009 | Bilim zamanlayıcı öncelik ağırlıkları | — | Bilim ekibi öncelik kararı | autonomy/mission_planner.md §7.3, autonomy/global_planner_pseudocode.py | P-MED |

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
| TBD-NAV-004 | LiDAR menzil ve çözünürlük özellikleri |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — C3 görevi, 24 TBD kaydı |
| 0.2 | 2026-11-14 | Agent D (D1-D2-D3): NAV-002..008, FDIR-001..008, PLAN-001..009 eklendi (25 yeni kayıt) |
