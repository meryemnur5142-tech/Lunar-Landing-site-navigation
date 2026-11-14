# LUNA-AI Katkı Kılavuzu

## Geliştirme Ortamı Kurulumu

Python 3.11 veya üzeri gereklidir.

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

pip install -r requirements.txt
```

## Testleri Çalıştırma

```bash
# Tüm testler
make test
# veya
PYTHONPATH=. python -m pytest tests/ -v --tb=short

# Sadece birim testleri
make test-unit

# Sadece entegrasyon testleri
make test-integration
```

CI'da her PR için tüm testler otomatik çalışır. PR açmadan önce `make test` ile yerel doğrulama yapın.

## Lint

```bash
make lint
```

## Branch Stratejisi

- `main` — kararlı, korumalı dal; doğrudan push yapılmaz.
- `feature/<kısa-açıklama>` — yeni özellikler ve iyileştirmeler.
- `fix/<kısa-açıklama>` — hata düzeltmeleri.
- `docs/<kısa-açıklama>` — yalnızca belgeleme değişiklikleri.

Her değişiklik için `main`'den yeni bir branch açın ve PR ile birleştirin. Self-merge yapılmaz; CI yeşil olduktan sonra melek ya da sorumlu mühendis birleştirir.

## Commit Mesajı Formatı

```
<tür>: kısa açıklama (≤72 karakter)

İsteğe bağlı gövde: neyi neden değiştirdin.
```

Türler: `feat` / `fix` / `docs` / `chore` / `test` / `refactor`

Örnek:
```
feat: HC-004 iniş elipsi boyut kısıtı ekle

ICD-003 parametreleri onaylandı; HC-004 semi_major_m <= 750 m eşiğiyle
default_constraints() listesine eklendi.
```

## Uyum Notları Kontrol Listesi

Her PR'ı açmadan önce v1.1 uyum notlarını (1–8) gözden geçir:

| # | Konu | Kontrol |
|---|------|---------|
| 1 | Emniyet bütçesi sahipliği `power/` modülünde | [ ] |
| 2 | Planner tüketici, güvenlik kararı vermez | [ ] |
| 3 | Emniyet bütçesi sahibi `power/`; planner tüketici | [ ] |
| 4 | İniş GNC ve yüzey nav ayrımı korunuyor | [ ] |
| 5 | Ağırlıklı toplam tek başına güvenlik kararı vermiyor | [ ] |
| 6 | Geometrik görünürlük ≠ link planlaması ayrımı | [ ] |
| 7 | HC eleme, sıralamadan önce uygulanıyor | [ ] |
| 8 | FDIR tepki süreleri QAR eşiklerini karşılıyor | [ ] |

Uygulanmayan notlar için PR açıklamasında gerekçe belirt.
