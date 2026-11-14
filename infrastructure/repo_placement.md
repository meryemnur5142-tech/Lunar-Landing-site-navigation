# status: draft
# owner: luna-ai-architecture
# depends_on: [infrastructure/decision_log.md (DR-INT-001), config/tbd_register.md (TBD-REPO-001, TBD-REPO-002)]
# open_items: [TBD-REPO-001: submodule vs referans dizin karar bekleniyor (M3 öncesi), TBD-REPO-002: GPU ray-marching flight bridge mimarisi P2 tasarım kararı]

# Repo Yerleşim Planı — lunar-navigator

**Kaynak:** daniel27-space/lunar-navigator (2026 NASA Space Apps Challenge)
**Karar (DR-INT-001):** Referans implementasyon olarak alınır; birebir kopyalanmaz. Kod değiştirilmez, yalnızca referans edilir.

---

## Dizin Yapısı

```
luna-ai/
└── reference/
    └── lunar-navigator/     ← git submodule VEYA referans dizin (TBD-REPO-001)
```

**TBD-REPO-001:** `git submodule` mu yoksa ayrı referans dizin mi? Karar M3 öncesinde alınacak.

### Bağlantı Haritası (Kod Değişmez — Referans Edilir)

| Referans kaynak | LUNA-AI hedef | Yöntem |
|----------------|--------------|--------|
| `reference/lunar-navigator/pipeline/` | `data-platform/processing/` | Referans (servis sarması) |
| `reference/lunar-navigator/web/` | `apps/ground-control/` | Prototip (B6 UI_INTEGRATION.md) |

### Girdi Olarak Kullanılanlar (Şema Tanımları İçin)

| Referans belge | LUNA-AI kullanımı |
|---------------|-----------------|
| `reference/lunar-navigator/docs/DATA_CONTRACT.md` | A2 şemalarının (interfaces/) kaynak referansı |
| `reference/lunar-navigator/docs/VALIDATION.md` | B4 kabul kriterlerinin kaynağı (AC-VAL-001..005) |

---

## Üretim Geçiş Planı (P0/P1/P2)

| Modül | P0 | P1 | P2 |
|-------|----|----|-----|
| `pipeline/ephem/` | Referans | Referans | Referans |
| `horizon.py` | Referans | Referans | Üretim entegre |
| Disk görünürlüğü | Referans | Referans | Üretim entegre |
| GPU ray-marching (tarayıcı) | Prototip | Prototip | Flight bridge TBD-REPO-002 |
| Site finder | Referans (uyarlanmış) | Entegre | Entegre |
| When-to-land | Referans | Entegre | Entegre |

**Not:** "Referans" = kod değiştirilmez, servis sarması veya doğrudan çağrı ile kullanılır. "Entegre" = LUNA-AI pipeline içinde veri akışı bağlanmış.

---

## Sınırlamalar ve Riskler

| Sınır | Kaynak | Etki | Risk |
|-------|--------|------|------|
| Zaman aralığı: 2024–2035 | Ephemeris geçerlilik | Görev tarihi bu dışındaysa geçersiz | RR-012 |
| DEM çözünürlük: 80m nominal, 300m site finder | Kaynak veri sınırı | Küçük engel kaçırma riski | RR-011, RR-015 |
| Observer height hassasiyeti | 1m fark en uzun geceyi değiştirebilir | SC-009 duyarlılık testi gerekiyor | RR-013 |
| Earth eclipse refraksiyon | Repo hesaplamıyor | Marjinal pencere güveni düşük | RR-014 |
| Doğrulama aralığı | JPL Horizons ±0.001°, NASA GSFC r≥0.988 | Üretim değeri | AC-VAL-001..003 |

---

## Açık TBD'ler

| ID | Parametre | Hedef Karar Tarihi |
|----|-----------|------------------|
| TBD-REPO-001 | git submodule vs referans dizin | M3 öncesi |
| TBD-REPO-002 | GPU ray-marching flight segment bridge mimarisi | P2 başlangıcı |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — C5 görevi |
