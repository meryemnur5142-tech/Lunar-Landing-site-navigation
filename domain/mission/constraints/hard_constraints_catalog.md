# status: draft
# owner: luna-ai-architecture
# depends_on: [docs/conops/CONOPS.md, docs/qar/QAR_TABLE.md, docs/adr/ADR-001..ADR-006, docs/architecture/SAFETY_STATE_MACHINE.md]
# open_items: [HC-001 araç eğim limiti TBD(source: §10), HC-002 pürüzlülük RMS TBD(source: §10), HC-004 düzlük varyansı TBD(source: §10), HC-005 tırmanma açısı TBD(source: §10), HC-006 dönüş rezervi Wh TBD(source: §10), HC-007 termal marj eşiği TBD(source: §10 termal model), HC-008 PSR batarya SoC TBD(source: §10), HC-009 min aydınlanma süresi TBD(source: §10), HC-010 maks karanlık aralığı TBD(source: §10), HC-011 şarj olanağı eşiği TBD(source: §10), HC-013 termal limit TBD(source: §10), HC-014 görüş açısı/pencere TBD(source: §10), HC-015 acil erişim mesafesi TBD(source: §10), HC-016 site finder min güneş oranı TBD(source: §10), HC-017 site finder min Dünya görünürlük oranı TBD(source: §10), HC-018 iniş zamanı Dünya görünürlük penceresi doğrulanmış]

# Hard Constraint Kataloğu — LUNA-AI v1.1

## 1. Amaç ve Kapsam

Bu katalog, LUNA-AI görev sisteminin eleme (pass/fail) düzeyindeki hard constraint'lerini tanımlar.
Bir kriter bu listede **Hard** olarak işaretlenmişse hiçbir çok kriterli sıralama skoru onu geçersiz kılamaz.
Soft sınıflandırmalı kriterler performans cezasına yol açar; eleme gerektirmez.

> **Uyum Notu 5:** Önce hard constraint'ler uygulanır; sıralama skoru yalnızca geçen adaylar üzerinde çalışır.
> **Uyum Notu 3:** Enerji/termal eşikler Power Management modülü tarafından hesaplanır ve planlayıcıya bildirilir.
>   Planlayıcı bu değerleri hard constraint olarak uygular — asla bağımsız olarak hesaplamaz.

---

## 2. Kısıt Tablosu

### 2.1 Arazi / İniş Kısıtları

| ID | Ad | Parametre | Operatör | Eşik | Birim | Kaynak / Gerekçe | Faz | Doğrulama Yöntemi |
|---|---|---|---|---|---|---|---|---|
| HC-001 | Maksimum İniş Alanı Eğimi | `max_slope_deg` | ≤ | 15.0 TBD(source: §10) | deg | v1.0 §4.1, QAR-MOB-001 — araç devrilme stabilitesi | landing | analysis |
| HC-002 | Maksimum Yüzey Pürüzlülüğü RMS | `surface_roughness_rms_m` | ≤ | 0.30 TBD(source: §10) | m | v1.0 §4.1, QAR-LND-002 — iniş bacak tasarım limiti | landing | simulation + test |
| HC-003 | Maksimum Kaya / Engel Yoğunluğu | `obstacle_fraction` | ≤ | 0.20 | fraction (0–1) | v1.0 §4.3, QAR-LND-003 — kaya kaçınma başarım limiti | landing, surface_exploration | analysis |
| HC-004 | Minimum İniş Elipsi Düzlüğü | `slope_variance_deg2` | ≤ | TBD(source: §10) | deg² | v1.0 §4.1 — iniş elipsi içi eğim varyansı; düzgün olmayan alanlar elenir | landing | analysis |
| HC-005 | Araç Erişilebilirlik Eğimi | `approach_slope_deg` | ≤ | TBD(source: §10) | deg | v1.0 §4.3, QAR-MOB-002 — çevre profil eğimi ≤ maks tırmanma açısı | surface_exploration, psr_ops | simulation |

