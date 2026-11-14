# status: draft
# owner: luna-ai-architecture
# depends_on: [docs/qar/, infrastructure/risk_register.md, simulation/scenarios/operational_scenarios.md, autonomy/autonomy_matrix.md, mission-intelligence/constraints/hard_constraints.py]
# open_items: [aydınlanma modeli doğrulama toleransı ±TBD% (source: LOLA/SPICE baseline), enerji-termal simülatör toleransı ±TBD% (source: §10 araç profili), FDIR yanlış pozitif oranı eşiği TBD]

# Doğrulama Kabul Kriterleri — LUNA-AI v1.1 (§1.10)

## Amaç

Her proje fazının (P0-P3) tamamlandığını gösteren ölçülebilir çıkış kriterleri. Test yöntemleri: Unit (birim test), SIL (Yazılım-içinde-döngü), HIL (Donanım-içinde-döngü), Analysis (analitik doğrulama).

**Not:** Hard constraints (HC-001..015) her fazda önce değerlendirilir. Kabul kriterleri HC kümesini geçen bir sistemin işlevsel doğruluğunu ölçer.

---

## P0 — Mimari Temel

**P0 tamamlandı sayılır:**

| Kriter ID | Kriter | Ölçüm Yöntemi | Hedef |
|-----------|--------|---------------|-------|
| P0-AC-01 | Tüm modül arayüzleri ICD şemasına uygun implement edilmiş | Unit test: her modül arayüzü için şema validasyonu | %100 geçme |
| P0-AC-02 | Hard constraints motoru HC-001..015 kümesini değerlendiriyor | Unit test: her HC için pozitif + negatif test case | 15 HC × 2 test = 30 test, %100 geçme |
| P0-AC-03 | Güvenlik durum makinesi 4 durum arası tüm geçişleri işliyor | Unit test: NORMAL↔CAUTION↔RETURN_REQUIRED↔SURVIVAL geçiş matrisi | Tüm geçerli geçişler işleniyor, geçersiz geçişler reddediliyor |
| P0-AC-04 | FDIR planlayıcıdan bağımsız çalışıyor (izole bellek doğrulandı) | Analysis + Unit test: bellek yalıtımı incelemesi, FDIR planner bağımlılığı yok | Bağımlılık sıfır |
| P0-AC-05 | Uyum Notu 1-5 kod reviewda onaylandı | Manuel inceleme: görev fazı/güvenlik durumu ayrımı, safe haven 7 kriter, Power Mgmt akış yönü | Onay alındı (reviewer imzası) |
| P0-AC-06 | temporal_class alanı tüm environment product TypedDict'lerinde mevcut | Unit test: `temporal_class` alanı zorunlu, None reddediliyor | %100 kapsam |
| P0-AC-07 | JSON Schema ve Python TypedDict uyumu (interoperabilite) | Unit test: JSON Schema ile Python TypedDict karşılaştırması | Sıfır uyumsuzluk |

---

## P1 — Bilimsel Simülasyon

**P1 tamamlandı sayılır:**

| Kriter ID | Kriter | Ölçüm Yöntemi | Hedef |
|-----------|--------|---------------|-------|
| P1-AC-01 | Aydınlanma modeli LOLA/SPICE gerçek verisiyle doğrulanmış | Analysis: simülasyon vs LOLA/SPICE karşılaştırması | ±TBD% (source: LOLA/SPICE baseline belirlenecek) |
| P1-AC-02 | Krater aday filtreleme HC kümesini doğru uyguluyor | SIL: 100 test adayı, bilinen HC ihlallerini içeren set | HC ihlalli adaylar %100 elendi, geçerli adaylar gözden kaçırılmadı |
| P1-AC-03 | Enerji-termal simülatörü bilinen araç profiliyle doğrulanmış | Analysis: simülatör vs §10 araç profili | ±TBD% (source: §10 araç termal + enerji modeli) |
| P1-AC-04 | Dijital ikiz nominal görev senaryosunu (SC-001) tamamlıyor | SIL: SC-001 tam koşusu — simüle DEM + sensör gürültüsü | Hedef noktaya ulaşıldı, enerji bütçe içinde, σ_pos < 0.5m |
| P1-AC-05 | Tüm temporal_class=predicted ürünleri historical'dan ayrı tutulmuş | Unit test: veri akışı izleme; predicted ve historical karışık kayıt yok | Sıfır karışma |
| P1-AC-06 | RR-002, RR-003, RR-004, RR-007 (yüksek RPN) için azaltma doğrulanmış | SIL: her yüksek RPN riski için özel test senaryosu | Her risk için azaltma etkinliği gösterildi |

---

## P2 — Otonomi Prototipi

**P2 tamamlandı sayılır:**

