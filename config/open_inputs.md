# status: draft
# owner: luna-ai-architecture
# depends_on: [mission-intelligence/constraints/hard_constraints.py, domain/environment/uncertainty_policy.md]
# open_items: [Bloke edici girdiler §10 kaynak onayını bekliyor; varsayılan aralıklar P1'de test edilecek]

# Açık Girdi Sınıflandırması — LUNA-AI v1.1 (v1.0 §10)

## Amaç

§10 araç donanım girdilerini iki kategoriye ayırır: P0/P1 aşamasında varsayılan aralıkla ilerlenebilecek olanlar ile kesinleşmeden ilerlenemeyen bloke edici girdiler.

---

## Tablo 1 — Aralıkla Dondurulabilir (P0/P1 varsayımla ilerlenebilir)

| Girdi | Varsayılan Aralık | Gerekçe | Etkilediği Modüller |
|-------|-----------------|---------|-------------------|
| Araç kütlesi | 100–300 kg | Lunar rover sınıfı (küçük-orta) | vehicle/mobility-control, power (enerji/kg tüketim) |
| Batarya kapasitesi | 500–1500 Wh | Küçük-orta rover tipik aralığı | power, HC-006 (dönüş rezervi eşiği) |
| Güneş paneli gücü | 300–800 W | Panel alanı ~1–2m² varsayımı | power, HC-009 (aydınlanma süresi yeterliliği) |
| Maks tırmanma açısı | 20–30° | Tekerlekli rover tipik sınırı | HC-001 (eğim sınırı), HC-005, autonomy/global-planner |
| Nominal gezinti hızı | 0.05–0.15 m/s | Lunar rover standart operasyon hızı | autonomy/global-planner (rota süresi tahmini) |
| Isıtıcı güç tüketimi | 50–200 W | Tipik rover termal sistem | thermal, power bütçesi |
| Observer height (anten/sensör) | 0.5–2.0 m | Tipik rover mast yüksekliği | communication (Dünya görünürlük), simulation/environment-model |

**Kullanım kuralı:** Aralık uç değerleri worst-case senaryolarda kullanılır. P1 simülasyon sonuçları aralık dışı tutumlar ortaya koyarsa yeniden değerlendirme gerekir.

---

## Tablo 2 — Bloke Edici (Kesinleşmeden ilerlenemez)

| Girdi | Neden Bloke Edici | Etkilediği Modüller | Beklenen Kaynak |
|-------|-----------------|-------------------|-----------------|
| Sensör paketi (tip, sayı, konfigürasyon) | Lokalizasyon algoritması seçimini belirler; EKF gürültü parametreleri sensöre bağımlıdır | vehicle/localization, vehicle/perception, FDIR eşikleri (QAR-NAV-002) | §10 araç tasarımı |
| Batarya kimyası (Li-ion, Li-Po vb.) | Güvenli şarj/deşarj limitleri ve termal model (C/kapasite limiti, düşük sıcaklık kesimi) batarya kimyasına bağlıdır | power, thermal, HC-006, HC-007 | §10 |
| Termal kütle + yalıtım konfigürasyonu | Karanlık toleransı hesabı (en uzun gece dayanımı) ve VIPER uyarısı: §10 gelene kadar VIPER parametresi kullanılıyorsa sapma riski | thermal, HC-007 (karanlık toleransı), SC-006 (termal ihlal) | §10 |
| İletişim donanımı (anten tipi, bant genişliği, güç) | Link budget hesabı, haberleşme kesinti toleransı (SC-002, SC-007), pencere kalitesi | communication, HC-014, autonomy/autonomy_matrix.md | §10 |
| İniş GNC gereksinimleri ve tasarımı | Landing GNC ayrı tasarım bileşeni; girdi gelmeden lokalizasyon handover testi (P3-AC-03) başlatılamaz | vehicle/landing-gnc, vehicle/localization | §10 |
| Görev tarihi / başlangıç penceresi | Ephemeris geçerlilik aralığı (2024–2035); bu dışında kalan tarih için ortam modeli geçersiz | simulation/environment-model, apps/ground-control, SC-008 | Görev otoritesi + §10 |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — C3 görevi |
