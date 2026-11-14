# status: draft
# owner: Agent D
# depends_on:
#   - docs/conops/CONOPS.md
#   - docs/qar/QAR_TABLE.md
#   - domain/mission/constraints/hard_constraints_catalog.yaml
#   - domain/mission/phase_state_machine.md
#   - docs/architecture/SAFETY_STATE_MACHINE.md
#   - autonomy/autonomy_matrix.md
# open_items:
#   - TBD-PLAN-001: Heuristik ağırlık faktörü (w) weighted A* için
#   - TBD-PLAN-002: Maksimum lokal replanning iterasyon sayısı
#   - TBD-PLAN-003: Arazi tipine göre enerji tüketim modeli (Wh/m)
#   - TBD-PLAN-004: Termal maliyet katsayısı (cost fonksiyonu)
#   - TBD-PLAN-005: Risk maliyet katsayısı (eğim, engel yakınlığı)
#   - TBD-PLAN-006: Safe haven minimum aydınlanma eşiği (HC-009 / QAR SHV-001)
#   - TBD-PLAN-007: Safe haven minimum yeniden şarj kapasitesi (HC-011)
#   - TBD-PLAN-008: İletişim kaybı bekleme süresi (TBD-COM-002 ile örtüşür)
#   - TBD-PLAN-009: Bilim zamanlayıcı öncelik ağırlıkları

# Kaynak-Kısıtlı Görev Planlayıcı — LUNA-AI

**Belge ID:** LUNA-AI-AUT-D1-001
**Versiyon:** 0.1-draft
**Tarih:** 2026-11-14
**Sahip:** Agent D

---

## 1. Planlayıcı State Space

### 1.1 State Vektörü

Görev planlayıcının durum uzayı altı boyutlu bir vektörle tanımlanır:

```
S = (konum_x, konum_y, zaman, enerji_wh, termal_durum, güvenlik_seviyesi)
```

| Alan | Tip | Birim | Açıklama |
|------|-----|-------|----------|
| `konum_x` | float | m | Araç X koordinatı (yerel harita çerçevesi) |
| `konum_y` | float | m | Araç Y koordinatı (yerel harita çerçevesi) |
| `zaman` | float | s | Görev başından itibaren geçen süre |
| `enerji_wh` | float | Wh | Mevcut batarya şarj düzeyi |
| `termal_durum` | enum | — | {NOMINAL, CAUTION, CRITICAL} |
| `güvenlik_seviyesi` | enum | — | {NOMINAL, CAUTION, RETURN_REQUIRED, SURVIVAL} |

### 1.2 Neden Klasik A* Yetmez

Klasik A*, yalnızca uzamsal konum ekseninde maliyet hesaplar: `f(n) = g(n) + h(n)` burada `g(n)` başlangıçtan düğüme olan gerçek mesafe maliyeti, `h(n)` ise hedef düğüme tahmin edilen mesafe maliyetidir. Bu modelin LUNA-AI için yetersiz kalmasının üç temel nedeni vardır:

**Enerji durumu state'e dahil:** Farklı enerji seviyeleriyle aynı (x, y) konumuna ulaşmak aynı düğüm değildir. Enerji kritik eşiğin altına düşen bir araç, aynı konumdaki tam şarjlı araca göre tamamen farklı hareket seçeneklerine sahiptir. Klasik A* bu farkı modelleyemez.

**Termal etki birikmeli:** Yavaş tırmanan bir rota enerji açısından verimli olabilir ama termal yük birikimini artırabilir. Termal durum da state'e dahil edilmelidir.

**Güvenlik durumu geçişleri deterministik:** FDIR durum makinesi (bkz. `docs/architecture/SAFETY_STATE_MACHINE.md`) belirli eşikler aşıldığında güvenlik durumunu değiştirir. Bu geçişler plan hesabı sırasında öngörülmeli ve maliyet fonksiyonuna yansıtılmalıdır.

### 1.3 State Space Büyümesi ve Pratik Sınırlama

Tam durum uzayı, uzamsal çözünürlük `Δxy`, enerji çözünürlüğü `Δe` ve zaman adımı `Δt` ile büyür:

```
|S| = (Lx/Δxy) × (Ly/Δxy) × (T/Δt) × (E_max/Δe) × |termal| × |güvenlik|
```

Tipik bir 500 m × 500 m operasyon alanı için 1 m uzamsal çözünürlük ve 10 Wh enerji adımı bile milyonlarca düğüm üretir. Pratik sınırlama stratejileri:

