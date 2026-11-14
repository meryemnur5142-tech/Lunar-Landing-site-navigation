# status: draft
# owner: luna-ai-architecture
# depends_on: [mission-intelligence/constraints/hard_constraints.py, docs/qar/, simulation/scenarios/operational_scenarios.md, autonomy/autonomy_matrix.md]
# open_items: [RPN eşik politikası TBD — hangi RPN'den yukarısı program riski sayılır, azaltma stratejileri §10 araç verisi geldikçe güncellenecek]

# Risk Kaydı — LUNA-AI v1.1

## Amaç

Bu belge LUNA-AI sisteminin tanımlanmış teknik ve operasyonel risklerini, olasılık/etki değerlendirmelerini ve azaltma stratejilerini kayıt altına alır. Risk sahipleri ile izleme yöntemleri proje fazlarına göre güncellenir.

## Skorlama Skalası

- **Olasılık (1-5):** 1=Çok düşük (<5%), 2=Düşük (5-20%), 3=Orta (20-40%), 4=Yüksek (40-60%), 5=Çok yüksek (>60%)
- **Etki (1-5):** 1=İhmal edilebilir, 2=Küçük, 3=Orta (görev hedefi etkilenir), 4=Büyük (görev başarısı risk altında), 5=Kritik (güvenlik tehlikesi veya tam görev kaybı)
- **RPN = Olasılık × Etki**

---

## Risk Tablosu

| ID | Risk Tanımı | Kaynak | Olasılık (1-5) | Etki (1-5) | RPN | Azaltma Stratejisi | İzleme Yöntemi | Sahip | Durum |
|----|-------------|--------|----------------|------------|-----|-------------------|----------------|-------|-------|
| RR-001 | Kaynak-kısıtlı planlayıcı hesap süresi aşımı | §6 A* algoritması | 3 | 3 | 9 | Hesap süresi aşımı için fallback: önceki geçerli rota veya sabit safe haven yönelimi. Zaman bütçesi < 30s replanning hedefi. Anytime algoritma yaklaşımı değerlendirilecek. | SIL performans testi: 1km² arazi, 100 senaryo. Replanning süresi histogramı. | autonomy/global-planner | AÇIK |
| RR-002 | Belirsizlik altında dönüş rezervi yetersizliği | Tahmin hatası + mesafe birikimi | 3 | 5 | 15 | HC-006 worst-case (2σ) planlama zorunlu. Dönüş rezervi güncelleme periyodu optimize edilecek. Enerji tüketim modeli kalibrasyon testleri. | HIL enerji tüketim doğrulaması; worst-case senaryo SIL. σ_energy izleme. | power | AÇIK |
| RR-003 | Termal model doğruluğu — VIPER parametresi | §6 uyarısı: VIPER verisi kullanıldıysa | 4 | 4 | 16 | §10 araç verisi geldiğinde termal model yeniden kalibre edilecek. TBD(source: §10 araç termal kütle + yalıtım). VIPER parametrelerinin hangi modüllerde kullanıldığı belgelenmeli. | P2: simülatör termal doğrulama; P3 HIL: gerçek araç termal ölçümü. Sapma eşiği: ±TBD%. | thermal | AÇIK |
| RR-004 | İletişim kaybı süresi tahmini — blackout beklenden uzun | Lunar relay geometrisi, yer anten müsaitliği | 3 | 4 | 12 | Link budget hesabı §10 iletişim donanımına bağlı. TBD(source: §10). Pre-planned abort trigger süreleri muhafazakâr seçilecek. Blackout toleransı SC-002 senaryosuna göre tasarlanacak. | Trajectory simülasyonu ile link kesinti analizi. SC-002 SIL testi. | communication | AÇIK |
| RR-005 | Belirsizlik eşik kalibrasyonu — QAR değerleri gerçek araçla uyumsuz | QAR-NAV-002 ve diğer QAR eşikleri | 3 | 3 | 9 | P1'de simülatör kalibrasyonu. P3 HIL'de gerçek sensör gürültüsü altında eşik revizyonu. Araç sensör paketi §10'dan geldikçe güncelleme. | HIL: lokalizasyon sigma ölçümü < 0.5m hedefi (P3 kabul kriteri). QAR eşik gözden geçirme toplantısı. | vehicle/localization | AÇIK |
| RR-006 | PSR haritası çözünürlük yetersizliği — ShadowCam kalitesi beklenden düşük | ShadowCam/LOLA veri kalitesi | 2 | 4 | 8 | temporal_class=predicted ürünler için belirsizlik bandı genişletilir. DEM çözünürlük yeterliliği B5 §1 tablosuna göre değerlendirilir (> 20m/px eleme). Alternatif veri kaynağı (Kaguya, LRO) değerlendirilecek. | Veri kalite skoru izleme. P1: aydınlanma modeli ±TBD% doğrulama. | data-platform | AÇIK |
| RR-007 | Lokalizasyon bootstrap hatası — iniş sonrası ilk konum kestirimi hatalı | İniş GNC → navigasyon handover | 3 | 4 | 12 | P3 kabul kriteri: Landing GNC → yüzey navigasyon handover doğrulanacak. Bootstrap belirsizliği σ başlangıç değeri muhafazakâr seçilecek. İlk landmark eşleşmesi öncelikli. | P3 HIL: iniş simülasyonu + lokalizasyon başlatma testi. σ_pos < eşik hedefi. | vehicle/localization | AÇIK |
| RR-008 | Güç-termal döngü kararsızlığı — ısıtıcı yükü enerji bütçesini sürekli ihlal ediyor | Termal-enerji geri besleme döngüsü | 2 | 4 | 8 | Power Mgmt sahibi, Planner tüketici (Uyum Notu 3). Döngü kararlılığı: ısıtıcı talep güncelleme periyodu optimize edilecek. TBD(source: §10 ısıtıcı güç profili). Kararlılık analizi SIL'de yapılacak. | SIL: enerji-termal ko-simülasyon 24 saatlik görev. Kararsızlık tespiti için enerji bandı aşım sayacı. | power + thermal | AÇIK |
| RR-009 | Araç donanım parametresi değişimi — §10 girdileri beklenen aralık dışı | §10 araç tasarım revizyonu | 3 | 3 | 9 | config/open_inputs.md'de bloke edici vs dondurulabilir girdiler ayrılmış. Parametre değişikliği impact analizi prosedürü oluşturulacak. TBD kaydı config/tbd_register.md'de takip edilir. | config/tbd_register.md düzenli güncelleme. §10 girdi değişikliğinde etkilenen modüllerin re-test listesi hazırlanacak. | luna-ai-architecture | AÇIK |
| RR-010 | FDIR yanlış pozitif — sağlıklı sistemde abort tetikleniyor | FDIR eşik kalibrasyonu | 2 | 3 | 6 | FDIR eşik değerleri QAR doğrulama kapsamına dahil edilecek. Yanlış pozitif oranı SIL hata enjeksiyonu ile ölçülecek. Eşik ayarı muhafazakâr ama gereksiz abort'u engelleyecek şekilde tasarlanacak. | B4 Hata Enjeksiyonu Matrisi: 10 kritik senaryo × FDIR beklenen tepki = %100 uyum hedefi. FDIR yanlış pozitif oranı < TBD%. | safety/fdir | AÇIK |