| Kriter ID | Kriter | Ölçüm Yöntemi | Hedef |
|-----------|--------|---------------|-------|
| P2-AC-01 | Global planlayıcı < 60s içinde rota üretiyor (1km² arazi) | SIL performans testi: 1km² DEM, 50 farklı başlangıç-hedef çifti | %95 oranında < 60s |
| P2-AC-02 | Replanning < 30s içinde tamamlanıyor | SIL: ani engel enjeksiyonu → replanning süresi ölçümü | %95 oranında < 30s |
| P2-AC-03 | SC-002 (link kaybı) SIL geçiyor | SIL: SC-002 — SURFACE_EXPLORATION ve PSR_OPS için ayrı koşular | Her iki senaryo kabul kriterini karşıladı |
| P2-AC-04 | SC-003 (enerji düşüşü) SIL geçiyor | SIL: SC-003 — HC-006 ihlali enjeksiyonu, FDIR→Planner akışı | FDIR 5s içinde tetiklendi, Planner 30s içinde rota üretti |
| P2-AC-05 | FDIR SC-004 (lokalizasyon kaybı) için doğru abort üretiyor | SIL: QAR-NAV-002 ihlali enjeksiyonu → FDIR tepki | Detection, Isolation, Recovery adımları doğru sırada |
| P2-AC-06 | FDIR SC-006 (termal ihlal) için doğru abort üretiyor | SIL: thermal_margin < 0°C enjeksiyonu → FDIR tepki | RETURN_REQUIRED 5s içinde, ısıtıcı önceliklendirme aktif |
| P2-AC-07 | Hata enjeksiyonu: 10 kritik senaryo × FDIR beklenen tepki | SIL hata enjeksiyonu (Hata Enjeksiyonu Kapsam Matrisi'nden) | %100 uyum |
| P2-AC-08 | Power Mgmt → Planner akış yönü doğrulandı (Uyum Notu 3) | SIL + Code review: Planner enerji politikası üretemiyor, yalnızca tüketiyor | Bağımlılık yönü tek yönlü |

---

## P3 — Araç Entegrasyonu

**P3 tamamlandı sayılır:**

| Kriter ID | Kriter | Ölçüm Yöntemi | Hedef |
|-----------|--------|---------------|-------|
| P3-AC-01 | HIL: lokalizasyon sigma < 0.5m (gerçek sensör gürültüsü altında) | HIL: gerçek sensör paketi ile nominal koşu, σ_pos ölçümü | σ_pos < 0.5m nominal koşulda |
| P3-AC-02 | HIL: FDIR tepki < 50ms (anomali enjeksiyonu ile) | HIL: 10 anomali tipi enjeksiyonu, FDIR karar süresi ölçümü | %95 oranında < 50ms |
| P3-AC-03 | Landing GNC → yüzey navigasyon handover doğrulandı | HIL: tam iniş simülasyonu + navigasyon başlatma | Handover σ_pos < bootstrap eşiği |
| P3-AC-04 | Tüm QAR-P1 (Kritik öncelik) maddeleri HIL'de karşılandı | HIL: QAR-P1 maddelerinin tam koşusu | %100 geçme |
| P3-AC-05 | SC-003, SC-004, SC-005, SC-006 HIL geçiyor | HIL: kritik senaryo koşuları | Her senaryo kabul kriterini karşıladı |

---

## Hata Enjeksiyonu Kapsam Matrisi

> Satırlar: FMEA'dan top-10 RPN hata modları (B3 risk kaydıyla hizalı).
> Sütunlar: Test seviyesi.
> Hücre: K=Kapsanıyor, —=Kapsanmıyor.

| Hata Modu | Risk | Unit | SIL | HIL |
|-----------|------|------|-----|-----|
| Planlayıcı hesap süresi aşımı | RR-001 | K | K | — |
| Dönüş rezervi (HC-006) ihlali | RR-002 | K | K | K |
| Termal model sapması (> ±eşik) | RR-003 | — | K | K |
| İletişim blackout (uzun süreli) | RR-004 | — | K | K |
| QAR-NAV-002 lokalizasyon eşik ihlali | RR-005 | K | K | K |
| PSR haritası düşük çözünürlük | RR-006 | K | K | — |
| Lokalizasyon bootstrap hatası | RR-007 | — | K | K |
| Güç-termal döngü kararsızlığı | RR-008 | — | K | K |
| Sensör arızası (kısmi/tam) | SC-004 | K | K | K |
| FDIR yanlış pozitif | RR-010 | K | K | — |

**Not:** HIL kapsam boşlukları (RR-001, RR-006, RR-010) P3'te analiz ile kapatılacak.

---

## Faz Geçiş Kapıları

| Faz | Kapı Koşulu | Yetkili |
|-----|-------------|---------|
| P0 → P1 | P0-AC-01..07 tümü yeşil | luna-ai-architecture |
| P1 → P2 | P1-AC-01..06 tümü yeşil | luna-ai-architecture |
| P2 → P3 | P2-AC-01..08 tümü yeşil | luna-ai-architecture |
| P3 → Operasyonel | P3-AC-01..05 tümü yeşil + §10 araç verisi dondurulmuş | Görev otoritesi |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — B4 görevi |