1. **Enerji ve termal ayrıştırma:** Uzamsal planlama önce yapılır, enerji ve termal durum her adımda ileri simülasyon (rollout) ile takip edilir. Bu yöntem, enerji/termal boyutlarını state uzayından çıkararak hesapsal karmaşıklığı düşürür.
2. **Erken budama:** Enerji rezervi `HC-006` eşiğinin altına düşecek herhangi bir rota anında elenir. Aramada dallanma sayısı azalır.
3. **Seyrek waypoint grafiği:** Ham piksel/voksel çözünürlüğü yerine kritik geçiş noktaları (kaya alanları, kret geçişleri, güneş boşlukları) düğüm olarak seçilir. Ara yollar doğrusal enterpolasyonla hesaplanır.
4. **Zaman boyutu çıkarma:** Enerji bütçesi hesabı, zaman değişkenini marjinal enerji tüketimiyle ilişkilendirerek dolaylı yoldan modele dahil edilir. Zaman ayrı bir arama boyutu olmaktan çıkar.
5. **Weighted A\*:** `f(n) = g(n) + w × h(n)` ile `w > 1` kullanımı bulma süresini QAR-PLAN-001 (< 60 s) hedefiyle uyumlu kılar; optimal olmayan ama kabul edilebilir rotalar üretir. `w` değeri: TBD-PLAN-001.

---

## 2. Global Planlayıcı

### 2.1 Girdi ve Çıktı

| Alan | Tip | Kaynak |
|------|-----|--------|
| `target_coord` | (x, y) metreler | Yer segmenti görev paketi |
| `current_state` | PlannerState | Navigasyon sistemi (ICD-001) |
| `environment_map` | OccupancyGrid | Yerel ve orbital harita füzyonu |
| `safe_haven_coords` | List[(x, y)] | Önceden yüklenmiş HC-009..HC-015 onaylı liste |
| `energy_budget` | EnergyBudget | Güç Yönetimi (ICD-002, HC-006 onayı) |

Çıktı: Sıralı waypoint listesi `[(x0, y0), (x1, y1), ..., (xN, yN)]` artı her adım için tahmini enerji tüketimi ve termal yük.

### 2.2 Algoritma Seçimi: Kaynak-Kısıtlı A* vs D* Lite

Her iki algoritma da değerlendirilmiş ve aşağıdaki gerekçeyle **Kaynak-Kısıtlı A*** temel algoritma olarak seçilmiştir (ADR-001 referans). D* Lite ikincil strateji olarak lokal replanning için rezervedir.

| Kriter | Kaynak-Kısıtlı A* | D* Lite |
|--------|------------------|---------|
| Statik çevrede optimum rota | Garanti edilir | Garanti edilir |
| Enerji/termal state entegrasyonu | Doğal | Ek bileşen gerektirir |
| Dinamik engel güncellemesi | Tam yeniden hesap | Artımlı güncelleme (verimli) |
| Bellek kullanımı | O(|açık set|) | O(|harita|) |
| Hesap süresi (ilk plan) | QAR-PLAN-001 ile uyumlu (< 60 s) | Benzer |
| Replanning süresi | Yüksek (tam yeniden) | Düşük (artımlı) |

**Tercih gerekçesi:** İlk görev planı statik çevrede optimum enerji rotası gerektirdiğinden A* tercih edilir. Dinamik engeller için D* Lite lokal planlayıcıya devredilir (§3).

### 2.3 Maliyet Fonksiyonu

Her düğüm geçişi `(n_i → n_j)` için birleşik maliyet:

```
cost(i, j) = w_dist × dist(i,j)
           + w_energy × energy_cost(i,j, terrain)   [Wh/m: TBD-PLAN-003]
           + w_thermal × thermal_cost(i,j)           [katsayı: TBD-PLAN-004]
           + w_risk × risk_cost(i,j)                 [katsayı: TBD-PLAN-005]
```

**Mesafe maliyeti (`w_dist`):** Öklid mesafesi. Temel maliyet terimi.

**Enerji maliyeti (`w_energy × energy_cost`):** Araç kütlesi × yerçekimi × eğim açısı × mesafe artı düz yüzey sürtünme modeli. Arazi tipine göre katsayılar: TBD-PLAN-003. Güç Yönetimi modülü tarafından sağlanan enerji tüketim modelinden beslenir (Uyum Notu 3: Planlayıcı enerji modelini bağımsız hesaplamaz).

