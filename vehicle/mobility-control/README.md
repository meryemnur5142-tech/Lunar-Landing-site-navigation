# Vehicle Mobility Control

**v1.0 Referans:** §4.6 Navigation & Mobility

Diferansiyel sürüş komutu üretimi, tekerlek tork kontrolü ve motor sürücü arayüzü.

## Bağımlılıklar

- `vehicle/localization/` — mevcut konum ve heading (ICD-003)
- `safety/` — hareket komutları emniyet monitörü tarafından denetlenir

## Motor Stall FDIR

Motor stall tespitinde FI-004 referanslı arıza enjeksiyonu uygulanır.
FDIR tepkisi: motor durdur → FDIR'a hata bildir → NOMINAL→CAUTION geçişi bekle.
Bkz. `docs/adr/FMEA_KRITIK_MODULLER.md` (FI-004) ve `safety/README.md`
