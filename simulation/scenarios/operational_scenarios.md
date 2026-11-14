# status: draft
# owner: luna-ai-architecture
# depends_on: [autonomy/autonomy_matrix.md, mission-intelligence/constraints/hard_constraints.py, docs/conops/, docs/qar/]
# open_items: [link_timeout değerleri TBD(source: §10), thermal_margin kritik eşiği TBD(source: §10 araç termal modeli), return_reserve_wh eşiği HC-006'da tanımlı]

# Operasyonel Senaryolar — LUNA-AI v1.1

## Amaç

Bu belge LUNA-AI aracının karşılaşabileceği tipik ve kritik durumlar için standart operasyon ve yanıt senaryolarını tanımlar. Her senaryo SIL/HIL kabul testlerinde doğrulama referansı olarak kullanılır.

**Önemli:** Güvenlik durumları (NORMAL/CAUTION/RETURN_REQUIRED/SURVIVAL) görev fazlarından (CRUISE/LANDING/SURFACE_EXPLORATION/PSR_OPS/RETURN/SAFE_STATE) bağımsız eksenlerdir. Geçişler her iki eksende ayrı takip edilir.

---

## SC-001: Normal Yüzey Keşfi

| Alan | İçerik |
|------|--------|
| **Senaryo ID** | SC-001 |
| **Ad** | Normal Yüzey Keşfi — Nominal Path |
| **Tetikleyici koşul** | Görev fazı SURFACE_EXPLORATION, güvenlik durumu NORMAL, enerji bütçesi nominal |
| **Başlangıç fazı** | SURFACE_EXPLORATION |
| **Sorumlu modüller** | vehicle/localization, autonomy/global-planner, autonomy/local-planner, power, communication |

**Beklenen araç yanıtı (adım adım):**

1. **Lokalizasyon:** Önceki orbital harita ve iniş verisini kullanarak başlangıç konum kestirimi. `position_uncertainty_m < 0.5m` doğrulandı.
2. **Lokal plan:** Local planner, global rotadan sonraki N waypoint'i hesaplar. Engellerden kaçınma değerlendirilir.
3. **Hareket:** Araç nominal hızda (`TBD(source: §10)` m/s) waypoint'e doğru ilerler. IMU + odometry füzyonu aktif.
4. **Lokalizasyon güncelleme:** Her `TBD(source: §10)` metrede landmark eşleştirme girişimi. Eşleşme başarılıysa σ_pos sıfırlanır.
5. **Telemetri:** Her `TBD(source: §10)` saniyede yer kontrolüne konum, enerji, termal durum raporu.
6. **Waypoint onay:** Hedef waypoint'e ±1m içinde ulaşıldı → hedef başarılı olarak işaretlendi.
7. **Bilimsel veri toplama:** Hedefte araç durur, bilim yükü açılır (OTN — otonom karar). Ölçüm döngüsü tamamlanır.
8. **Sonraki waypoint:** Global planner sonraki hedefi seçer; enerji bütçesi kontrol edilir.

| Alan | İçerik |
|------|--------|
| **Güvenlik durumu geçişi** | NORMAL → NORMAL (nominal koşulda geçiş yok) |
| **Yer kontrolüne bildirim koşulu** | Waypoint ulaşım onayı; bilimsel veri özeti; enerji tüketimi raporu |
| **Kabul kriteri** | Hedef noktaya ulaşıldı (±1m), enerji bütçe içinde (nominal ±10%), lokalizasyon σ < 0.5m korundu |
| **Test yöntemi** | SIL (simüle DEM + sensör gürültüsü), HIL (P3 aşamasında gerçek sensör) |

---

## SC-002: İletişim Kaybı

| Alan | İçerik |
|------|--------|
| **Senaryo ID** | SC-002 |
| **Ad** | İletişim Kaybı — Link Timeout (v1.0 §4.7) |
| **Tetikleyici koşul** | Telemetri linki `link_timeout_s > TBD(source: §10)` süre kesildi |
| **Başlangıç fazı** | SURFACE_EXPLORATION veya PSR_OPS (iki ayrı yanıt — aşağıda) |
| **Sorumlu modüller** | communication, autonomy/mission-executive, safety/fdir, autonomy/global-planner |

