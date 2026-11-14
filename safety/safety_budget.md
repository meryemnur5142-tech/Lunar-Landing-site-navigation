# status: draft
# owner: luna-ai-architecture
# depends_on:
#   - domain/mission/constraints/hard_constraints_catalog.yaml  (HC-006, HC-007, HC-008)
#   - interfaces/schemas/resource_state.schema.yaml
#   - interfaces/schemas/earth_visibility_windows.schema.yaml  (A4-EK: haberlesme kesinti butcesi)
#   - docs/architecture/SAFETY_STATE_MACHINE.md
# open_items:
#   - return_reserve_wh hesaplama modeli TBD(source: §10 Power Mgmt arac parametreleri)
#   - thermal_margin_c kritik bilesen listesi TBD(source: §10)
#   - uncertainty_margin_pct deger TBD (tahminen +%20, arac testinden dogrulanacak)
#   - guncelleme_periyodu TBD (navigasyon guncelleme periyodu ile senkron)
#   - max_communication_outage_hours TBD(source: hardware + repo lunar-navigator 60-gun pencere verisi)

# Emniyet Bütçesi Mekanizması — LUNA-AI v1.1

## 1. Mekanizma Tanımı ve Sahiplik (Uyum Notu 3)

```
Power Management  ──hesaplar──►  Planlayıcıya bildirir (resource_state.schema.yaml)
                                        │
                                        ▼
                           Planlayıcı hard constraint olarak uygular
                           (HC-006, HC-007 — Uyum Notu 5)
```

**Planlayıcı bütçeyi HESAPLAMAZ.** Yalnızca `resource_state` mesajından alınan
değerleri hard constraint olarak uygular.

İki bütçe boyutu tanımlanmıştır:
1. **Dönüş Enerji Rezervi** — Power Management sahibi
2. **Termal Marj** — Thermal Management sahibi (Power Management ile entegre)
3. **Maksimum Haberleşme Kesinti Süresi** — Communication Management bildirir (A4-EK)

---

## 2. Dönüş Enerji Rezervi

### 2.1 Hesaplama Formülü

```
return_reserve_wh =
    f(mesafe_m, zemin_direnci, hiz_ms, isitici_yuku_w, belirsizlik_payi)

= (mesafe_m × enerji_per_m_wh/m)
  + (isitici_yuku_w × tahmini_donus_suresi_s / 3600)
  + belirsizlik_payi_wh

Burada:
  enerji_per_m_wh/m  = TBD(source: §10 araç teker/motor parametreleri)
  isitici_yuku_w     = resource_state.heater_power_w (Power Mgmt sağlar)
  belirsizlik_payi   = return_reserve_wh * belirsizlik_pct
  belirsizlik_pct    = TBD(source: §10 araç testi) — tahminen +%20
```

### 2.2 Girdi Kaynakları

| Parametre | Sağlayan Modül | Şema/Referans |
|---|---|---|
| `mesafe_m` (anlık konum → safe haven) | Navigation | `vehicle_pose.schema.yaml` |
| `zemin_direnci` (arazi haritası) | Planetary Data | `environment_product.schema.yaml` |
| `isitici_yuku_w` | Power Management | `resource_state.schema.yaml` |
| `belirsizlik_payi` | Power Management | §10 araç test parametresi |

### 2.3 Güncelleme Kuralı

Her navigasyon güncellemesiyle senkron olarak yeniden hesaplanır.
Güncelleme periyodu: TBD(source: §10 navigasyon sistemi frekansı).

Uzaklaştıkça mesafe belirsizliği artar → rezerv tahmin hatası büyür →
belirsizlik payı dinamik güncellenmeli:

```
belirsizlik_payi_wh(t) = base_margin_wh + k × position_uncertainty_m(t)
  k = TBD(source: §10)
```

### 2.4 HC-006 ile İlişki

`resource_state.return_reserve_wh` alanı HC-006 eşiğiyle karşılaştırılır.
HC-006 eşiği Power Management tarafından belirlenir (TBD §10).
Planlayıcı karşılaştırır ve hard constraint olarak uygular.

---

## 3. Termal Marj