### 2.2 Enerji / Termal Kısıtları

| ID | Ad | Parametre | Operatör | Eşik | Birim | Kaynak / Gerekçe | Faz | Doğrulama Yöntemi |
|---|---|---|---|---|---|---|---|---|
| HC-006 | Minimum Dönüş Enerji Rezervi | `return_reserve_wh` | ≥ | TBD(source: §10) | Wh | Uyum Notu 3 — Power Mgmt hesaplar, planlayıcı uygular; HC-012 ile bağlantılı | surface_exploration, psr_ops, return | analysis + simulation |
| HC-007 | Minimum Güvenli Karanlık Tolerans Marjı | `thermal_margin_c` | ≥ | TBD(source: §10 termal model) | °C | Termal model bağımlı; VIPER 50s eşiği evrensel değil — araç tasarımına özel | psr_ops, return, safe_state | analysis |
| HC-008 | PSR Girişinde Minimum Batarya SoC | `battery_soc_pct` | ≥ | TBD(source: §10) | % | v1.0 §5.2, QAR-PWR-001 — PSR içi haberleşme + ısıtma garantisi | psr_ops | test + analysis |

### 2.3 Safe Haven Kısıtları — 7 Kriter (Uyum Notu 2)

> **Uyum Notu 2:** Safe haven değerlendirmesi tam olarak şu 7 kriter üzerinden yapılır.
> Bu 7'nin dışında kriter eklenmez veya çıkarılmaz.

| ID | Ad | Parametre | Operatör | Eşik | Birim | Safe Haven Kriteri | Faz | Doğrulama Yöntemi |
|---|---|---|---|---|---|---|---|---|
| HC-009 | Minimum Kesintisiz Aydınlanma Süresi | `continuous_illumination_hr` | ≥ | TBD(source: §10) | saat | Kriter 1: kesintisiz aydınlanma | safe_state | orbit analysis |
| HC-010 | Maksimum Kabul Edilebilir Karanlık Aralığı | `max_darkness_interval_hr` | ≤ | TBD(source: §10) | saat | Kriter 2: karanlık aralığı | safe_state | orbit analysis |
| HC-011 | Yeniden Şarj Olanağı | `recharge_capacity_wh_per_sol` | ≥ | TBD(source: §10) | Wh/sol | Kriter 3: yeniden şarj — aydınlanma_süresi × panel_verimi ≥ eşik | safe_state | analysis |
| HC-012 | Dönüş Enerjisi Yeterliliği | `return_energy_budget_wh` | ≥ | mesafe_m × tüketim_wh/m + belirsizlik_payı | Wh | Kriter 4: dönüş enerjisi — safe_haven→başlangıç mesafesi × tüketim ≤ rezerv | return, safe_state | simulation |
| HC-013 | Termal Güvenlik (Safe Haven) | `surface_temp_c`, `solar_angle_deg` | within | TBD(source: §10) | °C, deg | Kriter 5: termal güvenlik — güneş açısı ve yüzey sıcaklığı limitleri | safe_state | thermal analysis |
| HC-014 | Haberleşme Görüş Olanağı | `comm_visibility_deg` veya `comm_window_min_per_sol` | ≥ | TBD(source: §10) ° veya TBD(source: §10) dk/sol | deg / dk | Kriter 6: haberleşme — Dünya/relay görüş açısı veya pencere yeterliliği | tüm fazlar | link analysis |
| HC-015 | Acil Erişim Mesafesi | `emergency_route_distance_m` | ≤ | TBD(source: §10) | m | Kriter 7: acil erişim — güvenli rota mesafesi ≤ limit | surface_exploration, psr_ops, return | simulation |

---

## 3. Hard vs Soft Sınıflandırma Tablosu

