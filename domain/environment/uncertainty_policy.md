# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/schemas/environment_product.schema.yaml, safety/safety_budget.md, mission-intelligence/constraints/hard_constraints.py, docs/qar/]
# open_items: [Tüm sayısal eşikler TBD — QAR ve araç modeline göre kalibre edilecek, quality_score eşiği (0.7) araç sensör paketine göre revize edilecek]

# Belirsizlik Yönetimi Politikası — LUNA-AI v1.1

## Amaç

Bu belge LUNA-AI sisteminde ortam verileri ve araç durum kestirimlerine ilişkin belirsizliklerin nasıl tanımlanacağını, biriktiğini, yönetileceğini ve karar akışına nasıl yansıtılacağını tanımlar.

**Temel ilke:** Hard constraints (HC-001..015) her zaman önce değerlendirilir. Belirsizlik yönetimi HC kümesinin muhafazakâr uygulanmasını güvence altına alır.

---

## 1. Belirsizlik Eşikleri — Karar Tablosu

> **Not:** Tüm sayısal değerler TBD — QAR gereksinimleri ve araç modeline göre kalibre edilecek. Aşağıdaki değerler tasarım referans noktasıdır.

| Belirsizlik Tipi | Düşük (kabul — devam et) | Orta (operatöre sor) | Yüksek (eleme/dur) | FDIR Tetikleme |
|-----------------|--------------------------|---------------------|-------------------|----------------|
| Konum belirsizliği σ_pos | < 0.5m | 0.5–2m | > 2m | > QAR-NAV-002_threshold → SC-004 |
| PSR sınır güveni | > 0.85 | 0.70–0.85 | < 0.70 | PSR girişi reddedilir (HC kontrolü) |
| Enerji bütçe hatası | < 10% | 10–20% | > 20% | > 20% → worst-case planlama zorunlu |
| DEM çözünürlük yeterliliği | < 5m/px için | 5–20m/px | > 20m/px | > 20m/px → PSR haritalama reddedilir |
| Termal model sapması | < TBD% | TBD–TBD% | > TBD% | > eşik → SC-006 uyarı |
| Landmark eşleşme güveni | > 0.80 | 0.60–0.80 | < 0.60 | < 0.60 → lokalizasyon reset girişimi |

**Kullanım kuralı:** Belirsizlik "Orta" aralığına girdiğinde araç operatöre sor bildirimi gönderir ve onay bekler (YER — otonomi matrisi). "Yüksek" aralığında ise karar yapısına göre eleme, durdurma veya FDIR tetikleme uygulanır.

---

## 2. Nominal vs Worst-Case Planlama

### 2.1 Nominal Planlama

Nominal beklenen değerlerle hesaplama yapılır. Kullanım alanı: bilimsel hedef sıralama, ön keşif rota planlaması, telemetri tahmini.

### 2.2 Worst-Case Planlama

2σ belirsizlik payı eklenerek muhafazakâr hesaplama yapılır. **Zorunlu kullanım alanları:**

- PSR dönüş rezervi hesabı (HC-006) — **her koşulda worst-case**
- Safe haven seçimi (7 kriter)
- Acil dönüş süresi tahmini
- Karanlık toleransı hesabı

**PSR özel kuralı:** PSR operasyonunda enerji hesabı DAIMA worst-case kullanılır, nominal değil. Nominal hesap yalnızca raporlama amaçlıdır.

### 2.3 Belirsizlik Payı Formülasyonu

Dönüş rezervi worst-case tahmini:

```
return_reserve_wh_wc = return_reserve_wh_nominal × (1 + k_sigma × σ_energy_pct)
```

Burada `k_sigma = 2` (2σ), `σ_energy_pct` enerji tüketim modeli belirsizliği (TBD — §10 araç profili).

---

## 3. Belirsizlik Birikme Kuralı

### 3.1 Konum Belirsizliği Birikimi

Her navigasyon adımında:

```
σ_pos²(t+1) = σ_pos²(t) + σ_IMU_drift² + σ_odometry²
```

Birim: metre², her adım bağımsız gürültü eklenir.

**Parametreler:** `σ_IMU_drift` ve `σ_odometry` değerleri TBD(source: §10 sensör paketi).

### 3.2 Belirsizlik Reset Koşulları

| Reset Tetikleyici | Reset Etkisi | Yeni σ_pos Değeri |
|------------------|--------------|-------------------|
| Landmark eşleşmesi (güven > 0.80) | σ_pos sıfırlanır | Landmark ölçüm belirsizliği |
| Orbital harita fit | σ_pos güncellenir | Fit kalitesine bağlı |
| Statik duraksamada IMU kalibrasyonu | Drift azalır | TBD |

### 3.3 FDIR Tetikleme Eşiği

`σ_pos > §1 tablosu "Yüksek" eşiği` → SC-004 tetiklenir (Detection aşaması).

---

## 4. Veri Kalitesi Degradasyon Protokolü

Ortam ürünü kalite skoru `quality_score < 0.7` ise:

1. **Ürün belirsizliğini yukarı revize et:** `uncertainty_1sigma` alanı genişletilir (otomatik).
2. **Planlayıcıya düşük kalite uyarısı gönder:** `data_quality_flag = LOW` ile birlikte ürün iletilir.
3. **Hard constraint eşiğini daha muhafazakâr uygula:** Nominal eşik yerine worst-case eşik kullanılır.
4. **temporal_class kontrolü:** Düşük kaliteli kaynaktan gelen ürün `temporal_class = predicted` olarak işaretlenir; `historical` olarak kullanılamaz.

