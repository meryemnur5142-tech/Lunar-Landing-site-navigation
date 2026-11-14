# LUNA-AI Kritik Modüller FMEA (Failure Mode and Effects Analysis)

**Belge ID:** LUNA-AI-FMEA-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Yöntem:** MIL-STD-1629A uyumlu; uzay görev uyarlaması

---

## Puanlama Skalası

| Skor | Şiddet (S) | Olasılık (O) | Tespit (D) |
|------|-----------|-------------|-----------|
| 1 | Minimal etki | Son derece düşük | Neredeyse kesin tespit |
| 2 | Küçük etki | Düşük | Yüksek tespit olasılığı |
| 3 | Orta etki | Orta | Orta tespit olasılığı |
| 4 | Kritik etki | Yüksek | Düşük tespit olasılığı |
| 5 | Felaket (görev/araç kaybı) | Çok yüksek | Tespit edilemez |

**RPN = Şiddet × Olasılık × Tespit**  
**RPN ≥ 50:** Zorunlu önlem gerektirir  
**RPN ≥ 80:** Kritik; tasarım değişikliği önerilir

---

## FMEA Tablosu

### Modül: Güç Yönetimi

| Modül | Bileşen | Hata Modu | Etki | Şiddet (S) | Olasılık (O) | Tespit (D) | RPN | Önlem |
|-------|---------|-----------|------|-----------|-------------|-----------|-----|-------|
| Güç Yönetimi | Batarya | Ani kapasite düşüşü (SoC ölçüm < gerçek) | Dönüş enerjisi yetersiz kalır; araç PSR içinde enerji biter → Görev veya araç kaybı | 5 | 2 | 3 | **30** | Çift SoC ölçüm yöntemi (voltaj + Coulomb sayacı); dönüş marjı konservatif tutulur (%15 eşik) |
| Güç Yönetimi | Güneş Paneli | Panel açılım arızası (servo sıkışma) | Şarj olmaz; görev uzatılamaz; enerji rezervi düşer | 4 | 2 | 2 | **16** | Mekanik redundancy (yay destekli fail-open); şarj eksikliği güç monitörü ile < 30 s içinde tespit |
| Güç Yönetimi | Yük Yönetim Devresi | Kritik yük kesme komutu iletilemiyor | SURVIVAL modunda yüksek güç tüketimi devam eder; SoC hızla düşer | 5 | 1 | 2 | **10** | Donanım kesici (latching relay); yazılım ve donanım ayrı yoldan kesim sağlar |
| Güç Yönetimi | Şarj Regülatörü | Aşırı şarj (overcharge koruması devredışı) | Batarya ısınır; termal kritik; yangın riski | 5 | 1 | 2 | **10** | Donanım şarj koruma devresi; yazılım bağımsız voltaj izleme |

---

### Modül: Termal Yönetimi

| Modül | Bileşen | Hata Modu | Etki | Şiddet (S) | Olasılık (O) | Tespit (D) | RPN | Önlem |
|-------|---------|-----------|------|-----------|-------------|-----------|-----|-------|
| Termal Yönetimi | Isıtıcı | Isıtıcı açık devre arızası (çalışmıyor) | Kritik bileşen soğur → elektronik arıza → navigasyon/güç kaybı | 5 | 2 | 2 | **20** | Yedek ısıtıcı devresi; sıcaklık sensörü ile 1 s periyodik izleme; FDIR erken uyarı |
| Termal Yönetimi | Sıcaklık Sensörü | Sensör kısa devre (sabit yanlış okuma) | Yanlış sıcaklık verisi; termal kararlar hatalı → gecikmiş müdahale | 4 | 2 | 2 | **16** | Her kritik noktada ≥ 2 bağımsız sensör; oybirliği mantığı; anormallik tespiti |
| Termal Yönetimi | Termal Kontrol Yazılımı | Isıtıcı kontrol döngüsü donuyor (task freeze) | Isıtıcılar müdahalesiz; sıcaklık drift edebilir | 4 | 2 | 2 | **16** | FDIR watchdog (5 s timeout); watchdog tetiklenince FDIR doğrudan ısıtıcı güvenli durumuna geçirir |

