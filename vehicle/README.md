# vehicle/

Araç alt sistem yazılımı: iniş GNC, lokalizasyon, algılama, hareket kontrolü. Bkz. v1.0 §4.6.

Uyum Notu 4: İniş GNC ile yüzey navigasyonu ayrıdır. Handover sınırları `vehicle/localization/navigation_architecture.md §5` ile tanımlanmıştır.

## Alt Dizinler

- `landing-gnc/` — İniş güdüm, navigasyon ve kontrol; yüzey navigasyona handover sağlar.
- `localization/` — EKF tabanlı konum kestirimi; IMU + odometry + landmark füzyonu.
- `perception/` — Stereo görüntü, lidar, engel algılama; DEM güncelleme.
- `mobility-control/` — Tekerlek/yürüyüş komutu yürütme; eğim ve slip kontrolü.
