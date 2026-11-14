# status: draft
# owner: luna-ai-architecture
# depends_on:
#   - docs/architecture/SAFETY_STATE_MACHINE.md  (çapraz referans; bu dosya güvenlik durumunu TANIMLAMAZ)
#   - domain/mission/constraints/hard_constraints_catalog.yaml
#   - docs/qar/QAR_TABLE.md  (QAR-NAV-002)
#   - interfaces/schemas/resource_state.schema.yaml
# open_items:
#   - PSR_OPS entry checklist madde 4 eşiği QAR-NAV-002.target TBD
#   - SURFACE_EXPLORATION→PSR_OPS otorite seviyesi B1 otonomi matrisine bağlı TBD
#   - CRUISE→LANDING geçiş koşulları GNC arayüzüne bağlı TBD(source: §10)

# Görev Fazı Durum Makinesi — LUNA-AI v1.1

## 1. Kapsam ve Ayırım

**ÖNEMLİ (Uyum Notu 1):** Bu dosya yalnızca **görev fazı eksenini** tanımlar.

| Eksen | Tanımlandığı Yer | Bu Dosyadaki Rolü |
|---|---|---|
| Görev fazı | Bu dosya | Tam tanım |
| Güvenlik durumu | `docs/architecture/SAFETY_STATE_MACHINE.md` | Yalnızca çapraz ilişki matrisinde referans verilir |

İki eksen asla birleştirilmez. Faz makinesinin güvenlik durumu ile etkileşimi yalnızca
§5 Çapraz İlişki Matrisinde gösterilir.

---

## 2. Faz Tanımları

| Faz | Tanım | Araç Konumu |
|---|---|---|
| `CRUISE` | Yörüngede iniş öncesi; GNC Ay yörüngesinde | Uzay (yörünge) |
| `LANDING` | İniş GNC aktif, yüzey teması öncesi; powered descent | Alçalma yolunda |
| `SURFACE_EXPLORATION` | Nominal yüzey keşfi; PSR dışı bölge | Yüzey, aydınlanmış alan |
| `PSR_OPS` | PSR (Kalıcı Gölge Bölgesi) içi operasyon | Kalıcı gölge |
| `RETURN` | Safe haven'a aktif dönüş hareketi | Yüzey, dönüş güzergahı |
| `SAFE_STATE` | Şarj/termal toparlanma; haberleşme penceresi bekleme | Safe haven konumu |

---

## 3. Faz Geçiş Diyagramı

```
CRUISE
  │ iniş koridoru onayı + HC-001 adayı geçti
  ▼
LANDING
  │ yüzey teması onaylandı + araç stabil
  ▼
SURFACE_EXPLORATION ◄──────────────────────────────┐
  │ PSR_OPS onayı + 6-madde checklist OK            │
  ▼                                                  │
PSR_OPS ──► (dönüş koşulu) ──► RETURN ──► SAFE_STATE
  │                                          │
  │ (şarj + termal + hedef tamamlandı)       │
  └──────────────────────────────────────────┘
  (herhangi bir fazdan acil)
  RETURN ◄── (FDIR: emergency_autonomous)
  SAFE_STATE ◄── (survival modu)
```

---

## 4. Faz Detayları

### 4.1 CRUISE

**İzin verilen geçişler:**
- CRUISE → LANDING (nominal)

**Geçiş koşulları (CRUISE → LANDING):**
- Iniş koridoru hesaplandı ve onaylandı
- İniş adayı HC-001, HC-002, HC-003 geçti (ön analiz)
- Araç yakıt bütçesi yeterli TBD(source: §10)
- Haberleşme HC-014 karşılanıyor

**Girişte zorunlu kontrol:**
- Navigasyon sistemi aktif
- Telemetri nominal

**Çıkış koşulu:**
- Powered descent başladı; GNC iniş moduna geçti

---

### 4.2 LANDING

