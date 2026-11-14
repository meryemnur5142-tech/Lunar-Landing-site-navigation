# LUNA-AI Quality Attribute Requirements (QAR) Tablosu

**Belge ID:** LUNA-AI-QAR-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Durum:** Taslak — Donanım parametreleri TBD

---

## Kullanılan Kısaltmalar

| Kısaltma | Açıklama |
|----------|----------|
| RMS | Root Mean Square (Karekök Ortalama Karesel Hata) |
| SoC | State of Charge (Şarj Durumu) |
| FDIR | Fault Detection, Isolation and Recovery |
| HIL | Hardware-in-the-Loop (Donanım-Döngüde Simülasyon) |
| EKF | Extended Kalman Filter |
| TBD | To Be Determined (Belirlenecek) |

---

## QAR Öncelik Skalası

| Öncelik | Açıklama |
|---------|----------|
| **P1** | Güvenlik kritik — ihlal görev iptaline veya araç kaybına yol açar |
| **P2** | Görev kritik — ihlal görev hedeflerine ulaşmayı engeller |
| **P3** | Performans kritik — ihlal görev verimliliğini düşürür |
| **P4** | Desiderata — hedeflenin ötesinde iyileştirme |

---

## QAR Tablosu

| ID | Modül | Nitelik | Sayısal Hedef | Ölçüm Yöntemi | Öncelik |
|----|-------|---------|---------------|---------------|---------|
| **FDIR-001** | FDIR | Anomali Tespit Süresi | < 50 ms (P95) | HIL enjeksiyonu: 100 senaryoda ölçüm | P1 |
| **FDIR-002** | FDIR | Recovery Karar Süresi | < 500 ms anomali tespitinden itibaren | HIL: anomali → karar arası gecikme ölçümü | P1 |
| **FDIR-003** | FDIR | Yanlış Pozitif Oranı | < %1 nominal operasyon saati başına | 100 saatlik nominal simülasyon, false alarm sayısı | P2 |
| **FDIR-004** | FDIR | Yanlış Negatif Oranı | < %0.1 (kritik hatalar için sıfır hedef) | Hata enjeksiyon testi: her kritik hata modu için en az 50 test | P1 |
| **FDIR-005** | FDIR | Durum Makinesi Geçiş Tutarlılığı | %100 deterministik (aynı girdi → aynı geçiş) | Formal doğrulama + 1000 tekrarlı test | P1 |
| **NAV-001** | Navigasyon | Konum Doğruluğu (düz arazi) | < 0.5 m RMS | Bilinen referans noktaları üzerinde 50 ölçüm, RTK karşılaştırması | P1 |
| **NAV-002** | Navigasyon | Yönelim Doğruluğu | < 0.5° RMS (yaw/pitch/roll) | Star-tracker karşılaştırması, 100 örnek | P1 |
| **NAV-003** | Navigasyon | Konum Güncelleme Frekansı | ≥ 10 Hz (hareket halinde), ≥ 1 Hz (dur-bekle) | Veri akışı zaman damgası analizi | P2 |
| **NAV-004** | Navigasyon | Lokalizasyon Kayıp Tespiti | < 2 saniye (EKF uyumsuzluk → alarm) | HIL: EKF ıraksama senaryosu | P1 |
| **NAV-005** | Navigasyon | Dead-Reckoning Kayması | < 2 m/dak (IMU alone, kayma sensörü yok) | Bilinen yol üzerinde kapalı döngü ölçüm | P2 |
| **NAV-006** | Navigasyon | PSR İçi Navigasyon Doğruluğu | < 1.0 m RMS (görsel landmark azaldığında) | LiDAR-only simülasyon, 20 PSR senaryosu | P2 |
| **PLAN-001** | Görev Planlayıcı | Global Rota Hesaplama Süresi | < 60 saniye (500m yol, A* algoritması) | Simülasyon: 10 farklı arazi profili, ortalama ve P99 | P2 |
| **PLAN-002** | Görev Planlayıcı | Yeniden Planlama (Replanning) Süresi | < 30 saniye (anlık engel tespiti sonrası) | HIL: beklenmedik engel enjeksiyonu | P2 |
| **PLAN-003** | Görev Planlayıcı | Enerji Bütçe Tahmin Hatası | < %10 (planlanan vs gerçekleşen enerji tüketimi) | 20 nominal görev gününde plan-gerçek karşılaştırması | P2 |
| **PLAN-004** | Görev Planlayıcı | PSR Giriş Koşulu Değerlendirme Süresi | < 10 saniye | Simülasyon: 50 giriş senaryosu | P1 |
| **PLAN-005** | Görev Planlayıcı | Dönüş Tetikleyici Hesaplama Frekansı | ≥ 1 Hz (sürekli dönüş marjı izleme) | Veri akışı periyod ölçümü | P1 |
| **PWR-001** | Güç Yönetimi | Minimum Dönüş SoC Rezervi | ≥ %15 SoC (safe haven kapısında) | Her görev günü kayıt; ihlal = P1 anomali | P1 |
| **PWR-002** | Güç Yönetimi | Enerji Tahmin Hatası | < %10 (kalan süre/mesafe için) | Dijital ikiz simülasyonu, 50 görev gün senaryosu | P2 |
| **PWR-003** | Güç Yönetimi | Yük Kesme Tepki Süresi | < 100 ms (kritik yük kesme komutu → fiili kesim) | HIL ölçümü: komut zaman damgası vs akım sensörü | P1 |
| **PWR-004** | Güç Yönetimi | Yük Kesme Tepki Süresi (Survival) | < 10 ms (SURVIVAL modunda tüm opsiyonel yükler) | HIL ölçümü | P1 |
| **PWR-005** | Güç Yönetimi | SoC Ölçüm Doğruluğu | **TBD:** ± % — batarya kimyasına bağlı; hedef: %2 | Kalibrasyon testi: bilinen kapasite karşılaştırması | P1 |
| **PWR-006** | Güç Yönetimi | Panel Verimliliği İzleme | Güncelleme periyodu ≤ 10 saniye | Veri akışı zaman damgası analizi | P3 |
| **THM-001** | Termal Yönetimi | Sıcaklık İzleme Periyodu | ≤ 1 saniye (tüm kritik sensörler) | Telemetri akışı periyod doğrulama | P1 |
| **THM-002** | Termal Yönetimi | Isıtıcı Aktivasyon Gecikmesi | < 5 saniye (komut → fiili ısıtma başlangıcı) | HIL: sıcaklık eşik geçişi → aktivasyon arası süre | P1 |
| **THM-003** | Termal Yönetimi | Termal Kritik Tespit Süresi | < 2 saniye (sıcaklık eşik ihlali → FDIR alarmı) | HIL enjeksiyonu: ani sıcaklık artışı senaryosu | P1 |
| **THM-004** | Termal Yönetimi | Min. Operasyon Sıcaklığı (Elektronik) | **TBD:** °C — parça seçimine bağlı | Termal vakum testi (TVAC) | P1 |
| **THM-005** | Termal Yönetimi | Maks. Operasyon Sıcaklığı (Elektronik) | **TBD:** °C — parça seçimine bağlı | TVAC | P1 |
| **COM-001** | Haberleşme | Komut İşleme Gecikmesi | < 500 ms (komut alındı → icra edildi) | End-to-end gecikme ölçümü, 100 test | P2 |
| **COM-002** | Haberleşme | Telemetri Güncelleme Periyodu (Nominal) | ≤ 10 saniye | Zaman damgası analizi | P2 |
| **COM-003** | Haberleşme | Telemetri Güncelleme Periyodu (Kritik Durum) | ≤ 1 saniye (CAUTION veya üstü durum) | Durum geçişi sonrası güncelleme frekansı | P1 |
| **COM-004** | Haberleşme | Otonom Çalışma Süresi (Link Yok) | ≥ **TBD:** saat (tam görev günü beklentisi) | Simülasyon: link kesildi, görev devam ediyor | P1 |
| **COM-005** | Haberleşme | Komut Bütünlüğü (CRC Hata Tespiti) | %100 (tek bit flip tespiti garantili) | CRC testi: 10.000 bozulmuş paket senaryosu | P1 |
| **COM-006** | Haberleşme | Link Yeniden Bağlantı Süresi | < **TBD:** dakika (link penceresi tekrar açılınca) | Test ortamı link simülasyonu | P2 |
| **SHV-001** | Safe Haven | Minimum Aydınlanma Süresi | ≥ **TBD:** saat/gün (güneş enerjisi yeterliliği için) | Orbital mekanik simülasyonu (SPICE) | P1 |
| **SHV-002** | Safe Haven | Minimum Dönüş Enerjisi Rezervi (Safe Haven kapısında) | ≥ %15 SoC | Her görev gününde ölçüm | P1 |
| **SHV-003** | Safe Haven | Safe Haven'a Ulaşım Süresi (Nominal) | ≤ **TBD:** dakika (maksimum uzaklık için) | Navigasyon simülasyonu: en uzak görev noktasından | P1 |
| **SHV-004** | Safe Haven | Safe Haven'a Ulaşım Süresi (SURVIVAL modu) | ≤ **TBD:** dakika (minimum enerji rotası) | SURVIVAL modu simülasyonu | P1 |
| **SHV-005** | Safe Haven | Zemin Eğim Toleransı | ≤ **TBD:** ° (güvenli park için) | Arazi haritası + güç/termal analizi | P2 |

