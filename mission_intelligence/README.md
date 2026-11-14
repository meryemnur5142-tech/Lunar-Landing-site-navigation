# Mission Intelligence

**v1.0 Referans:** §4.1 Mission Intelligence

Hedef krater adaylarını filtreler, sıralar ve görev paketini oluşturur.

## Alt Modüller

- `candidate-filter/` — Hard constraint eleme (önce HC, sonra sıralama)
- `scoring/` — Çok kriterli ağırlıklı puanlama (CandidateScorer)
- `science-objectives/` — Bilimsel hedef tanımları

## Uyum Notu 5

Ağırlıklı toplam tek başına güvenlik kararı vermez.
Aday sıralaması hard constraint elemenin ardından uygulanır.
Bkz. `domain/mission/constraints/hard_constraints_catalog.md`