**İzin verilen geçişler:**
- LANDING → SURFACE_EXPLORATION (başarılı iniş)
- LANDING → SAFE_STATE (iniş sonrası sistem kontrolü)

**Geçiş koşulları (LANDING → SURFACE_EXPLORATION):**
- Yüzey teması ve stabilite onaylandı
- Tüm HC-001..HC-005 iniş alanı kontrolü geçti
- Sistem sağlık kontrolü nominal

**Girişte zorunlu kontrol:**
- GNC iniş algoritması aktif
- İniş radar/lidar aktif

**Çıkış koşulu:**
- Araç yüzeyde kararlı durumda
- Tüm iniş kısıtları karşılandı

---

### 4.3 SURFACE_EXPLORATION

**İzin verilen geçişler:**
- SURFACE_EXPLORATION → PSR_OPS (onaylı PSR girişi)
- SURFACE_EXPLORATION → RETURN (dönüş koşulu karşılandı)
- SURFACE_EXPLORATION → SAFE_STATE (şarj/termal gereksinimi)

**Geçiş koşulları (SURFACE_EXPLORATION → PSR_OPS):**
Bkz. §4.3.1 PSR_OPS Giriş Öncesi Zorunlu Kontrol Listesi.

**Geçiş koşulları (SURFACE_EXPLORATION → RETURN):**
- `resource_state.return_reserve_wh <= HC-006.threshold * 1.1` (erken uyarı)
- veya yer komutu (ground_approved)
- veya FDIR tetiklemesi (emergency_autonomous)

**Girişte zorunlu kontrol:**
- Safe haven koordinatı yüklenmiş
- HC-014 haberleşme karşılanıyor
- Navigasyon lokalizasyon sistemi aktif

**Çıkış koşulu:**
- PSR girişi onaylandı (checklist) VEYA dönüş koşulu karşılandı

#### 4.3.1 PSR_OPS Giriş Öncesi Zorunlu Kontrol Listesi

Aşağıdaki 6 maddenin **tamamı** karşılanmadan PSR_OPS fazına geçilemez:

1. **Dönüş rezervi:** `resource_state.return_reserve_wh >= HC-006.threshold`
   - Power Management onayı gerekir (Uyum Notu 3)
2. **Termal marj:** `resource_state.thermal_margin_c >= HC-007.threshold`
   - Thermal Management onayı gerekir
3. **Haberleşme penceresi:** `comm_window >= HC-014.threshold`
   - veya pre-planned abort trigger tanımlı (uplink kesildiğinde otomatik RETURN)
4. **Lokalizasyon belirsizliği:** `vehicle_pose.position_uncertainty_m <= QAR-NAV-002.target`
   - Navigasyon sistemi onayı gerekir
5. **Bilimsel hedef onayı:** Yer segmenti onayı (ground_approved)
   - veya otonom karar matrisi (B1 otonomi matrisine bağlı TBD)
6. **Safe haven yedek koordinatı:** En az bir HC-009..HC-015 onaylı aday yüklenmiş

---

### 4.4 PSR_OPS

**İzin verilen geçişler:**
- PSR_OPS → RETURN (dönüş koşulu veya FDIR)
- PSR_OPS → SAFE_STATE (acil survival — FDIR emergency_autonomous)

**Geçiş koşulları (PSR_OPS → RETURN):**
- `resource_state.return_reserve_wh <= HC-006.threshold * 1.1` (%10 erken uyarı eşiği)
- veya bilimsel hedef tamamlandı
- veya yer komutu (emergency_return)
- veya FDIR tetiklemesi

**Geçiş koşulları (PSR_OPS → SAFE_STATE — acil):**
- Yalnızca FDIR: `resource_state.power_mode == survival` ve dönüş enerjisi yetersiz
- Güvenlik durumu SURVIVAL iken (çapraz ilişki matrisine bkz. §5)

**Girişte zorunlu kontrol:**
- §4.3.1 checklist tamamlandı ve onaylandı (vehicle_command.psr_entry_checklist_complete: true)