**Termal maliyet (`w_thermal × thermal_cost`):** PSR girişinde sıfıra çekilen güneş enerjisi ve aktif aydınlatma yüküyle artan termal stres. Termal durum `CAUTION` → `CRITICAL` eşiğine yaklaşan rotalar yüksek maliyet alır.

**Risk maliyeti (`w_risk × risk_cost`):** `HC-003` engel yoğunluğu kesriyle orantılı; `HC-005` eğim limitine yakın rotalar yüksek risk puanı alır. TBD-PLAN-005.

### 2.4 Dönüş Rezervi Kısıtı

Planlayıcı her yeni waypoint eklemeden önce dönüş enerji kısıtını kontrol eder:

```
IF (mevcut_enerji - cost_to_next_waypoint - return_energy(next_waypoint)) < HC-006.threshold:
    REJECT waypoint  # bu adım plana dahil edilmez
    EMIT return_trigger
```

`return_energy(pos)` fonksiyonu, verilen konumdan en yakın onaylı safe haven'a olan en kısa enerji maliyetini verir. Bu değer, Güç Yönetimi modülünce hesaplanır ve planlayıcıya ICD-002 üzerinden bildirilir (HC-006 Uyum Notu 3: planlayıcı bu değeri bağımsız hesaplamaz).

Dönüş marjı izleme frekansı: QAR-PLAN-005'e göre ≥ 1 Hz.

---

## 3. Lokal Planlayıcı (Gerçek Zamanlı)

### 3.1 Reaktif Replanning

Lokal planlayıcı, global planlayıcının ürettiği rotayı anlık engel algısıyla takip eder. Araç navigasyon hızında (10 Hz, QAR-NAV-003) çalışır. Global planın ±50 m'lik bir lokal penceresi üzerinde reaktif kararlar alır.

**Lokal replanning akışı:**

```
HER navigasyon döngüsünde:
  1. Algı katmanından mevcut engel haritasını al
  2. Önümüzdeki N waypoint için çarpışma kontrolü yap
  3. Çarpışma tespit edilirse:
     a. Yerel sapma (kaçınma manevrası) dene
     b. Kaçınma başarılıysa: global rotaya geri dön
     c. Kaçınma başarısızsa: replanning tetikleyici gönder (§4)
  4. Enerji tüketimini güncelle, dönüş rezervini kontrol et
```

**Lokal maliyet haritası:** Perception katmanından gelen LiDAR/stereo kamera verileriyle güncellenen dinamik engellilik ızgarası (occupancy grid). Güncelleme periyodu: navigasyon döngüsüyle eş zamanlı.

### 3.2 Global Planla Tutarlılık

Lokal planlayıcı global rotadan sapabilir; ancak şu kısıtlar geçerlidir:

- Sapma mesafesi maksimum `D_max` metreden fazla olamaz (TBD-PLAN-002 ile ilişkili; otonomi matrisine göre PSR içinde yalnızca önceden onaylı harita sınırları içinde OTN).
- Safe haven koordinatlarından uzaklaşan sapma kararları yalnızca SURFACE_EXPLORATION fazında OTN; PSR_OPS fazında sınır dışına çıkış YER gerektirir (otonomi matrisi §Ana Matris dipnot ¹).
- Lokal sapma tamamlandıktan sonra araç global rota üzerindeki en yakın waypoint'e geri döner.

---

## 4. Replanning Tetikleyicileri

### 4.1 Tam Yeniden Plan vs Lokal Düzeltme Karar Kuralı

| Durum | Karar | Gerekçe |
|-------|-------|---------|
| Tek engel, lokal sapma mesafesi < `D_local` | Lokal düzeltme | Küçük sapma; global rota geçerliliğini korur |
| Birden fazla ardışık engel veya bloke edilmiş koridor | Tam yeniden plan | Global rota artık geçersiz |
| Dönüş rezervi %110 eşiğine ulaştı (erken uyarı) | Yönlendirilmiş yeniden plan | Dönüş odaklı yeniden hesap; keşif segmentleri kısaltılır |
| FDIR güvenlik durumu CAUTION'dan RETURN_REQUIRED'a geçti | Zorunlu tam yeniden plan | Dönüş rotası önceliklendirilir, keşif bölümleri iptal edilir |
| Safe haven koordinatı değişti (YER onayıyla) | Zorunlu tam yeniden plan | Hedef değişikliği |
| PSR içinde FDIR abort_signal (ABT-001..ABT-006) | ACL tam yeniden plan | Güvenlik öncelikli |