---

## RPN Önem Sıralaması

| Sıra | ID | RPN | Açıklama |
|------|----|-----|----------|
| 1 | RR-003 | 16 | Termal model doğruluğu (VIPER uyarısı) |
| 2 | RR-002 | 15 | Dönüş rezervi belirsizliği |
| 3 | RR-004 | 12 | İletişim kaybı süresi |
| 4 | RR-007 | 12 | Lokalizasyon bootstrap hatası |
| 5 | RR-001 | 9 | Planlayıcı hesap süresi |
| 6 | RR-005 | 9 | QAR eşik kalibrasyonu |
| 7 | RR-009 | 9 | Donanım parametresi değişimi |
| 8 | RR-006 | 8 | PSR haritası çözünürlük |
| 9 | RR-008 | 8 | Güç-termal kararsızlık |
| 10 | RR-010 | 6 | FDIR yanlış pozitif |

**Yüksek öncelik eşiği (RPN ≥ 12):** RR-002, RR-003, RR-004, RR-007 → P1 simülasyon aşamasında azaltma tamamlanmalı.

---

## TBD Referansları Bu Belgede

- RR-003: Termal model sapma eşiği `±TBD%` (source: §10 araç termal kütle + yalıtım)
- RR-004: Link timeout süresi (source: §10 iletişim donanımı)
- RR-008: Isıtıcı güç profili (source: §10)
- RR-010: FDIR yanlış pozitif oranı hedefi (source: güvenilirlik analizi)

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — B3 görevi, 10 risk, RPN sıralaması |