**Çıkış koşulu:**
- Dönüş rezervi %110 eşiğine ulaştı VEYA hedefler tamamlandı VEYA FDIR tetikledi

---

### 4.5 RETURN

**İzin verilen geçişler:**
- RETURN → SAFE_STATE (safe haven'a ulaşıldı)
- RETURN → SURFACE_EXPLORATION (dönüş iptal + yeterli enerji; yer onayı gerekir)

**Geçiş koşulları (RETURN → SAFE_STATE):**
- Araç safe haven koordinatına ulaştı (HC-015 mesafe karşılandı)
- HC-009..HC-013 safe haven kriterleri karşılandığı doğrulandı

**Geçiş koşulları (RETURN → SURFACE_EXPLORATION):**
- Yer segmenti onayı (ground_approved)
- `resource_state.return_reserve_wh >= HC-006.threshold * 1.5` (güvenli marj)
- Termal marj nominal

**Girişte zorunlu kontrol:**
- Dönüş güzergahı hesaplandı
- Safe haven koordinatı yüklenmiş

**Çıkış koşulu:**
- Safe haven'a ulaşıldı

---

### 4.6 SAFE_STATE

**İzin verilen geçişler:**
- SAFE_STATE → SURFACE_EXPLORATION (toparlanma tamamlandı; yer onayı)
- SAFE_STATE → LANDING (yalnızca görev iptalinde; yer onayı)

**Geçiş koşulları (SAFE_STATE → SURFACE_EXPLORATION):**
- `resource_state.state_of_charge_pct >= HC-008.threshold` (tam şarj için TBD)
- `resource_state.thermal_margin_c >= HC-007.threshold`
- Yer segmenti yeni görev paketi gönderdi (mission_package.schema.yaml)
- HC-014 haberleşme penceresi aktif

**Girişte zorunlu kontrol:**
- Safe haven HC-009..HC-015 kriterleri karşılandı
- Şarj sistemi aktif

**Çıkış koşulu:**
- Yer segmenti onayı + enerji/termal toparlanma tamamlandı

---

## 5. Güvenlik Durumu Çapraz İlişki Matrisi (Uyum Notu 1)

Güvenlik durumları `docs/architecture/SAFETY_STATE_MACHINE.md`'de tanımlanmıştır.
Bu tablo yalnızca faz–durum etkileşimini gösterir.

| Faz \ Güvenlik Durumu | NORMAL | CAUTION | RETURN_REQUIRED | SURVIVAL |
|---|---|---|---|---|
| CRUISE | Geçerli | Geçerli | Geçerli | Geçerli |
| LANDING | Geçerli | Geçerli | Zorunlu Geçiş: iniş iptal + yörüngeye dön | Zorunlu Geçiş: acil iptal |
| SURFACE_EXPLORATION | Geçerli | Geçerli; bilim kısıtlı | Zorunlu Geçiş: → RETURN | Zorunlu Geçiş: → SAFE_STATE |
| PSR_OPS | Geçerli | Geçerli; erken uyarı | Zorunlu Geçiş: → RETURN (acil) | Zorunlu Geçiş: → RETURN veya → SAFE_STATE (enerji yetersizse) |
| RETURN | Geçerli | Geçerli; hız artır | Geçerli; devam et | Zorunlu: hız+ısıtıcı optimizasyonu |
| SAFE_STATE | Geçerli | Geçerli; şarj öncelikli | Geçerli; devam şarj | Geçerli; minimum güç modu |

**Zorunlu Geçiş Örnekleri:**

- PSR_OPS + SURVIVAL → Dönüş enerjisi yeterliyse: → RETURN; yetersizse: → SAFE_STATE (en yakın)
- SURFACE_EXPLORATION + RETURN_REQUIRED → derhal → RETURN (planlayıcı görevi bırakır)
- LANDING + RETURN_REQUIRED → iniş iptal komutu (yakıt yeterliyse yörüngeye çekil)
