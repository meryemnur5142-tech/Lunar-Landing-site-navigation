# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/schemas/vehicle_command.schema.yaml, mission-intelligence/constraints/hard_constraints.py, docs/conops/]
# open_items: [authority_level field alignment with vehicle_command.schema.yaml pending schema finalization, ACL timeout durations TBD(source: §10)]

# Otonomi Matrisi — LUNA-AI v1.1

## Amaç

Bu belge, LUNA-AI aracının hangi koşullarda hangi kararları bağımsız alacağını (OTN), yer onayı bekleneceğini (YER), işlemin o fazda yasak olduğunu (YAS) veya yalnızca FDIR abort senaryosunda devreye gireceğini (ACL) tanımlar.

**Önemli:** Görev fazları (CRUISE/LANDING/SURFACE_EXPLORATION/PSR_OPS/RETURN/SAFE_STATE) ile güvenlik durumları (NORMAL/CAUTION/RETURN_REQUIRED/SURVIVAL) AYRI eksenlerdir. Bu matris görev fazı eksenini kullanır.

---

## Sembol Tanımları

| Sembol | Anlam | Açıklama |
|--------|-------|----------|
| **OTN** | Otonom | Araç kendi karar verir, yer onayı gerekmez |
| **YER** | Yer Onaylı | Komut bekler; süre aşımında bekle veya safe haven'a yönel |
| **YAS** | Yasak | O görev fazında bu karar türü uygulanamaz |
| **ACL** | Acil-Otonom | Yalnızca FDIR abort senaryosunda; normal operasyonda YER veya YAS |

---

## Ana Matris — Normal Operasyon

> **Not:** Hard constraints (HC-001..015) her durumda önce değerlendirilir. Matris, HC kümesi geçildikten sonraki otorite seviyesini gösterir.

| Görev Fazı | Rota Değişikliği | Bilimsel Hedef Terk | PSR Girişi | Safe Haven Değişikliği | Acil Dönüş | Bilim Yükü Açma/Kapama | Mod Değişikliği |
|------------|-----------------|---------------------|------------|----------------------|------------|------------------------|-----------------|
| **CRUISE** | YAS | YAS | YAS | YAS | ACL | YAS | YER |
| **LANDING** | YAS | YAS | YAS | YAS | ACL | YAS | ACL |
| **SURFACE_EXPLORATION** | OTN | OTN | YER | YER | ACL | OTN | OTN |
| **PSR_OPS** | OTN¹ | YER | YAS² | YER³ | ACL | YER | OTN |
| **RETURN** | OTN | YAS | YAS | YER | ACL | OTN | OTN |
| **SAFE_STATE** | YAS | YAS | YAS | YER | ACL | YAS | YER |

**Dipnotlar:**

¹ PSR_OPS rota değişikliği: Yalnızca pre-approved PSR haritası sınırları içinde OTN; sınır dışına çıkış YER gerektirir.

² PSR girişi: Dönüş rezervi (HC-006) doğrulanmadan giriş yasaktır. SURFACE_EXPLORATION'dan PSR_OPS'a geçiş her zaman YER.

³ Safe haven değişikliği PSR içinde: Koordinatlar veya birincil güzergah güncellenemez (PSR içinde orbital harita güncellemesi mümkün değil). Yedek safe haven seçimi (SC-005 tetiklenirse) ACL.

---

## İletişim Kaybı Matrisi

Telemetri linki koptuğunda aynı karar türleri için otorite seviyeleri:

| Görev Fazı | Rota Değişikliği | Bilimsel Hedef Terk | PSR Girişi | Safe Haven Değişikliği | Acil Dönüş | Bilim Yükü Açma/Kapama | Mod Değişikliği |
|------------|-----------------|---------------------|------------|----------------------|------------|------------------------|-----------------|
| **CRUISE** | YAS | YAS | YAS | YAS | ACL | YAS | ACL |
| **LANDING** | YAS | YAS | YAS | YAS | ACL | YAS | ACL |
| **SURFACE_EXPLORATION** | OTN | OTN | BEKLE⁴ | OTN⁵ | ACL | OTN | OTN |
| **PSR_OPS** | OTN⁶ | ACL⁷ | YAS | ACL⁸ | ACL | ACL | OTN |
| **RETURN** | OTN | YAS | YAS | OTN | ACL | OTN | OTN |
| **SAFE_STATE** | YAS | YAS | YAS | ACL | ACL | YAS | ACL |

**Dipnotlar (İletişim Kaybı):**

⁴ PSR girişi link kaybı sırasında: Araç bekler (pre-planned abort trigger yoksa). Bekleme süresi: TBD(source: §10 — link recovery window). Süre aşımında PSR girişi iptal, güvenli bekle.

⁵ Safe haven değişikliği (SURFACE_EXPLORATION, link yok): Pre-planned yedek safe haven listesinden OTN seçim. Listede yer yoksa mevcut koordinatta bekle.