### 4.2 Replanning Süresi Hedefi

Yeniden planlama süresi: QAR-PLAN-002'ye göre < 30 saniye. Bu hedef, lokal düzeltme için de geçerlidir; tam yeniden plan için 500 m rota üzerinde QAR-PLAN-001 (< 60 s) eşiği geçerlidir.

Replanning eşiği hesaplanırken mevcut enerji ve navigasyon belirsizliği göz önünde bulundurulur. Eğer replanning sırasında enerji dönüş rezervi düşmeye devam ediyorsa, replanning iptal edilir ve araç son bilinen iyi noktadan dönüşe geçer.

---

## 5. Safe Haven Seçimi

### 5.1 Puanlama Fonksiyonu

Her aday safe haven koordinatı aşağıdaki ağırlıklı puanlama fonksiyonuyla değerlendirilir:

```
score(candidate) = w1 × illumination_score(candidate)   [HC-009 / SHV-001: TBD-PLAN-006]
                 + w2 × recharge_score(candidate)         [HC-011 / SHV-001]
                 + w3 × return_energy_score(candidate)    [HC-012 / HC-006]
                 + w4 × thermal_safety_score(candidate)   [HC-013 / HC-007]
                 + w5 × comm_visibility_score(candidate)  [HC-014]
                 + w6 × emergency_route_score(candidate)  [HC-015]
                 + w7 × max_darkness_penalty(candidate)   [HC-010]
```

**Önemli:** Puanlama fonksiyonu yalnızca tüm HC-009..HC-015 hard constraint'lerini geçen adaylar için uygulanır. HC kümesi geçilmeyen adaylar elenir; puanlamaya alınmaz (HC katalogu preamble: "Hard constraints are evaluated first (pass/fail elimination)").

### 5.2 7 Safe Haven Kriteri

| Kriter No | HC ID | Parametre | Minimum Eşik |
|-----------|-------|-----------|-------------|
| 1 | HC-009 | Kesintisiz aydınlanma süresi | TBD-PLAN-006 (SHV-001) |
| 2 | HC-010 | Maksimum kabul edilebilir karanlık aralığı | TBD (§10 termal) |
| 3 | HC-011 | Yeniden şarj kapasitesi (Wh/sol) | TBD-PLAN-007 |
| 4 | HC-012 | Dönüş enerjisi yeterliliği | mesafe × Wh/m + marj (§10) |
| 5 | HC-013 | Termal güvenlik (yüzey sıcaklığı, güneş açısı) | TBD (§10 termal model) |
| 6 | HC-014 | Haberleşme görüş olanağı | TBD (§10 iletişim) |
| 7 | HC-015 | Acil erişim mesafesi | TBD (§10) |

Minimum eşikler `config/tbd_register.md`'de TBD-PLAN-006 ve TBD-PLAN-007 olarak kayıtlıdır; §10 araç ve orbital verisi geldiğinde kapatılacaktır.

### 5.3 Yedek Safe Haven Listesi

Birincil safe haven'ın erişilemez hale gelmesi (rota bloke, enerji yetersiz) durumuna karşı en az iki adet HC-009..HC-015 onaylı yedek koordinat araçta tutulur. Bu liste PSR_OPS fazına geçiş öncesi giriş kontrol listesi madde 6'da doğrulanır (phase_state_machine.md §4.3.1).

---

## 6. İletişim Kesintisi Senaryosu

### 6.1 Pre-Planned Karar Ağacı

İletişim kaybı koşullarında araç davranışı, otonomi matrisi İletişim Kaybı Matrisi ile tam uyumludur:

```
link_timeout tetiklendi (süre > TBD-PLAN-008):

SURFACE_EXPLORATION fazında:
  → Mevcut plan devam (OTN) — yeni risk alınmaz, PSR girişi BEKLE
  → PSR girişi: bekle (bekleme süre sınırı: TBD-COM-003)
  → Bekleme süresi aşıldı: PSR girişi iptal, güvenli bekle

PSR_OPS fazında:
  → Pre-approved harita sınırları içinde rota devam (OTN)
  → Enerji kritik tetiklendi (ABT-004): ACL acil dönüş
  → FDIR uyarısı aktif: bilimsel hedef terk (ACL), dönüş öncelikli

RETURN fazında:
  → Safe haven değişikliği OTN — önceden yüklenmiş yedek listeden seçim
  → Rota takibi OTN devam
```

### 6.2 Abort Trigger Koşulları