**quality_score tanımı:** Kaynak veri çözünürlüğü, zaman tazeliği ve sensor güven skorunun ağırlıklı ortalaması. Hesaplama yöntemi TBD(source: data-platform provenance modülü).

---

## 5. Bağlantılar

| Bağlantı | Belge | Alan |
|----------|-------|------|
| Ortam ürünü belirsizlik alanı | `interfaces/schemas/environment_product.schema.yaml` | `uncertainty_1sigma` |
| Emniyet bütçesi belirsizlik payı | `safety/safety_budget.md` | Enerji bütçe belirsizlik bölümü |
| Dönüş enerjisi hard constraint | `mission-intelligence/constraints/hard_constraints.py` | HC-012, HC-006 |
| Aydınlanma süresi hard constraint | `mission-intelligence/constraints/hard_constraints.py` | HC-009 |
| Lokalizasyon QAR eşiği | `docs/qar/` | QAR-NAV-002 |
| PSR girişi otonomi kuralı | `autonomy/autonomy_matrix.md` | PSR_OPS satırı |

---

## 6. Uygulama Notları

### 6.1 Planlayıcıya Belirsizlik Aktarımı

Planlayıcı her ortam ürününü `uncertainty_1sigma` ile birlikte alır. Rota planlamasında:
- Düşük belirsizlik: nominal davranış
- Orta belirsizlik: güvenlik marjı artırılır
- Yüksek belirsizlik: ilgili alan plandan çıkarılır veya YER onayı istenir

### 6.2 PSR Sınır Güven Skoru

PSR sınır güveni < 0.85 olduğunda PSR girişi YER gerektirir (güven 0.85 üzerinde dahi YER — ancak ek kontrol gerekmez). Güven < 0.70 olduğunda PSR girişi reddedilir.

### 6.3 Enerji Bütçe Hatası

`enerji_bütçe_hatası > 20%` → Hard constraint eşikleri worst-case moduna geçer. Power Mgmt bu kararı verir ve Planner'a iletir (Uyum Notu 3: Power Mgmt sahibi, Planner tüketici).

---

## 7. Dünya Görünürlük Belirsizliği (B5-EK)

### 7.1 Marjinal Durum Belirsizliği

Dünya'nın ufka yakın olduğu koşullarda (elevation < TBD°) geometrik görünürlük hesabı ek belirsizlik kaynaklarına karşı duyarlıdır:

- **Atmosferik refraksiyon (Earth eclipse):** Repo bu etkiyi hesaplamaz. Gerçek Dünya görünürlüğü, Dünya'nın ufka yakın olduğu marjinal durumlarda ±bilinmeyen sapar. Bu etki `uncertainty_minutes` alanında yansıtılmalıdır.
- **Ufuk profil hassasiyeti:** 720-ray horizon hesabı 80m DEM'den üretilir. Gerçek ufuk ile model arasındaki fark görünürlük penceresi başlangıç/bitiş zamanını etkiler.
- **Uygulama kuralı:** Dünya elevation < TBD° olan pencereler `confidence: LOW` olarak işaretlenir; `longest_outage_hours` hesabında bu pencereler worst-case sayılır.

### 7.2 temporal_class Politikası

| Kullanıcı zamanı | temporal_class | Açıklama |
|------------------|---------------|----------|
| Geçmiş (< şimdiki zaman) | `historical` | Gerçekleşmiş geometri — kesin değer |
| Gelecek (≥ şimdiki zaman) | `predicted` | Hesaplanmış geometri — belirsizlik payı uygulanır |

**Kural:** Kullanıcı arayüzünde zaman kaydırıcısı kullanıldığında `temporal_class` otomatik olarak güncellenir. `predicted` etiketli veri `historical` kaynakla karıştırılamaz.

### 7.3 Çözünürlük Belirsizlik Kaynakları

| DEM Çözünürlüğü | Belirsizlik Tipi | Etki |
|-----------------|-----------------|------|
| 80m (temel çözünürlük) | Küçük engel kaçırma | Yerel yol planlamasında gizli engel riski (RR-006 ile hizalı) |
| 300m (site finder hücre) | Site sınır belirsizliği | ±150m sınır belirsizliği — PSR sınır güveni hesabını etkiler |
| 2.7km (global trend) | Büyük ölçek trend | Uzun mesafe enerji/ışık tahmininde sapma |

**Pratikte:** 80m çözünürlük ile hesaplanan PSR sınır güveni skoru, 20m çözünürlükte yeniden hesaplandığında değişebilir. B4 AC-VAL-005 bunu ölçer.

### 7.4 Earth Eclipse Refraksiyon — Bilinen Eksiklik

Referans pipeline (lunar-navigator) Dünya'nın güneş tutulması sırasındaki refraksiyon etkisini modellememektedir. Bu etki:
- Görünürlük penceresi başlangıç/bitiş zamanını ±TBD dakika kaydırabilir
- Marjinal durumlarda (Dünya elevation < 2°) yanlış "görünür" veya "görünmez" kararı üretebilir
- **Azaltma:** Bu pencereler `confidence: LOW` ile işaretlenir ve link planlama hesabında güvenli bant dışı tutulur

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — B5 görevi |
| 0.2 | 2026-11-14 | B5-EK: Dünya görünürlük belirsizliği, temporal_class politikası, çözünürlük kaynakları, refraksiyon eksikliği |