### 3.1 Hesaplama Formülü

```
thermal_margin_c = min(T_limit_c[i] - T_current_c[i])  for i in kritik_bilesenleri

Kritik bileşenler:
  - batarya           (T_limit: TBD §10)
  - ana_bilgisayar    (T_limit: TBD §10)
  - motor_suruculeri  (T_limit: TBD §10)
```

Termal model: araç tasarımına özgü. VIPER 50s toleransı birebir aktarılmaz. TBD(source: §10).

### 3.2 HC-007 ile İlişki

`resource_state.thermal_margin_c` alanı HC-007 eşiğiyle karşılaştırılır.
PSR_OPS girişinde HC-007 zorunlu kontrol listesi madde 2'dir (phase_state_machine.md §4.3.1).

---

## 4. Bütçe İhlali → FDIR Tetikleme

| Durum | Eşik | FDIR Aksiyonu | Güvenlik Durumu Geçişi |
|---|---|---|---|
| `return_reserve_wh < HC-006.threshold × 1.1` | Erken uyarı (%110) | Planlayıcıya bildir; mevcut fazı sürdür | CAUTION |
| `return_reserve_wh <= HC-006.threshold` | Kritik | Zorunlu RETURN fazı tetikle | RETURN_REQUIRED |
| `thermal_margin_c < 5°C` | Uyarı (eşik TBD §10) | Isıtıcı önceliklendirmesi | CAUTION |
| `thermal_margin_c <= 0°C` | Kritik | Survival modu; tüm bilim devre dışı | SURVIVAL |
| `comm_outage_elapsed_hr >= max_communication_outage_hours × 0.9` | Erken uyarı | Planlayıcıya bildir | CAUTION |
| `comm_outage_elapsed_hr >= max_communication_outage_hours` | Kritik | RETURN veya SAFE_STATE | RETURN_REQUIRED |

> **Not:** Güvenlik durumu geçişleri `docs/architecture/SAFETY_STATE_MACHINE.md`'de tanımlanmıştır.
> Bu tablo yalnızca bütçe ihlalinin tetiklediği FDIR aksiyonlarını gösterir.

---

## 5. Belirsizlik Birikimi Modeli

```
Zaman / mesafe arttıkça:
  position_uncertainty_m(t) ↑
    → mesafe tahmin hatası ↑
      → return_reserve_wh hesap hatası ↑
        → güvenlik marjı dinamik güncellenmeli

Güncelleme kuralı: her navigasyon güncellemesinde yeniden hesapla.
Lokalizasyon düzeltmesi (landmark, bölge tespiti) sonrasında belirsizlik sıfırlanır.
```

---

## 6. Maksimum Haberleşme Kesinti Süresi (A4-EK)

**Sahip:** Communication Management — hesaplar ve bildirir.
**Tüketici:** Power Management ve Planlayıcı — hard constraint olarak uygular (Uyum Notu 3 korunur).

```
max_communication_outage_hours = TBD(source: hardware + repo lunar-navigator 60-gün pencere verisi)
```

**Kaynak:** `daniel27-space/lunar-navigator` — 60-gün güneş/Dünya penceresi analizi,
"longest night/communication gap" metriği.

**Şema referansı:** `interfaces/schemas/earth_visibility_windows.schema.yaml`
(en uzun kesinti süresi: `longest_outage_duration_hours` alanı).

**Neden TBD:** Gerçek değer araç donanım (alıcı/verici) duyarlılığına bağlıdır.
Repo metriği referans tavan; operasyonel eşik §10 donanım verisiyle belirlenecek.

---

## 7. HC Referansları

| HC ID | İlgili Parametre | Bu Dosyadaki Rol |
|---|---|---|
| HC-006 | `return_reserve_wh` | §2'nin hesaplama çıktısı; kritik eşik |
| HC-007 | `thermal_margin_c` | §3'ün hesaplama çıktısı; kritik eşik |
| HC-008 | `battery_soc_pct` | PSR girişi öncesi SoC kontrolü |
| HC-014 | `comm_visibility_deg` / pencere | §6 haberleşme kesinti bütçesiyle ilişkili |
