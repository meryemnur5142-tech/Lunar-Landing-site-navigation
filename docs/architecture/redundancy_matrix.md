# status: draft
# owner: Agent C
# depends_on: [docs/adr/FMEA_KRITIK_MODULLER.md, docs/architecture/SAFETY_STATE_MACHINE.md, docs/architecture/ICD_TEMPLATES.md]
# open_items: [TBD-RED-001..TBD-RED-008 — araç kütlesi/hacim kısıtları kesinleşmeden uygulanamayan yedeklilikler; RPN'ler donanım seçimi sonrası güncellenecek]

# Redundancy Matrix (Yedeklilik Matrisi) — LUNA-AI v1.0

**Belge ID:** LUNA-AI-ARCH-003  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Bağlı Belgeler:** LUNA-AI-FMEA-001, LUNA-AI-ARCH-001, ADR-005

---

## Yedeklilik Tipi Tanımları

| Kod | Tip | Açıklama |
|-----|-----|----------|
| **Simplex** | Tekil | Yedekleme yok; tek bileşen. Arıza doğrudan etki. |
| **Dual** | Çift | İki özdeş bileşen; biri arızalanınca diğeri devralır. |
| **Triple (2-of-3)** | Üçlü Oylama | Üç bağımsız kanal; 2'si anlaştığı değer kullanılır (majority voting). |
| **Functional** | Fonksiyonel | Farklı teknoloji/yöntemle aynı işlevi sağlayan yedek (heterojen). |

## Failover Tipi Tanımları

| Kod | Tip | Açıklama |
|-----|-----|----------|
| **Cold Standby** | Soğuk Bekleme | Yedek güçsüz bekler; failover süresi dakika mertebesinde. |
| **Warm Standby** | Ilık Bekleme | Yedek güçlü ama aktif değil; saniye mertebesinde failover. |
| **Hot Standby** | Sıcak Bekleme | Yedek sürekli aktif ve senkron; anlık (< 1 s) failover. |

---

## Yedeklilik Matrisi

| Modül | Bileşen | Yedeklilik Tipi | Failover Stratejisi | Tespit Süresi | Recovery Süresi | FMEA RPN Ref |
|-------|---------|-----------------|---------------------|---------------|-----------------|--------------|
| **Güç Yönetimi** | Güç Dağıtım Ünitesi (PDU) | Dual | Hot Standby — ikincil PDU sürekli izler; birincil kayıpsa anlık devir | < 500 ms (donanım latch) | < 1 s (otomatik) | FMEA-RPN-PWR-003 (RPN: 10) |
| **Güç Yönetimi** | Batarya Sistemi | Dual (iki bağımsız modül) | Warm Standby — ikincil modül şarjlı bekler; birincil arızalanınca bağlanır | < 2 s (SoC monitörü) | < 5 s (güç aktarımı) | FMEA-RPN-PWR-001 (RPN: 30) |
| **Uçuş Bilgisayarı** | Ana Bilgisayar (OBC) | Dual | Warm Standby — yedek OBC senkron bellek güncellenir; birincil donunca watchdog tetikler | < 500 ms (FDIR watchdog) | < 10 s (boot + durum restorasyon) | FMEA-RPN-FDIR-001 (RPN: 5) |
| **Navigasyon** | IMU / Navigasyon Sensörü | Functional (IMU birincil + visual odometry/EKF yedek) | Warm Standby — IMU sağlıklıysa tam füzyon; arızalanınca kamera+odometry-only moda geçiş | < 500 ms (EKF kovaryans izleme) | < 5 s (mod geçişi) | FMEA-RPN-NAV-001 (RPN: 24) |
| **Güvenlik** | FDIR Watchdog | Dual (yazılım FDIR + donanım watchdog) | Hot Standby — donanım watchdog FDIR'dan bağımsız çalışır; FDIR donunca donanım reset atar | < 25 ms (donanım kick süresi) | < 30 s (boot + CAUTION'dan başlama) | FMEA-RPN-FDIR-001 (RPN: 5) |
| **Haberleşme** | Alıcı-Verici (Transceiver) | Dual (yüksek kazançlı yönlü + omni UHF) | Cold Standby — birincil yön kaybında omni UHF devreye girer (düşük bant genişliği ama link sürdürür) | < 30 s (link timeout izleme) | < 60 s (omni UHF bağlantı kurma) | FMEA-RPN-COM-001 (N/A — SPF listesi) |
| **Termal Yönetim** | Isıtıcı Kontrolcüsü | Dual (birincil kontrolcü + donanım fallback devresi) | Warm Standby — birincil kontrolcü donunca FDIR doğrudan donanım fallback devresini tetikler | < 5 s (termal heartbeat timeout) | < 2 s (fallback devre aktivasyonu) | FMEA-RPN-THM-001 (RPN: 20) |
| **Hareket Kontrolü** | Motor Sürücüleri | Functional (4+ tekerlekli diferansiyel sürüş; tek tekerlek kaybı toleranslı) | Degraded Mode — arızalı tekerlek izole edilir; kalan tekerleklerle asimetrik sürüş | < 500 ms (akım sensörü anomali tespiti) | < 2 s (sürücü izolasyon komutu) | FMEA-RPN-MOT-001 (RPN: 18) |

---

## 1. Single-Point Failure (Tekil Arıza Noktası) Listesi