| ID | Sınıf | Gerekçe |
|---|---|---|
| HC-001 | **Hard** | Araç devrilme riski — kurtarma mümkün değil |
| HC-002 | **Hard** | İniş bacak hasar riski — görev kaybı |
| HC-003 | **Hard** | Kaya kaçınma algoritması garantisi dışında kalır |
| HC-004 | **Hard** | İniş elipsi içi düzgünsüzlük iniş GNC hata bütçesini aşar |
| HC-005 | **Hard** | Araç sıkışma riski — kurtarma imkânsız |
| HC-006 | **Hard** | Araç dönüş enerjisi yetersizse görev kaybı; Uyum Notu 3 |
| HC-007 | **Hard** | Termal marj sıfırın altına düşerse batarya / bileşen hasarı kalıcı |
| HC-008 | **Hard** | PSR içinde yeterli enerji yoksa haberleşme + ısıtma kesilir |
| HC-009 | **Hard** | Şarj penceresi yetersizse safe haven geçersizdir |
| HC-010 | **Hard** | Karanlık tolerans aşılırsa termal survival tehlikeye girer |
| HC-011 | **Hard** | Şarj olanağı yoksa safe haven sürdürülemez |
| HC-012 | **Hard** | Dönüş enerjisi yetersizse araç geri dönemez — HC-006 ile örtüşür |
| HC-013 | **Hard** | Termal limit aşılırsa bileşen arızası kaçınılmaz |
| HC-014 | **Hard** | Haberleşme kesilirse yer müdahalesi mümkün değil; otonom kararlar kısıtlanır |
| HC-015 | **Hard** | Acil erişim imkânı olmayan safe haven, kriz senaryolarında işlevsizdir |

---

## 4. Sınıflandırma Notu

Soft constraint örnekleri (bu katalogda yer almaz, puanlama skorunda işlenir):
- Bilimsel değer puanı
- Yüzey örneği çeşitliliği
- Telemetri kalitesi
- İletişim bant genişliği tercihi

---

## 4b. Site Finder Metrikleri — Ek Hard Constraint'ler (A1-EK)

> **Kaynak:** `daniel27-space/lunar-navigator` site finder modülü (eğim/güneş/Dünya/PSR metrikleri).
> **Uyum Notu 5 hatırlatıcısı:** Site finder sıralaması güvenlik kararı vermez.
> Ağırlıklı toplam (sun × w1 + earth × w2 + ...) tek başına güvenlik kararı veremez.
> Site finder çıktısı yalnızca HC geçen adayları sıralamak için kullanılır.

| ID | Ad | Parametre | Operatör | Eşik | Birim | Kaynak / Gerekçe | Faz | Doğrulama Yöntemi |
|---|---|---|---|---|---|---|---|---|
| HC-016 | Site Finder Min Güneş Oranı | `site_sun_fraction` | ≥ | TBD(source: §10) | fraction (0–1) | lunar-navigator site finder; güneş oranı < eşik → şarj yetersiz | surface_exploration, safe_state | orbit analysis |
| HC-017 | Site Finder Min Dünya Görünürlük Oranı | `site_earth_fraction` | ≥ | TBD(source: §10) | fraction (0–1) | lunar-navigator site finder; Dünya görünürlüğü < eşik → haberleşme riski | surface_exploration, safe_state | orbit analysis |
| HC-018 | İniş Zamanı Dünya Görünürlük Penceresi | `earth_visibility_confirmed` | == | true | bool | Dünya görünürlük penceresi doğrulanmış [kaynak: earth_visibility_windows.schema.yaml]; iniş zamanı planlamasında zorunlu | landing | link analysis |

**Hard vs Soft:** HC-016, HC-017, HC-018 → **Hard** (eleme). Site finder sıralama skoru → Soft (ceza).

---

## 5. Versiyon ve Değişim Yönetimi

Bir HC eşiği değiştikçe `hard_constraints_catalog.yaml` güncellenir ve `schema_version` MINOR arttırılır.
Yeni HC eklenmesi MINOR, mevcut HC kaldırılması MAJOR versiyon değişikliğidir.
