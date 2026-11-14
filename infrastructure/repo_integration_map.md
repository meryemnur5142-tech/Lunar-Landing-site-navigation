---
status: draft
owner: luna-ai-architecture
depends_on:
  - domain/mission/constraints/hard_constraints_catalog.yaml  (A1-EK: HC-016..HC-018)
  - interfaces/schemas/environment_product.schema.yaml  (A2-EK: terrain_resolution, ephemeris_validity_range)
  - interfaces/schemas/earth_visibility_windows.schema.yaml
  - interfaces/schemas/multi_site_geometry_product.schema.yaml
  - interfaces/schemas/landing_window_product.schema.yaml
  - domain/mission/phase_state_machine.md  (A3-EK: LANDING giris kosullari)
  - safety/safety_budget.md  (A4-EK: max_communication_outage_hours)
open_items:
  - repo submodule path TBD (dogrudan submodule mu, fork mu, referans mi — entegrasyon karari)
  - production migration schedule TBD
  - GPU ray-marching browser→flight segment bridge TBD(source: §10 araç bilgisayar kapasitesi)
---

# Repo Entegrasyon Haritası — lunar-navigator → LUNA-AI

**Kaynak:** `daniel27-space/lunar-navigator` (NASA Space Apps Challenge 2026)
**Doğrulama:** JPL Horizons ±0.001°, NASA GSFC r=0.988/0.993

**Strateji:** Referans implementasyon — kopyalanmaz, bağlanır.
Hackathon prototipi güçlü algoritmik temel sunuyor; LUNA-AI üretim segmentine
doğrudan gömülmez, referans alınır ve araç-güvenli arayüzlerle sarılır.

---

## 1. Bileşen Haritası

| Repo Modülü | LUNA-AI Hedefi | Entegrasyon Türü | Uyarlama Notu |
|---|---|---|---|
| `pipeline/ephem/` (SPICE DE440) | `data-platform/processing/ephemeris/` | Referans | Değişmeden alınır |
| `pipeline/terrain/horizon.py` + `web/src/lib/horizon.ts` (720-ray) | `data-platform/processing/horizon/` | Referans | Değişmeden alınır |
| Güneş/Dünya disk görünürlüğü hesabı | `data-platform/processing/visibility/` | Referans | Değişmeden alınır |
| 3B GPU gölge ray-marching | `apps/ground-control/` prototip UI | Prototip korunur | Üretim öncesi review gerekir; browser-only → flight bridge TBD |
| Site finder (eğim/güneş/Dünya/PSR) | `mission-intelligence/candidate-filter/` | Referans; sıralama yeniden düzenlenir | Uyum Notu 5: sıralama güvenlik kararı vermez; HC eleme önce gelir |
| "When to land" (7/14/30 gün) | `mission-intelligence/landing-window-optimizer/` | Doğrudan kullanılabilir | `landing_window_product.schema.yaml` arayüzüyle sarılır |
| Çoklu bölge karşılaştırması (2–3) | `mission-intelligence/multi-site-time-comparator/` | Genişletilir | 2–3 → 5 bölge; `multi_site_geometry_product.schema.yaml` |
| 60-gün güneş/Dünya penceresi + en uzun gece/kesinti | Güvenlik bütçesi §4.7 Haberleşme + §4.5 Termal | Doğrudan kullanılabilir | Uyum Notu 6: görünürlük ≠ link planlama |
| `docs/DATA_CONTRACT.md` | A2 veri sözleşmeleri (`interfaces/schemas/`) | Girdi | Türetildi; genişletildi |
| `docs/VALIDATION.md` | B4 kabul kriterleri | Doğrulama kanıtı | JPL/NASA GSFC/Gläser referansları |

---

## 2. Değişmeden Alınan / Uyarlanan / Yeniden Yazılan

### Değişmeden Alınan
- `pipeline/ephem/` — SPICE DE440 efemeris işlem hattı
- `pipeline/terrain/horizon.py` ve `horizon.ts` — 720-ray ufuk tarama algoritması
- Güneş/Dünya disk görünürlüğü hesabı
- "When to land" pencere hesaplama mantığı

### Uyarlanan
- **Site finder sıralaması:** HC eleme önce uygulanır; ağırlıklı toplam yalnızca geçen adayları sıralar (Uyum Notu 5)
- **Çoklu bölge karşılaştırması:** 2–3 bölgeden 5 bölgeye genişletildi; `multi_site_geometry_product.schema.yaml` arayüzüyle paketlendi
- **60-gün pencere çıktısı:** `earth_visibility_windows.schema.yaml` ve `safety_budget.md §6` arayüzlerine bağlandı

### Üretim Öncesi Review Gereken
- **GPU ray-marching:** Browser-only prototip; flight segment köprüsü TBD (araç bilgisayarı GPU kapasitesi §10)

### Yeniden Yazılan
- Yok (v1.1 kapsamında)

---

## 3. Repo'nun Bilinen Sınırları — LUNA-AI'de Nasıl Ele Alınır

| Sınır | LUNA-AI Çözümü |
|---|---|
| Çözünürlük: 80m / 300m / 2.7km | A2 `terrain_resolution` alanında zorunlu; planlayıcıya açık bildirilir; gizlenmez (Uyum Notu 7) |
| Zaman aralığı: 2024–2035 (SPICE DE440) | A2 `ephemeris_validity_range` alanında zorunlu; bu aralık dışı ürün reddedilir |
| Observer height hassasiyeti ("a mast a metre taller can halve the longest night") | B2 senaryo; B3 risk kaydı; operasyonel araç yüksekliği §10'dan alınır |
| Earth eclipse refraksiyon ihmalı | B3 risk kaydı; belirsizlik kaynağı; `uncertainty_minutes` alanında yansıtılır |
| Site finder 300m hücre çözünürlüğü | B3 risk kaydı; A1 HC-001..HC-005 not alanında belirtildi; 80m doğrulama gerekebilir |

---

## 4. Önemli Uyum Notları

| Uyum Notu | İçerik | Bu Belgedeki Yansıması |
|---|---|---|
| **Uyum Notu 5** | Önce hard constraint eleme; sıralama skoru elemeyi atlayamaz | §1 site finder satırı; §2 uyarlama notu |
| **Uyum Notu 6** | "Dünya ufukta görünür mü" ≠ haberleşme link planlaması | §1 60-gün pencere satırı |
| **Uyum Notu 7** | Çözünürlük/zaman sınırları gizlenmez, A2'de zorunlu alan | §3 ilk iki satır |
| **Uyum Notu 8** | Repo hackathon prototipi; referans alınır, birebir kopyalanmaz | §2 strateji paragrafı |

---

## 5. Entegrasyon Kararları (Açık Maddeler)

| Karar | Seçenek | Durum |
|---|---|---|
| Repo bağlantı türü | git submodule / fork / API çağrısı | TBD — submodule path belirlenmeli |
| GPU ray-marching taşıması | Browser-only bırak / flight bridge yaz | TBD(source: §10 araç bilgisayarı) |
| Production migration zamanlaması | M4 / M5 | TBD |
| Validation: en uzun gece metriği uçuş kabul kriterine dönüşümü | B4 kabul testi | TBD — B serisi görev |
