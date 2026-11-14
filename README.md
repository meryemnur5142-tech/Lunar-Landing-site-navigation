# LUNA-AI — Ay Krateri Keşif ve Otonom Görev Sistemi

Ay kraterlerini bilimsel ve operasyonel verilerle değerlendiren, PSR erişimi sağlayan
ve enerji-termal kısıtlar altında güvenli dönüşü yöneten otonom görev sistemi.

## Mimari Segmentler

| Segment | Sorumluluk |
|---|---|
| **Ground Segment** | Bilimsel analiz, görev tasarımı, operatör arayüzü |
| **Flight Segment** | Gerçek zamanlı navigasyon, güvenlik, hareket kontrolü |
| **Simulation & Validation** | Dijital ikiz, senaryo testleri, hata enjeksiyonu |

## Klasör Yapısı

```
docs/           — Mimari dokümanlar (ConOps, QAR, FMEA, ADR)
domain/         — Alan modelleri (crater, environment, mission, resources)
data-platform/  — Planetary veri alım ve işleme hattı
mission-intelligence/ — Aday filtreleme, sıralama, bilimsel hedefler
interfaces/     — Sürümlenmiş veri sözleşmeleri (ICD)
tests/          — Unit, integration, system testleri
```

## Geliştirme Durumu

Havacılık donanım verileri bekleniyor (batarya, panel, termal parametreler).
Bu veriler gelene kadar: mimari dokümanlar + bilimsel veri platformu geliştiriliyor.

## Referans

Mimari prompt dosyası: `LUNA-AI_Mimari_Prompt_Dosyasi.md`