**Beklenen araç yanıtı — SURFACE_EXPLORATION'da link kaybı (adım adım):**

1. Communication modülü link_timeout'u algılar → FDIR'a bildirir.
2. Güvenlik durumu NORMAL → CAUTION geçişi.
3. Araç mevcut waypoint'e doğru harekete devam eder (OTN — pre-planned trigger yoksa).
4. Pre-planned abort trigger listesi (ABT-001..006) kontrol edilir. Hiçbiri tetiklenmediyse devam.
5. `link_wait_timeout = TBD(source: §10)` süre bekleme sayacı başlar.
6. Bekleme süresi aşılmadan link geri gelirse: CAUTION → NORMAL, operasyon devam.
7. Bekleme süresi aşılırsa: Pre-planned safe haven listesine yönel (OTN). Enerji bütçesi kontrol.
8. Safe haven'a ulaşıldığında bekle, periyodik haberleşme girişimi devam eder.

**Beklenen araç yanıtı — PSR_OPS'ta link kaybı (adım adım):**

1. Communication modülü link_timeout'u algılar → FDIR'a bildirir.
2. Güvenlik durumu NORMAL → RETURN_REQUIRED geçişi (PSR'de link kaybı = dönüş tetikleyici).
3. FDIR: Enerji durumunu kontrol et. `return_reserve_wh` yeterli mi?
   - **Evet:** ACL dönüş rotası başlat. Bilimsel operasyon durdurulur.
   - **Hayır:** ACL acil dönüş + enerji koruma modu. Power Mgmt önceliklendirme yapar.
4. Planner, mevcut konumdan safe haven'a en kısa enerji-verimli rota üretir.
5. Araç dönüş rotasında ilerlerken periyodik link girişimi yapar.
6. PSR çıkışında anten açısı toparlanabilirse link geri gelebilir.

**Pre-planned abort trigger listesi (SC-002 kapsamında):**

| Trigger | Koşul | Eylem |
|---------|-------|-------|
| ABT-001 | `return_reserve_wh < HC-006_threshold` AND faz=PSR_OPS | ACL acil dönüş |
| ABT-004 | `link_timeout > TBD(source: §10)` AND faz=PSR_OPS AND `energy_critical=true` | ACL acil dönüş |
| ABT-006 | `fdir_abort_flag=true` | ACL göreve göre eylem |

| Alan | İçerik |
|------|--------|
| **Güvenlik durumu geçişi** | SURFACE_EXPLORATION: NORMAL→CAUTION→(link gelirse NORMAL) veya →RETURN_REQUIRED; PSR_OPS: NORMAL→RETURN_REQUIRED |
| **Yer kontrolüne bildirim koşulu** | Link geri geldiğinde: link kaybı başlangıç/bitiş zamanı, yapılan eylemler, mevcut konum ve enerji durumu |
| **Kabul kriteri** | Link kaybı sırasında araç pre-planned sınırlar dışına çıkmadı; enerji kritik eşiğin altına düşmedi; link dönüşünde koordinasyon başarıyla sağlandı |
| **Test yöntemi** | SIL (link simülasyonu ile), HIL (P3) |

---

## SC-003: PSR'de Ani Enerji Düşüşü

| Alan | İçerik |
|------|--------|
| **Senaryo ID** | SC-003 |
| **Ad** | PSR'de Ani Enerji Düşüşü (v1.0 §5.D) |
| **Tetikleyici koşul** | `return_reserve_wh < HC-006_threshold` — PSR içindeyken dönüş rezervi kritik eşiğin altına indi |
| **Başlangıç fazı** | PSR_OPS |
| **Sorumlu modüller** | power, safety/fdir, autonomy/global-planner, thermal |

**Beklenen araç yanıtı (adım adım):**

1. **Power Mgmt algılar:** `return_reserve_wh` HC-006 eşiğinin altına düştü → FDIR'a anomali bildirimi.
2. **FDIR kararı:** HC-006 ihlali → güvenlik durumu geçişi NORMAL → RETURN_REQUIRED.
   - FDIR bağımsız çalışır (planner'dan izole bellek).
3. **Power Mgmt enerji bütçesi günceller:** Bilimsel yük kapatılır (enerji tüketimini azalt). Isıtıcılar minimum zorunlu düzeye indirilir. Bu karar Power Mgmt'e aittir; Planner tüketicidir.
4. **FDIR → Planner'a dönüş komutu:** `abort_to_safe_haven = true`, `reason = HC006_violation`.
5. **Planner rota üretir:** Mevcut PSR konumundan safe haven'a minimum enerji rotası. Rota üretim hedefi < 30s.
6. **Araç dönüş rotasına girer:** Faz PSR_OPS → RETURN geçişi.
7. **Telemetri:** Yer kontrolüne HC-006 ihlali, dönüş başlangıcı, beklenen varış zamanı iletilir.
8. **Dönüş izleme:** Her adımda `return_reserve_wh` yeniden hesaplanır. Yeterli kalıyorsa devam; kritikleşirse enerji koruma modu artırılır.
9. **Safe haven ulaşım:** Şarj başlar. Güvenlik durumu RETURN_REQUIRED → NORMAL (şarj tamamlanınca).

**Akış yönü notu (Uyum Notu 3):** Power Mgmt enerji bütçesi sahibidir; bütçe hesapları ve kısıtları Power Mgmt'ten gelir. Planner bu bilgiyi tüketir, kendi başına enerji politikası belirleyemez.

| Alan | İçerik |
|------|--------|
| **Güvenlik durumu geçişi** | NORMAL → RETURN_REQUIRED (HC-006 ihlali anında), RETURN_REQUIRED → NORMAL (safe haven şarj sonrası) |
| **Yer kontrolüne bildirim koşulu** | HC-006 ihlali anında (enerji değeri, konum, beklenen dönüş süresi); safe haven ulaşımında |
| **Kabul kriteri** | FDIR HC-006 ihlalini algıladı ve 5s içinde RETURN_REQUIRED geçişini tetikledi; planner 30s içinde dönüş rotası üretti; araç safe haven'a HC-006 eşiği üzerinde enerji ile ulaştı |
| **Test yöntemi** | SIL (enerji tüketim simülasyonu), HIL (P3) |

---

## SC-004: Lokalizasyon Kaybı / Sensör Arızası

| Alan | İçerik |
|------|--------|
| **Senaryo ID** | SC-004 |
| **Ad** | Lokalizasyon Kaybı / Sensör Arızası (v1.0 §4.8) |
| **Tetikleyici koşul** | `position_uncertainty_m > QAR-NAV-002_threshold` — konum belirsizliği kabul eşiğini aştı |
| **Başlangıç fazı** | SURFACE_EXPLORATION veya PSR_OPS |
| **Sorumlu modüller** | vehicle/localization, safety/fdir, autonomy/global-planner, autonomy/local-planner |

**FDIR Adımları — Detection → Isolation → Recovery:**

**Detection:**
1. Lokalizasyon modülü sürekli σ_pos izler.
2. `position_uncertainty_m > QAR-NAV-002_threshold` → FDIR anomali bayrağı set edilir.
3. Güvenlik durumu NORMAL → CAUTION.
4. Araç DUR komutunu alır (hareket durdurulur).

**Isolation:**
5. Hangi sensörün arızalı olduğu tespit edilmeye çalışılır:
   - IMU tutarsızlık testi
   - Odometry/IMU karşılaştırması
   - Son landmark eşleşme kalitesi kontrolü
6. Arızalı sensör izole edilir (degraded mode).

**Recovery:**
7. **Landmark arama:** Araç yerinde dönerek orbital haritadaki landmark eşleşmesini dener.
   - Eşleşme başarılı: σ_pos < eşiğe düşer → CAUTION → NORMAL. Hareket devam.
   - Eşleşme başarısız (N deneme, TBD(source: §10)): Recovery başarısız.
8. **Recovery başarısız:** Güvenlik durumu CAUTION → RETURN_REQUIRED.
   - Faz PSR_OPS ise: ACL acil dönüş (konum belirsizliğiyle degraded navigation).
   - Faz SURFACE_EXPLORATION ise: Pre-planned safe haven koordinatlarına IMU-only navigasyon.
9. **Degraded navigation modu:** Yalnızca IMU + odometry, landmark olmadan. Hata birikimi kabul edilen maksimum mesafeyle sınırlandırılır.
10. Yer kontrolüne bildirim: Sensör arızası tipi, mevcut σ_pos, planlanan eylem.

| Alan | İçerik |
|------|--------|
| **Güvenlik durumu geçişi** | NORMAL→CAUTION (algılama), CAUTION→NORMAL (recovery başarılı) veya CAUTION→RETURN_REQUIRED (recovery başarısız) |
| **Yer kontrolüne bildirim koşulu** | QAR-NAV-002 ihlali anında; recovery kararında (başarılı/başarısız) |
| **Kabul kriteri** | FDIR lokalizasyon kaybını 5s içinde algıladı; landmark arama girişimi yapıldı; recovery başarısızsa RETURN_REQUIRED geçişi tetiklendi ve araç safe haven'a ulaştı |
| **Test yöntemi** | SIL (sensör gürültüsü enjeksiyonu), HIL (P3 — gerçek sensör arıza simülasyonu) |

---

## SC-005: Safe Haven'a Erişilemiyor

| Alan | İçerik |
|------|--------|
| **Senaryo ID** | SC-005 |
| **Ad** | Safe Haven'a Erişilemiyor — Birincil Rota Tıkandı |
| **Tetikleyici koşul** | `primary_safe_haven_route_blocked = true` — engel veya arazi koşulu birincil safe haven rotasını kapattı |
| **Başlangıç fazı** | SURFACE_EXPLORATION, PSR_OPS veya RETURN |
| **Sorumlu modüller** | autonomy/global-planner, autonomy/replanner, safety/fdir, power |

**Beklenen araç yanıtı (adım adım):**

1. Local planner birincil safe haven rotasında geçilemez engel algılar → FDIR'a bildirir.
2. Araç DUR. FDIR yedek safe haven değerlendirmesini başlatır.
3. **Yedek safe haven seçimi — 7 kriter (Uyum Notu 2):**
   - Kriter 1: Kesintisiz aydınlanma (enerji şarjı için)
   - Kriter 2: Karanlık aralığı toleransı (termal dayanım)
   - Kriter 3: Yeniden şarj kapasitesi (panel açısı, beklenen güç)
   - Kriter 4: Dönüş enerjisi yeterliliği (oradan iniş noktasına)
   - Kriter 5: Termal güvenlik (sıcaklık aralığı)
   - Kriter 6: Haberleşme (yer antenine görüş hattı)
   - Kriter 7: Acil erişim (gelecek görev veya kurtarma için)
4. Tüm 7 kriteri karşılayan yedek safe haven var → replanner yeni rota üretir. YER onayı (normal operasyonda) veya ACL (PSR içinde veya enerji kritikse).
5. Yer kontrolüne bildirim: Birincil safe haven tıkandı, yedek seçildi, 7 kriter sonuçları.
6. **Yedek safe haven yok:** Hiçbir alternatif 7 kriterin tamamını karşılamıyorsa:
   - Güvenlik durumu RETURN_REQUIRED → SURVIVAL geçişi.
   - SURVIVAL modu hazırlığı: bilim yükü kapat, ısıtıcıları minimum zorunlu düzeyde tut, enerji koruma maks.
   - Araç konumunda bekler. Periyodik haberleşme girişimi.
   - Yer kontrolüne kritik durum bildirimi: konum, enerji, termal durum, beklenen hayatta kalma süresi.

| Alan | İçerik |
|------|--------|
| **Güvenlik durumu geçişi** | (mevcut)→RETURN_REQUIRED (yedek bulunursa dönüş planı); RETURN_REQUIRED→SURVIVAL (yedek yoksa) |
| **Yer kontrolüne bildirim koşulu** | Birincil rota tıkanması anında; yedek seçim kararında; SURVIVAL girişinde (kritik) |
| **Kabul kriteri** | 7 kriter doğru uygulandı; yedek bulunursa rota üretildi; SURVIVAL'da enerji koruma aktif ve bildirim gönderildi |
| **Test yöntemi** | SIL (rota engelleme enjeksiyonu, 7 kriter senaryoları), HIL (P3) |

---

## SC-006: Termal Limit İhlali

| Alan | İçerik |
|------|--------|
| **Senaryo ID** | SC-006 |
| **Ad** | Termal Limit İhlali (v1.0 §4.5) |
| **Tetikleyici koşul** | `thermal_margin_c < 5°C` (uyarı) veya `thermal_margin_c < 0°C` (kritik) |
| **Başlangıç fazı** | SURFACE_EXPLORATION veya PSR_OPS |
| **Sorumlu modüller** | thermal, power, safety/fdir, autonomy/global-planner |

**Beklenen araç yanıtı — Uyarı seviyesi (< 5°C marj):**

1. Thermal modül uyarı eşiğini algılar → FDIR'a bildirir. Güvenlik durumu NORMAL → CAUTION.
2. Isıtıcı önceliklendirme: Kritik sistem ısıtıcıları (işlemci, batarya, sensörler) önce. Bilimsel yük ısıtıcıları askıya alınır.
3. **Enerji bütçesine etki (Uyum Notu 3):** Power Mgmt ısıtıcı güç talebini alır, bütçeyi günceller. Toplam tüketim artıyorsa Planner'a yeni bütçe sınırı iletilir. Planner gezinti hızını/sıklığını azaltır.
4. Yer kontrolüne bildirim: Termal uyarı, hangi ısıtıcıların açıldığı, enerji bütçesine etkisi.
5. Durum izlenir; marj 5°C'nin üzerine çıkarsa CAUTION → NORMAL.

**Beklenen araç yanıtı — Kritik seviye (< 0°C marj):**

1. Thermal modül kritik eşiği algılar → FDIR'a bildirir. Güvenlik durumu CAUTION/NORMAL → RETURN_REQUIRED.
2. Tüm ısıtıcılar maksimum önceliğe alınır. Bilimsel yük acil kapatılır.
3. **PSR içindeyse karar:**
   - `ısınma_in_place_vs_return` değerlendirmesi: Mevcut termal model + enerji durumuna göre.
   - Eğer PSR içinde güneş ışığı yoksa ve ısıtıcı güç yeterliyse: **yerinde ısınma** (< X dakika, TBD(source: §10 termal model)).
   - Isınma yetmeyecekse veya enerji kritikse: **ACL acil dönüş** başlatılır.
4. SURFACE_EXPLORATION'da: ACL en yakın aydınlık bölgeye yönel (termal kazanım).
5. **Power Mgmt → Planner akış:** Power Mgmt ısıtıcı talebiyle güncellenmiş bütçe gönderir. Planner bu bütçe içinde rota üretir.
6. Yer kontrolüne bildirim: Kritik termal durum, yapılan eylem, beklenen iyileşme süresi.

| Alan | İçerik |
|------|--------|
| **Güvenlik durumu geçişi** | NORMAL→CAUTION (uyarı), CAUTION→RETURN_REQUIRED (kritik) |
| **Yer kontrolüne bildirim koşulu** | Uyarı eşiği geçildiğinde; kritik eşikte (acil); PSR dönüş/yerinde ısınma kararında |
| **Kabul kriteri** | Uyarı: Isıtıcı önceliklendirme 2s içinde aktif; enerji bütçesi güncellendi. Kritik: RETURN_REQUIRED 5s içinde tetiklendi; PSR içinde doğru karar (ısınma/dönüş) verildi |
| **Test yöntemi** | SIL (termal model ile hata enjeksiyonu), HIL (P3) |

---

## Senaryo Özet Tablosu

| Senaryo | Faz | Güvenlik Geçişi | Otorite | Test |
|---------|-----|-----------------|---------|------|
| SC-001 | SURFACE_EXPLORATION | NORMAL kalır | OTN | SIL + HIL |
| SC-002 | SURFACE / PSR | NORMAL→CAUTION veya RETURN_REQUIRED | OTN / ACL | SIL + HIL |
| SC-003 | PSR_OPS | NORMAL→RETURN_REQUIRED | ACL | SIL + HIL |
| SC-004 | SURFACE / PSR | NORMAL→CAUTION→NORMAL veya RETURN_REQUIRED | FDIR | SIL + HIL |
| SC-005 | SURFACE / PSR / RETURN | →RETURN_REQUIRED veya SURVIVAL | ACL / YER | SIL + HIL |
| SC-006 | SURFACE / PSR | NORMAL→CAUTION→RETURN_REQUIRED | ACL | SIL + HIL |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — B2 görevi |