---

## Ölçüm Yöntemi Sözlüğü

| Yöntem | Açıklama |
|--------|----------|
| **HIL** | Gerçek uçuş yazılımı + simüle donanım; enjeksiyonlu hata senaryoları |
| **Dijital İkiz Simülasyonu** | Tam sistem modeli üzerinde Monte Carlo veya senaryo bazlı test |
| **Formal Doğrulama** | Model checking (örn. TLA+, SPIN) ile durum makinesi tutarlılığı |
| **TVAC** | Thermal Vacuum Chamber — gerçek sıcaklık/vakum ortamında test |
| **Veri Akışı Analizi** | Çalışma zamanı telemetrisi üzerinden periyod ve gecikme ölçümü |

---

## TBD Takip Listesi

Aşağıdaki QAR değerleri donanım/arazi verisi beklenmektedir:

| QAR ID | TBD Parametresi | Bağımlı Veri |
|--------|----------------|--------------|
| PWR-005 | SoC ölçüm toleransı | Batarya kimyası seçimi |
| THM-004/005 | Min/Maks elektronik sıcaklık | Elektronik parça listesi (BoM) |
| COM-004 | Otonom çalışma süresi | Görev profili + link analizi |
| COM-006 | Yeniden bağlantı süresi | Orbital mekanik simülasyonu |
| SHV-001 | Min aydınlanma süresi | SPICE orbital simülasyonu |
| SHV-003/004 | Safe haven ulaşım süreleri | Araç hız + enerji profili |
| SHV-005 | Zemin eğim toleransı | Araç mekanik tasarımı |

---

*QAR değerleri donanım entegrasyon aşamasında gözden geçirilecek ve SRS (System Requirements Specification) ile çapraz kontrol edilecektir.*
