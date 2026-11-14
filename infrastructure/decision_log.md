# status: draft
# owner: luna-ai-architecture
# depends_on: [mission-intelligence/constraints/hard_constraints.py, docs/adr/, docs/conops/]
# open_items: [DL-002 safe haven 5+2 ayrımı henüz kesinleşmedi — ADR gerekiyor]

# Karar Kaydı — LUNA-AI v1.1

## Amaç

Bu belge LUNA-AI v1.1 kapsamında alınan mimari ve tasarım kararlarını, gerekçelerini ve v1.0 referanslarını kayıt altına alır.

---

## Karar Tablosu

| ID | Tarih | Karar | Gerekçe | v1.0 Referansı | Durum |
|----|-------|-------|---------|----------------|-------|
| DL-001 | 2026-11-14 | HC-001..015 hard constraint olarak sınıflandırıldı; soft constraint listesi ayrı tutulur | Hard constraint ihlali görev güvenliğini tehlikeye atar ve hiçbir koşulda geçilemez. Soft constraint optimizasyon hedefidir; ihlal kabul edilebilir ama kayıt edilir. | v1.0 §2, §6 | KAPALTI |
| DL-002 | 2026-11-14 | Safe haven kriterleri: 5 hard + 2 soft ayrımı değerlendirilmekte — henüz kesinleşmedi | Tüm 7 kriterin hard constraint sayılması aşırı kısıtlayıcı olabilir; acil erişim ve karanlık aralığı toleransı soft olarak değerlendirilebilir. ADR hazırlanacak. | v1.0 §4.8, Uyum Notu 2 | AÇIK |
| DL-003 | 2026-11-14 | Görev fazı (CRUISE/LANDING/SURFACE_EXPLORATION/PSR_OPS/RETURN/SAFE_STATE) ile güvenlik durumu (NORMAL/CAUTION/RETURN_REQUIRED/SURVIVAL) AYRI eksenler olarak tanımlandı | İkisini karıştırmak belirsiz durum makinesi üretir; faz otonomi matrisini, güvenlik durumu abort mantığını tanımlar. Çapraz etki belgelenmiş ve izlenebilir olmalı. | Uyum Notu 1, v1.0 §4.3, §4.6 | KAPALTI |
| DL-004 | 2026-11-14 | Emniyet bütçesi akış yönü: Power Management sahibi, Planner tüketici | Power Mgmt enerji politikasını bilir; Planner'ın kendi başına enerji politikası belirlemesi tutarsız davranış üretir. Tek kaynak ilkesi. | Uyum Notu 3, v1.0 §5 | KAPALTI |
| DL-005 | 2026-11-14 | temporal_class alanı tüm environment product TypedDict'lerinde zorunlu alan olarak tanımlandı | Tarihsel veri ile tahmin veriyi aynı alanda karıştırmak doğrulama hatası riski taşır. Zorunlu alan, None reddi, ikisi arasında karışma sıfır hedef. | v1.0 §6, Uyum Notu'nda belirtilen veri tipi karışıklığı riski | KAPALTI |
| DL-006 | 2026-11-14 | JSON Schema araç-yer interoperabilitesi için Python TypedDict'e ek olarak ayrıca tanımlandı | Yer kontrol yazılımı Python kullanmayabilir; JSON Schema dil-bağımsız sözleşme sağlar. TypedDict Python-içi doğrulama, JSON Schema servis-arası sözleşme işlevi görür. | v1.0 §3 (ICD) | KAPALTI |

---

## v1.2 Entegrasyon Kararları (C6 — lunar-navigator entegrasyonu)

### DR-INT-001: Repo Referans Implementasyon Olarak Alındı

| Alan | Değer |
|------|-------|
| **Tarih** | 2026-11-14 |
| **Karar** | daniel27-space/lunar-navigator kopyalanmaz; referans implementasyon olarak bağlanır (git submodule veya referans dizin — TBD-REPO-001). |
| **Gerekçe** | Yeniden yazmak gereksiz iş; kopyalamak teknik borç üretir; servis sarması browser-GPU avantajını kaybettirir. Kod değişmez, yalnızca referans edilir. |
| **v1.0 Referansı** | — (Yeni entegrasyon kararı) |
| **Durum** | AÇIK (submodule vs referans dizin TBD) |

### DR-INT-002: Site Finder Sıralaması Güvenlik Kararı Vermez

| Alan | Değer |
|------|-------|
| **Tarih** | 2026-11-14 |
| **Karar** | Ağırlıklı toplam (site finder weighted score) tek başına güvenlik kararı vermez; önce hard constraints kontrol edilir. |
| **Gerekçe** | Güvenlik kararlarını sıralama algoritmasına devreden sistemler HC ihlalini gizleyebilir. HC kümesi her zaman önce; sıralama sonra. |
| **v1.0 Referansı** | Uyum Notu 5; v1.0 §2, §6 |
| **Durum** | KAPALTI |

### DR-INT-003: Dünya Görünürlüğü ≠ Haberleşme Link Planlaması

| Alan | Değer |
|------|-------|
| **Tarih** | 2026-11-14 |
| **Karar** | Repo'nun "Dünya ufukta görünür mü" hesabı (geometrik görünürlük) ile §4.7 haberleşme link planlaması (veri hızı, kuyruk yönetimi, pencere atama) ayrı katmanlar. UI'da birleştirilmez. |
| **Gerekçe** | Geometrik görünürlük gerekli ama yeterli koşul değildir; link bütçesi, kuyruk durumu ve pencere atama ayrı hesaplardır. Karıştırmak yanlış "link hazır" kararına yol açabilir. |
| **v1.0 Referansı** | v1.0 §4.7, Uyum Notu 6 |
| **Durum** | KAPALTI |

### DR-INT-004: Çözünürlük ve Zaman Aralığı Sınırları Zorunlu Alan

| Alan | Değer |
|------|-------|
| **Tarih** | 2026-11-14 |
| **Karar** | `terrain_resolution` ve `ephemeris_validity_range` A2 şemalarında zorunlu alan olarak tanımlanır; veri getirildiğinde gizlenmez. |
| **Gerekçe** | Kullanıcıya hangi çözünürlükte ve hangi zaman aralığında geçerli veri sunulduğunu gizlemek yanlış güven yaratır. Sınırlar şeffaf ve her zaman görünür olmalı. |
| **v1.0 Referansı** | Uyum Notu 7 |
| **Durum** | KAPALTI |

---

## DR-README-001: README Bölüm Referansı Düzeltmeleri
Tarih: 2026-11-14  
Değişiklikler:
- `vehicle/README.md`: §4.2 → §4.6 (Navigation & Mobility); Uyum Notu 4 eklendi (iniş GNC / yüzey nav ayrımı)
- `safety/README.md`: §4.6 → §4.8 (Flight Safety & Fault Management); Uyum Notu 3 eklendi (emniyet bütçesi sahipliği)
- `infrastructure/README.md`: §1 → §10 (Araç Parametreleri / Genel)
- `simulation/README.md`: Lunar-Navigator entegrasyon notu eklendi (SPICE, horizon, visibility pipeline referansları)
- Eksik README'ler (mission_intelligence, apps/ground-control, vehicle/localization, vehicle/mobility-control): dosya yok, kural gereği oluşturulmadı; open_items'a not düşüldü.

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — C2 görevi, DL-001..006 |
| 0.2 | 2026-11-14 | C6 eki: DR-INT-001..004 — lunar-navigator entegrasyon kararları |
| 0.3 | 2026-11-14 | DR-README-001: README bölüm referansları ve uyum notları düzeltildi |