---

### Modül: Navigasyon

| Modül | Bileşen | Hata Modu | Etki | Şiddet (S) | Olasılık (O) | Tespit (D) | RPN | Önlem |
|-------|---------|-----------|------|-----------|-------------|-----------|-----|-------|
| Navigasyon | IMU (Atalet Ölçüm Birimi) | Yüksek drift (kalibrasyon bozulması) | Konum hatası birikerek > 1 m RMS olur; Yerel Planlayıcı engel yaklaşım hızını kısar, durabilir | 4 | 3 | 2 | **24** | Çok-sensör füzyon (IMU + LiDAR landmark + kamera); EKF kovaryans izleme; hızlı yeniden kalibrasyon |
| Navigasyon | LiDAR | Toz/parçacık tarafından kirletilme (geri dönüş artar) | Görünür mesafe azalır; engel algılama güvenilirliği düşer | 3 | 3 | 2 | **18** | Birden fazla ölçüm perspektifi; kamera ile çapraz doğrulama; yazılımda outlier filtreleme |
| Navigasyon | EKF (Extended Kalman Filter) | Yanlış başlatma (initialization failure) | Lokalizasyon hiçbir zaman konverjans sağlamaz; araç hareket edemez | 4 | 2 | 2 | **16** | Boot testi: EKF konverjans < **TBD** saniye içinde sağlanmazsa FDIR bildirilir; yeniden başlatma prosedürü |

---

### Modül: FDIR

| Modül | Bileşen | Hata Modu | Etki | Şiddet (S) | Olasılık (O) | Tespit (D) | RPN | Önlem |
|-------|---------|-----------|------|-----------|-------------|-----------|-----|-------|
| FDIR | FDIR Yazılım Görevi | FDIR task freeze (watchdog kick durdu) | Durum makinesi güncelleme almaz; güvenlik kararları yapılamaz → tek hata noktası | 5 | 1 | 1 | **5** | Donanım watchdog: FDIR donunca sistem yeniden başlatılır; boot sonrası otomatik CAUTION; kritik görev izleme dual-channel |
| FDIR | Durum Makinesi Mantığı | Yanlış durum geçişi (false positive return) | Araç erken dönüş tetikler; görev hedefi yitirilir | 3 | 2 | 2 | **12** | Formal doğrulama (TLA+); 10.000 simülasyon senaryosu; histerezis eşiği (gürültü filtresi) |
| FDIR | Hata Tespit Eşikleri | Çok gevşek eşik (missed fault) | Kritik hata geç tespit edilir; CAUTION atlanarak SURVIVAL'a gelinebilir | 5 | 2 | 3 | **30** | Parametre doğrulama testi (eşik sweep); güvenli tasarım: her eşik 3 bağımsız mühendis tarafından incelendi |

---

### Modül: Hareket Kontrolü

| Modül | Bileşen | Hata Modu | Etki | Şiddet (S) | Olasılık (O) | Tespit (D) | RPN | Önlem |
|-------|---------|-----------|------|-----------|-------------|-----------|-----|-------|
| Hareket Kontrolü | Motor Sürücüsü | Motor sürücü arızası (bir tekerlek) | Araç düz gidemiyor; manevra kısıtlanıyor | 3 | 3 | 2 | **18** | 4+ tekerlekli diferansiyel sürüş; sürücü arızası motor akım sensörü ile < 500 ms tespit |
| Hareket Kontrolü | Servo Kontrolcüsü | Servo sıkışma (panel veya anten) | Panel yönlendirilemiyor (enerji azalır) veya anten yönlendirilemiyor (link zayıflar) | 3 | 2 | 2 | **12** | Fail-safe mekanizması (servo son güvenli konumda kilitlenir); manual override komutu (TC_IMMEDIATE) |
| Hareket Kontrolü | Tekerlek Enkoder | Enkoder okuma hatası | Hız/konum geri beslemesi yanlış → Yerel Planlayıcı hatalı hareket komutu → çarpışma riski | 4 | 2 | 2 | **16** | IMU hızla çapraz doğrulama; anormallik tespitinde enkoder devre dışı, IMU-only moda geçiş |