⁶ PSR_OPS rota değişikliği (link yok): Pre-approved sınırlar içinde devam OTN. Enerji uyarısı tetiklenirse ACL dönüş.

⁷ Bilimsel hedef terk (PSR, link yok + FDIR uyarı): ACL — dönüş önceliklidir.

⁸ Safe haven değişikliği (PSR, link yok): Yalnızca enerji kritik + birincil rota tıkandıysa ACL yedek safe haven seçimi.

**Özel Durum: PSR içinde link koptu + enerji kritik:**
→ ACL acil dönüş tetiklenir. FDIR → RETURN_REQUIRED geçişi → Power Mgmt dönüş rezervi onaylar → Planner rota üretir.

---

## Pre-Planned Abort Trigger Listesi

Aşağıdaki koşullardan herhangi biri gerçekleştiğinde araç yer onayı beklemeksizin belirtilen eylemi uygular:

| Trigger ID | Koşul | Eylem | Faz |
|------------|-------|-------|-----|
| ABT-001 | `return_reserve_wh < HC-006_threshold` | ACL acil dönüş başlat | PSR_OPS, SURFACE_EXPLORATION |
| ABT-002 | `position_uncertainty_m > QAR-NAV-002_threshold` | Dur, landmark ara, başarısızsa dönüş | SURFACE_EXPLORATION, PSR_OPS |
| ABT-003 | `thermal_margin_c < 0` | ACL ısıtıcı maks + dönüş değerlendirmesi | Tüm yüzey fazları |
| ABT-004 | `link_timeout > TBD(source: §10)` AND faz=PSR_OPS AND `energy_critical=true` | ACL acil dönüş | PSR_OPS |
| ABT-005 | `safe_haven_route_blocked=true` AND `backup_safe_haven=none` | SURVIVAL modu hazırlığı | Tüm yüzey fazları |
| ABT-006 | `fdir_abort_flag=true` | ACL göreve göre eylem (§4 FDIR ağacı) | Tüm fazlar |

---

## Operatör Onayı Zorunlu Kararlar (YER Hücreleri)

Aşağıdaki kararlar her koşulda yer operatörü onayı gerektirir:

1. **PSR girişi** (tüm fazlardan) — Dönüş rezervi, termal durum, haberleşme penceresi doğrulanmadan girilemez
2. **Safe haven değişikliği** (SURFACE_EXPLORATION, PSR_OPS, RETURN, SAFE_STATE'de) — 7 kriter doğrulaması yer tarafı sorumluluğundadır
3. **Bilimsel hedef terk** (PSR_OPS'ta) — Bilimsel öncelik değişikliği görev otoritesi kararıdır
4. **Mod değişikliği** (CRUISE, SAFE_STATE'de) — Kritik faz geçişleri manuel onay gerektirir
5. **PSR_OPS rota değişikliği** (sınır dışı) — Harita güncellemesi yer tarafı doğrulaması gerektirir

---

## Bağlantı: vehicle_command.schema.yaml

Bu matristeki otorite seviyeleri `interfaces/schemas/vehicle_command.schema.yaml` → `authority_level` alanıyla hizalıdır:
- `OTN` → `authority_level: "autonomous"`
- `YER` → `authority_level: "ground_approved"`
- `ACL` → `authority_level: "emergency_autonomous"`
- `YAS` → komut gönderimi `authority_level` validasyonunda reddedilir

---

---

## Görev Planlama Kararları — Yer Onayı Zorunlu (B1-EK)

Aşağıdaki kararlar, otonomi matrisi dışında ancak v1.2 entegrasyon kapsamında operatör onayı (YER) gerektiren ek karar türleridir:

| Karar Türü | Otorite | Gerekçe |
|-----------|---------|---------|
| **Site finder kararı** | YER | Nihai iniş bölgesi seçimi görev otoritesi kararıdır; algoritmik sıralama (site finder weighted score) girdi sağlar, karar vermez |
| **"When to land" / iniş penceresi seçimi** | YER | Güneş/Dünya geometrisi pencere önerisi sunar; iniş zamanı seçimi insansız görev için dahi yer kontrolü onayı gerektirir |
| **Çoklu bölge karşılaştırması / bölge seçimi** | YER | 2–5 bölge arasından nihai seçim görev otoritesi kararıdır |
| **Geometri güncellemesi (tahmin iyileştirmesi)** | OTN | Hesaplama iyileştirmesi (JPL Horizons güncellemesi vb.) otonom olabilir; bölge veya zaman seçimi değiştirilmiyorsa onay gerekmez |

**Önemli ayrım:** Site finder algoritması ve "when to land" analizi karar *önerisi* üretir. Nihai bölge-zaman seçimi her koşulda YER'dir. Geometrik hesaplama güncellemesi (örn. yeni ephemeris verisiyle yeniden hesaplama) ise OTN olabilir.

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — B1 görevi |
| 0.2 | 2026-11-14 | B1-EK: Site finder, iniş penceresi, çoklu bölge karşılaştırması YER kararları eklendi |
