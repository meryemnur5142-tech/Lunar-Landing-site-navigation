# autonomy/

Görev yürütme, global/lokal planlama, replanning, bilimsel zamanlama. Bkz. v1.0 §4.3.

## Alt Dizinler

- `mission-executive/` — Görev fazı yönetimi; faz geçiş mantığı, abort kararları.
- `global-planner/` — A* tabanlı global rota planlama; < 60s hedefi (1km² arazi).
- `local-planner/` — Gerçek zamanlı engel kaçınma ve lokal waypoint üretimi.
- `replanner/` — Ani koşul değişikliğinde < 30s replanning; ABT trigger entegrasyonu.
- `scheduler/` — Bilimsel görev zamanlaması; enerji-zaman bütçesi optimizasyonu.