---

## Özet Analiz

### En Yüksek RPN'li 3 Hata Modu

| Sıra | Modül | Hata Modu | RPN | Kritik Olan |
|------|-------|-----------|-----|-------------|
| 1 | Güç Yönetimi | Ani batarya kapasite düşüşü | **30** | Dönüş enerjisi hesabı yanlış → araç PSR'da mahsur kalabilir |
| 2 | FDIR | Çok gevşek eşik — kaçırılan kritik hata | **30** | Kritik durum geç tespit → SURVIVAL'a hızla ulaşma riski |
| 3 | Navigasyon | IMU yüksek drift | **24** | Lokalizasyon kaybı → araç durmak zorunda |

---

### Single-Point Failure (Tekil Arıza Noktası) Listesi

Aşağıdaki bileşenler mevcut tasarımda yedeksizdir ve arızalandığında derhal görev kesintisine yol açar:

| Bileşen | Risk | Önerilen Önlem |
|---------|------|----------------|
| FDIR donanım watchdog | FDIR donduğunda güvenlik kararı yok | Donanım watchdog çift kanalı veya secondary processor |
| Ana batarya paketi | Toplam güç kaybı | Minimum iki bağımsız batarya modülü (paralel veya backup) |
| Birincil haberleşme modülü | Link tamamen kesilir | Yedek düşük-kazançlı/UHF omni anten (düşük bant genişliği ama link sürdürür) |
| IMU | Navigasyon tamamen kör | Yedek MEMS IMU veya güçlü visual odometry yeteneği |

---

### Görev Kaybı vs Araç Kaybı Ayrımı

| Hata Kategorisi | Tanım | Örnek Hata Modları |
|----------------|-------|-------------------|
| **Görev Kaybı** | Araç güvende ancak bilimsel hedefler gerçekleştirilemez | Panel açılım arızası, servo sıkışma, IMU drift, yanlış durum geçişi |
| **Araç Kaybı** | Araçtan geri dönüş sağlanamaz veya araç tahrip olur | Batarya ani kapasite düşüşü (PSR içinde), kritik ısıtıcı arızası (sıfırın altında ortamda), FDIR freeze (watchdog yok) |
| **Veri Kaybı** | Bilimsel veri toplanamaz veya iletilemiyor | LiDAR kirlenmesi, haberleşme kaybı (tamponlama yeterli değilse) |

**Öncelik:** Araç güvenliği her zaman görev hedeflerinin önünde gelir. Görev kaybı senaryoları kabul edilebilir; araç kaybı senaryoları için mutlaka yedeklilik veya yazılım azaltma önlemi tanımlanmalıdır.

---

## TBD Takip Listesi

| ID | TBD Parametresi | Bağımlı Veri |
|----|----------------|--------------|
| FMEA-TBD-001 | Batarya kimyası belirlenince ani kapasite düşüşü ihtimali güncellenecek | Batarya seçimi |
| FMEA-TBD-002 | IMU parça seçimine göre drift değeri güncellenmeli | IMU parça BoM |
| FMEA-TBD-003 | Termal ortam (PSR içi min sıcaklık) belirlendikçe ısıtıcı arıza olasılığı güncellenecek | Termal analiz |
| FMEA-TBD-004 | Radyasyon ortamı analizi tamamlanınca SEU kaynaklı yazılım arızası olasılıkları eklenecek | Radyasyon analizi |

---

*Bu FMEA taslak aşamada olup donanım seçimleri tamamlandıkça güncellenecektir. FMEA'nın her revizyonu sistem tasarım gözden geçirme toplantısında onaylanacaktır.*