Aşağıdaki koşullardan herhangi biri karşılandığında araç yer onayı beklemeksizin dönüşe geçer (otonomi matrisi ABT serisi):

| Trigger | Koşul | Kaynak |
|---------|-------|--------|
| ABT-001 | `return_reserve_wh < HC-006.threshold` | Güç Yönetimi |
| ABT-004 | `link_timeout > TBD-PLAN-008` AND `energy_critical=true` AND `faz=PSR_OPS` | FDIR/İletişim |
| ABT-002 | `position_uncertainty_m > 2.0 m` (QAR-NAV-004 eşiği) | Navigasyon |

### 6.3 Bekleme vs Dönüş Kararı

| Faz | Link Yok Süresi | Enerji Durumu | Karar |
|-----|-----------------|---------------|-------|
| SURFACE_EXPLORATION | < TBD-PLAN-008 | Yeterli | Bekle, görev devam |
| SURFACE_EXPLORATION | > TBD-PLAN-008 | Yeterli | RETURN_REQUIRED → safe haven'a dön |
| PSR_OPS | Herhangi | Kritik (ABT-001) | Anında dönüş |
| PSR_OPS | < TBD-PLAN-008 | Yeterli | Mevcut rota devam (OTN, sınır içi) |
| PSR_OPS | > TBD-PLAN-008 | Yeterli | Dönüş değerlendirme (ACL) |

**Kural:** "Link yokken araç yeni risk almaz; sadece mevcut planı tamamlar veya döner." (CONOPS §6.3 Kural 1)

---

## 7. Bilimsel Hedef vs Kaynak Dengesi

### 7.1 Bilim Zamanlayıcısı Mimarisi

Bilim zamanlayıcısı, kalan enerji ve zaman bütçesine göre bilimsel görevlerin önceliklendirilmesinden ve iptalinden sorumludur. Mission Planner'ın bir alt modülüdür; FDIR'dan bağımsızdır.

**Girdi sinyalleri:**
- `energy_state.state_of_charge_pct` (Güç Yönetimi, QAR-PWR-001)
- `safety_status` (FDIR, ICD-004)
- `resource_state.thermal_margin_c` (Termal Yönetimi)
- `remaining_mission_time` (planlayıcı iç saati)
- `science_priority_weights` (yer segmenti görev paketi, TBD-PLAN-009)

### 7.2 İptal Kuralları

| Koşul | İptal Edilen Bilim Görevi | Gerekçe |
|-------|--------------------------|---------|
| Güvenlik durumu CAUTION | Yüksek güçlü bilim sensörü başlatılamaz | SAFETY_STATE_MACHINE CAUTION kısıtlamaları |
| Güvenlik durumu RETURN_REQUIRED | Tüm bilim operasyonları dondurulur | SAFETY_STATE_MACHINE RETURN_REQUIRED |
| `SoC < %25` (erken uyarı) | Opsiyonel yüksek güç bilim görevi | CONOPS Adım 5.2 |
| Replanning süresi > QAR-PLAN-002 | Düşük öncelikli bilim görevi askıya alınır | Planlayıcı zaman bütçesi |
| Dönüş marjı %110 erken uyarı eşiği | Yeni bilim noktası planlanmaz | HC-006 proaktif uyum |

### 7.3 Öncelik Sıralaması

Bilim görevleri iptal sırasına göre sıralanmıştır (en önce iptal edilecek en düşük önceliktedir):

1. Opsiyonel panoramik fotoğraf (düşük bilimsel özgünlük)
2. Yüzey sıcaklık profili (tekrar edilebilir)
3. Kimyasal analiz (yüksek özgünlük, ancak enerji yoğun)
4. Buz/kaynak numunesi spektroskopisi — **asla otomatik iptal edilmez**; yalnızca yer komutuyla

Öncelik ağırlıkları: TBD-PLAN-009 (yer segmentinden görev paketinde belirlenir).

---

## Uyum Notları

- **Uyum Notu 1 (Planlayıcı ≠ Güvenlik):** Görev Planlayıcı güvenlik kararı vermez. FDIR'dan gelen `safety_status` ve `abort_signal` mesajlarına tepki verir; bu sinyalleri üretmez.
- **Uyum Notu 3 (Enerji Hesabı):** `return_reserve_wh` değeri her zaman Güç Yönetimi modülünce hesaplanır ve ICD-002 üzerinden planlayıcıya bildirilir. Planlayıcı bu değeri bağımsız hesaplamaz (HC-006).

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent D görev D1 |