Simplex tasarım veya yüksek RPN'li bileşenler; mevcut mimaride arızalanınca derhal görev kesintisine yol açar:

| # | Bileşen | Neden SPF | FMEA RPN | Mevcut Risk |
|---|---------|-----------|----------|-------------|
| SPF-001 | Güneş Paneli Mekanik Açılım | Servo sıkışmasında şarj olmaz; yazılımsal yedek yok (mekanik sistem) | RPN: 16 | Görev kaybı (enerji üretimi sıfıra düşer) |
| SPF-002 | Batarya Ana Paketi (mevcut tek modül tasarımında) | Toplam güç kaybı; araç tamamen devre dışı | RPN: 30 | **Araç kaybı** |
| SPF-003 | FDIR Durum Makinesi Mantığı | Yanlış durum geçişi veya FDIR freeze → güvenlik kararları yapılamaz | RPN: 12–30 | Araç kaybı riski |
| SPF-004 | IMU (Birincil navigasyon; visual odometry henüz entegre değilse) | Navigasyon tamamen kör; araç hareket edemez | RPN: 24 | Görev kaybı / araç takılı kalır |
| SPF-005 | Yük Yönetim Devresi (Load Switch) | SURVIVAL modunda yüksek güç kesim komutu iletilemez; SoC hızla düşer | RPN: 10 | Araç kaybı (enerji tükenme) |

---

## 2. Önerilen Aksiyonlar

| # | Hedef SPF / Bileşen | Öneri | Öncelik |
|---|---------------------|-------|---------|
| ACT-001 | Batarya Sistemi (SPF-002) | İki bağımsız batarya modülü ekle (paralel veya bağımsız devre); mevcut matristeki Dual tasarımını onaya al ve kütleye göre boyutlandır | P-CRIT |
| ACT-002 | Haberleşme Alıcı-Vericisi | Birincil yüksek kazançlı anten arızasında UHF omni yedek bağlantıyı HIL testleriyle doğrula | P-HIGH |
| ACT-003 | IMU (SPF-004) | Visual odometry / kamera-tabanlı odometry fonksiyonel yedek olarak P2'de entegre et; EKF'e ikinci kaynak olarak bağla | P-HIGH |
| ACT-004 | Yük Yönetim Devresi (SPF-005) | Latching relay donanım kesici + yazılım yolundan bağımsız donanım yolunu formal olarak doğrula; FMEA RPN güncellemesi yap | P-HIGH |
| ACT-005 | Güneş Paneli Açılımı (SPF-001) | Yay destekli fail-open mekanizması mevcut; ek eylem: açılım başarısını fırlatma sonrası kontrol protokolüne ekle ve sensörle doğrula | P-MED |
| ACT-006 | OBC Çift Bilgisayar | Warm standby OBC için bellek senkronizasyon protokolü tasarla; failover süresi < 10 s kabul kriterini SIL'de doğrula | P-MED |

---

## 3. Araç Kütlesi / Hacim Kısıtları Bilinmeden Uygulanamayan Yedeklilikler (TBD)

Aşağıdaki yedeklilik kararları §10 araç verisi (kütle bütçesi, hacim zarfı, güç bütçesi) gelene kadar uygulanamaz. `config/tbd_register.md`'e eklendi.

| TBD ID | Yedeklilik | Neden TBD |
|--------|------------|-----------|
| TBD-RED-001 | İkinci IMU modülü ekleme | IMU kütlesi + hacmi araç bütçesiyle kısıtlı; dual IMU veya ekstra kamera seçimi §10 sonrası belirlenecek |
| TBD-RED-002 | Üçlü OBC (Triple Voting) | Her ek OBC ~TBD kg; araç kütle bütçesi bilinmeden triple feasibility değerlendirilemez |
| TBD-RED-003 | İkinci batarya modülü boyutlandırması (Wh) | Batarya kapasitesi (TBD-BAT-001) ve kimyası (TBD-BAT-002) belirlenene kadar dual batarya hacim planlaması yapılamaz |
| TBD-RED-004 | UHF omni anten boyutu ve frekans bandı | Araç yapısındaki anten montaj hacmi (§10 yapı alt sistemi) ve onaylı frekans planı (TBD-COM-001) bilinmeden anten seçimi netleşmez |
| TBD-RED-005 | Motor sürücü redundancy seviyesi (Dual yerine Triple) | Motor sayısı ve araç tahrik mimarisi (§10 hareket alt sistemi) onaylanmadan ek sürücü ekleme değerlendirilemez |
| TBD-RED-006 | Termal fallback ısıtıcı güç kapasitesi (W) | Termal kütle (TBD-THM-001) ve yalıtım konfigürasyonu bilinmeden fallback ısıtıcı boyutlandırması yapılamaz |
| TBD-RED-007 | Yedek güneş paneli veya alternatif enerji kaynağı | Araç kütlesi ve panel gerimi (TBD-SOL-001) belirlenmeden ek panel ekleme fizibilite değerlendirilemez |
| TBD-RED-008 | PDU yedeklilik detayı (güç hattı yönlendirme) | Araç güç dağıtım topolojisi (kablo harnesi) §10 araç mühendisliğiyle belirlenir |

---

## Revizyon Geçmişi

| Versiyon | Tarih | Değişiklik |
|----------|-------|------------|
| 0.1 | 2026-11-14 | İlk taslak — Agent C, C1 görevi |
