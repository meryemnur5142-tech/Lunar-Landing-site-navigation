# safety/

Güvenlik katmanı: sağlık izleme, FDIR, güvenli mod yönetimi, watchdog. Bkz. v1.0 §4.8.

Uyum Notu 3: Emniyet bütçesinin sahibi Power Management modülüdür; planlayıcıya bildirilir, akış tersine çevrilemez (Bkz. `safety/safety_budget.md`).

FDIR planner'dan bağımsız çalışır (izole bellek — P0-AC-04).

## Alt Dizinler

- `health-monitor/` — Sistem sağlık telemetrisi izleme; anomali tespit öncesi ham veri.
- `fdir/` — Fault Detection, Isolation & Recovery; abort kararı üretici.
- `safing/` — Safe state geçiş prosedürleri; SAFE_STATE fazı yönetimi.
- `watchdog/` — Yazılım watchdog; kritik görev döngüsü zaman aşımı koruması.
