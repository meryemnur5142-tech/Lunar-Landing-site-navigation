# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/earth_visibility.schema.yaml, interfaces/multi_site_comparison.schema.yaml, interfaces/landing_window_validation.schema.yaml, infrastructure/repo_placement.md]
# open_items: [GPU ray-marching browser bridge TBD (P2 tasarım kararı — TBD-REPO-002), 5-site comparison layout UX tasarımı bekleniyor]

# Ground Control UI Entegrasyon Planı — lunar-navigator → LUNA-AI

Kaynak: daniel27-space/lunar-navigator UI bileşenleri (2026 NASA Space Apps Challenge)

---

## Bileşenler ve Entegrasyon

### Earth Visibility Katmanı

- **Kaynak:** lunar-navigator repo doğrudan (referans)
- **Gösterim:** "Dünya ufukta görünür mü? Ne zaman değişir?" göstergesi
- **Veri kaynağı:** `interfaces/earth_visibility.schema.yaml`
- **Güncelleme:** Zaman kaydırıcısı hareket ettiğinde canlı güncelleme

**KRİTİK (Uyum Notu 6):** Bu katman yalnızca geometrik görünürlük gösterir — Dünya'nın ufukta olup olmadığı. §4.7 haberleşme link planlaması (veri hızı, kuyruk yönetimi, pencere atama) AYRI katmandır. UI'da birleştirilmez, aynı panelde gösterilmez.

---

### Site Kartı

- **İçerik:** Güneş geometrisi + Dünya görünürlüğü + görünürlük değişim süresi
- **Veri kaynağı:** `interfaces/multi_site_comparison.schema.yaml`
- **Her site için gösterilen:** `sun_fraction`, `earth_fraction`, `longest_night_hours`, `longest_outage_hours`, `terrain_resolution`

---

### "When to Land" Paneli

- **Kaynak:** lunar-navigator landing-window (7/14/30 gün konaklama analizi)
- **UI rolü:** İniş zamanı önerisi — operatör kararı girdi ekranı
- **Önemli:** Bu panel öneri sunar; nihai iniş zamanı seçimi YER (operatör onayı) — B1-EK ile hizalı
- **Faz makinesine bağlantı:** Onaylanan pencere `interfaces/landing_window_validation.schema.yaml` üzerinden görev yürütme katmanına iletilir

---

### Çoklu Bölge Karşılaştırması

- **Repo kapasitesi:** 2–3 bölge
- **LUNA-AI genişletmesi:** 5 bölge karşılaştırması
- **Her bölge için sütunlar:**

| Sütun | Kaynak alan | Açıklama |
|-------|------------|----------|
| Güneş oranı | `sun_fraction` | 0.0–1.0 |
| Dünya görünürlük oranı | `earth_fraction` | 0.0–1.0 |
| En uzun gece | `longest_night_hours` | Saat |
| En uzun iletişim kesintisi | `longest_outage_hours` | Saat |
| DEM çözünürlüğü | `terrain_resolution` | 80m / 300m / 2700m |

---

### Polar Ufuk Grafiği

- **Gösterim:** Güneş ve Dünya'nın yerel ufka göre konumu (720-ray horizon profili)
- **Kaynak:** lunar-navigator `pipeline/terrain/horizon.py`
- **Observer height girişi:** `observer_height_m` = TBD-HEIGHT-001 (SC-009 duyarlılık ile hizalı)

---

### Zaman Kaydırıcısı

- Kullanıcı zamanı değiştikçe tablo ve grafik canlı güncellenir
- **temporal_class kuralı (B5-EK ile uyumlu):**
  - Geçmiş zaman → `temporal_class: historical`
  - Gelecek zaman → `temporal_class: predicted`
- Kaydırıcı konumu değiştiğinde `temporal_class` otomatik güncellenir; uyarı etiketi gösterilir

---

## GPU Ray-Marching Notu

- Lunar-navigator 3B GPU gölge ray-marching tarayıcı-içi çalışır
- **LUNA-AI flight segment bridge:** TBD-REPO-002 (P2 tasarım kararı)
- **Şimdilik:** Prototip olarak `apps/ground-control/` altında korunur; üretim entegrasyonu P2 kapsamına alınacak

---

## Bağlantı Haritası

| UI Bileşen | Şema | Üretici Modül |
|------------|------|--------------|
| Earth Visibility Katmanı | `interfaces/earth_visibility.schema.yaml` | communication/ |
| Site Kartı / Karşılaştırma | `interfaces/multi_site_comparison.schema.yaml` | simulation/environment-model |
| When to Land Paneli | `interfaces/landing_window_validation.schema.yaml` | apps/ground-control → autonomy/mission-executive |
| Polar Ufuk Grafiği | — | simulation/environment-model (horizon.py) |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — B6 görevi |
