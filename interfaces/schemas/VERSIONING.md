# status: draft
# owner: luna-ai-architecture
# depends_on: [interfaces/schemas/*.schema.yaml]
# open_items: []

# Şema Versiyon Politikası — LUNA-AI v1.1

## 1. Genel Kurallar

Her şema dosyası `schema_version` alanını taşımak zorundadır.
Format: **MAJOR.MINOR.PATCH** (Semantic Versioning 2.0.0).

```yaml
schema_version: "1.0.0"
```

Yer-araç arasında aktarılan tüm mesajlar şema versiyonu içerir.
Araç aldığı mesajı desteklediği şema versiyonuyla kıyaslar; uyumsuzlukta redet.

---

## 2. Versiyon Artırma Kuralları

### PATCH (1.0.0 → 1.0.1)
Davranışı değiştirmeyen, geriye ve ileriye uyumlu düzeltmeler:
- Açıklama (description) metin düzeltmesi
- Örnek (example) güncelleme
- Yorum ekleme/değiştirme

### MINOR (1.0.0 → 1.1.0)
Geriye uyumlu ekleme (eski alıcı yeni mesajı anlayabilir):
- Yeni **opsiyonel** alan ekleme
- Mevcut bir `enum` değerine **yeni değer ekleme** (eski alıcı bilinmeyeni yoksayar)
- Yeni opsiyonel kısıt ekleme (minimum, maximum genişletme)

### MAJOR (1.0.0 → 2.0.0)
Geriye **uyumsuz** değişiklik (eski alıcı yeni mesajı anlayamaz):
- Mevcut **zorunlu alan** ekleme veya kaldırma
- Mevcut bir `enum` değerini **kaldırma** veya **yeniden adlandırma**
- Mevcut bir alanın tipini veya anlamını değiştirme
- `required` listesine mevcut opsiyonel alan taşıma

---

## 3. Geriye Uyumlu Değişiklik Örnekleri (→ MINOR)

| Değişiklik | Versiyon | Gerekçe |
|---|---|---|
| `resource_state.schema.yaml`'a opsiyonel `battery_temp_c` eklendi | 1.0.0 → 1.1.0 | Eski araç yazılımı alanı yoksayar |
| `vehicle_command.schema.yaml`'a `instrument_toggle_batch` enum değeri eklendi | 1.2.0 → 1.3.0 | Eski alıcı bilinmeyen enum değerini reddeder → yük geçmez, güvenli |
| `environment_product.schema.yaml`'a opsiyonel `sensor_id` eklendi | 1.0.0 → 1.1.0 | Eski alıcı alanı yoksayar |

---

## 4. Breaking Change Örnekleri (→ MAJOR)

| Değişiklik | Versiyon | Neden Breaking |
|---|---|---|
| `resource_state.schema.yaml`'a zorunlu `heater_duty_cycle` eklendi | 1.x.x → 2.0.0 | Eski gönderici alanı üretmez → alıcı validation hatası verir |
| `vehicle_command.schema.yaml`'dan `abort` enum değeri kaldırıldı | 1.x.x → 2.0.0 | Eski gönderici `abort` gönderebilir → alıcı reddeder, kritik komut kaybolur |
| `mission_package.schema.yaml`'da `authority_level` alanı yeniden adlandırıldı (`command_authority` yapıldı) | 1.x.x → 2.0.0 | Eski alıcı alanı bulamaz → validation hatası |

---

## 5. Yer-Araç Versiyon Uyumsuzluğu Protokolü

```
Araç aldığı mesajın schema_version MAJOR değerini kendi desteklediği MAJOR ile karşılaştırır.

MAJOR farklıysa:
  → Mesajı reddet
  → Hata telemetrisi gönder: SCHEMA_VERSION_MISMATCH
  → Son geçerli durumda kal (komutu uygulamaz)

MAJOR aynı, MINOR farklıysa (alıcı daha eski):
  → Bilinmeyen alanları yoksay (additionalProperties: false kuralı araç tarafında esnetilebilir)
  → Zorunlu alanlar karşılanıyorsa mesajı kabul et

MINOR farklıysa (alıcı daha yeni):
  → Mesajı kabul et; eksik opsiyonel alanlar için varsayılan değer uygula
```

**Kritik kural:** Yer segmenti ile araç yazılımı arasında MAJOR versiyon farkı tolerans edilemez.
Görev öncesi MAJOR uyumluluğu doğrulanır ve ICD kontrolü yapılır.

---

## 6. Şema Dosyaları ve Güncel Versiyonlar

| Dosya | Güncel Versiyon | Son Değişiklik |
|---|---|---|
| `environment_product.schema.yaml` | 1.0.0 | v1.1 ilk yayın |
| `resource_state.schema.yaml` | 1.0.0 | v1.1 ilk yayın |
| `mission_package.schema.yaml` | 1.0.0 | v1.1 ilk yayın |
| `vehicle_command.schema.yaml` | 1.0.0 | v1.1 ilk yayın |

---

## 7. Değişiklik Süreci

1. Değişiklik teklifi ADR (Architectural Decision Record) olarak belgelenir.
2. MAJOR değişiklikler mühendislik incelemesinden geçer.
3. `schema_version` güncellenir; `VERSIONING.md` §6 tablosu güncellenir.
4. Yer segmenti ve araç yazılımı entegrasyon testi gerçekleştirilir.
