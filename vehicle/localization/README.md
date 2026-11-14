# Vehicle Localization

**v1.0 Referans:** §4.6 Navigation & Mobility

EKF tabanlı konum kestirimi: IMU, LiDAR odometri, güneş açısı ve (varsa) yer referans ölçümü füzyonu.

## Uyum Notu 4

İniş GNC sistemi ve yüzey navigasyon sistemi ayrı tasarım alanlarıdır.
Bu modül yalnızca yüzey görevini kapsar.

Traverse geçmişi yolu (traverse_path) planlayıcıya ICD-003 aracılığıyla iletilir;
ham sensör verisi flight bilgisayarında tutulur, yer segmentine iletilmez.
Bkz. `interfaces/nav_to_local_planner.schema.yaml` (ICD-003)
