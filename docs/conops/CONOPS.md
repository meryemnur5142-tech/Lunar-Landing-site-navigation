# LUNA-AI Concept of Operations (CONOPS)

**Belge ID:** LUNA-AI-CONOPS-001  
**Versiyon:** 0.1-draft  
**Tarih:** 2026-11-14  
**Durum:** Taslak — Donanım parametreleri TBD

---

## 1. Görev Tanımı ve Hedefler

LUNA-AI, Ay güneyindeki PSR (Permanently Shadowed Region / Kalıcı Gölge Bölgesi) içeren kraterleri bilimsel ve operasyonel verilerle değerlendiren otonom bir Ay yüzey görev sistemidir.

### 1.1 Birincil Hedefler

- Ay güney kutbu yakınındaki hedef kraterlere güvenli erişim sağlamak
- PSR içindeki buz/kaynak bölgelerini in-situ sensörlerle haritalandırmak
- Her operasyon gününü yeterli enerji rezerviyle safe haven'a dönerek tamamlamak

### 1.2 Kapsam Dışı

- Ay dışı (transit / cruise) faz bu CONOPS kapsamında değildir
- Iniş ve yüzey transferi aşamaları ayrı bir CONOPS ile ele alınacaktır

---

## 2. Sistem Segmentleri

| Segment | Alt Bileşenler | Birincil Sorumluluk |
|---------|----------------|---------------------|
| **Ground Segment** | Bilimsel Analiz, Görev Tasarımı, Operatör Arayüzü | Uzun vadeli görev planlaması, bilimsel önceliklendirme, telemetri analizi |
| **Flight Segment** | Navigasyon, FDIR, Hareket Kontrolü, Güç Yönetimi, Termal, Haberleşme | Gerçek zamanlı operasyon, güvenlik, otonom karar |
| **Simulation & Validation** | Dijital İkiz, Senaryo Test Ortamı | Görev öncesi doğrulama, risk analizi, eğitim |

---

## 3. Nominal Görev Günü

Ay güneyinde bir güneş dönemi yaklaşık **14 Dünya günüdür**. Araç, her çalışma döngüsünde aşağıdaki adımları izler.

> **Varsayım:** Araç gece boyunca safe haven'da beklemiş, bataryalar tam şarjlı, termal sistem nominal aralıkta.

### Adım 1 — Sabah Sistem Kontrolü (Sorumlu: FDIR + Güç Yönetimi)

| Alt-adım | Açıklama | Çıktı |
|----------|----------|-------|
| 1.1 | FDIR boot-on-wakeup testi: tüm subsistemlerden heartbeat doğrulama | Go / No-Go |
| 1.2 | Güç Yönetimi: batarya SoC ölçümü, açılış enerjisi hesabı | energy_state mesajı |
| 1.3 | Termal Yönetimi: kritik bileşen sıcaklıkları kontrol | thermal_state mesajı |
| 1.4 | Navigasyon: IMU başlatma, star-tracker / Sun-sensor kalibrasyonu | vehicle_pose ilk fix |
| 1.5 | Haberleşme: yer ile uplink/downlink link testi | link_status |

**Çıkış koşulu:** Tüm subsistemler nominal → Görev Planlayıcıya Go ver.

### Adım 2 — Güneş Paneli Açılımı ve Şarj (Sorumlu: Güç Yönetimi)

| Alt-adım | Açıklama | Sorumlu Modül |
|----------|----------|---------------|
| 2.1 | Panel yönlendirme algoritması güneş açısını hesapla | Güç Yönetimi |
| 2.2 | Panel servo komutu gönder | Hareket Kontrolü |
| 2.3 | Şarj akımı doğrulama: **TBD:** minimum panel verimliliği eşiği | Güç Yönetimi |
| 2.4 | Şarj güncelleme oranı: her **TBD:** saniyede energy_state yayımla | Güç Yönetimi → Mission Planner |

### Adım 3 — Günlük Plan Alımı (Sorumlu: Haberleşme + Görev Planlayıcı)

| Alt-adım | Açıklama |
|----------|----------|
| 3.1 | Uplink penceresi açılana kadar bekle (link penceresi: **TBD:** başlangıç/bitiş) |
| 3.2 | Yer segmentinden günlük görev paketini al (ICD-005 formatında) |
| 3.3 | Görev Planlayıcı paketi doğrula: parametreler, enerji bütçesi tutarlılığı |
| 3.4 | Doğrulama başarılıysa planı aktif et; hata varsa önceki güvenli planı koru |

### Adım 4 — Keşif Operasyonu (Sorumlu: Navigasyon + Yerel Planlayıcı + Hareket Kontrolü)

| Alt-adım | Açıklama |
|----------|----------|
| 4.1 | Görev Planlayıcı global rotayı yayımla (ICD-001/002/003 üzerinden durum güncelleme) |
| 4.2 | Yerel Planlayıcı engel haritasını güncelle, anlık yol üret |
| 4.3 | Hareket Kontrolü waypoint'lere doğru hareketi icra et |
| 4.4 | Her **TBD:** saniyede FDIR subsistem sağlık kontrolü yap |
| 4.5 | Bilimsel sensörler: krater kenarına yaklaşınca spektroskopi/kamera başlat |
| 4.6 | Telemetri: her **TBD:** saniyede yer segmentine downlink (ICD-006) |

**Sürekli kontrol:** Güç Yönetimi dönüş enerjisi rezervini izle → %15 SoC altına düşme ihtimali varsa Görev Planlayıcıya CAUTION yayımla.

### Adım 5 — Öğleden Sonra Enerjiy Değerlendirmesi (Sorumlu: Görev Planlayıcı)

| Alt-adım | Açıklama |
|----------|----------|
| 5.1 | Mevcut SoC ve öngörülen tüketim ile dönüş enerji hesabı yap |
| 5.2 | Hesaplanan dönüş marjı < %25 SoC → operasyon süresini kıs, dönüş hazırlığına geç |
| 5.3 | Güneş açısı düşüyorsa panel yeniden yönlendir |
| 5.4 | Yer segmentine öğle durum raporu gönder |

### Adım 6 — Safe Haven Dönüş Manevrası (Sorumlu: Navigasyon + Görev Planlayıcı)

| Alt-adım | Açıklama |
|----------|----------|
| 6.1 | Görev Planlayıcı dönüş tetikleyicisine ulaşınca (enerji, zaman veya yer komutu) RETURN_REQUIRED durumuna geç |
| 6.2 | Navigasyon safe haven koordinatlarına A* rota hesapla |
| 6.3 | Hareket Kontrolü dönüş rotasını icra et |
| 6.4 | Her güvenli konuma ulaşımda checkpoint kaydet (acil durumda fallback noktası) |
| 6.5 | Safe haven'a varışta sistem durumunu doğrula, yer segmentine nihai günlük rapor gönder |

### Adım 7 — Gece Hazırlığı (Sorumlu: Termal + Güç Yönetimi)

| Alt-adım | Açıklama |
|----------|----------|
| 7.1 | Panel güneş izlemesini kapat |
| 7.2 | Termal Yönetimi: ısıtıcıları aktive et, kritik bileşenleri minimum sıcaklık üzerinde tut |
| 7.3 | Güç Yönetimi: gece hayatta kalma güç moduna geç, devre dışı bırakılabilir yükleri kes |
| 7.4 | FDIR gece izleme modunu başlat (düşük frekanslı heartbeat) |

---

## 4. PSR Giriş Senaryosu

PSR operasyonu en yüksek risk taşıyan görev fazıdır. Aşağıdaki akış, güvenlik önce prensibinin uygulandığı koşullu geçiş mantığını gösterir.

### 4.1 Giriş Öncesi Koşul Doğrulama

| Koşul | Sorumlu Modül | Kabul Eşiği |
|-------|---------------|-------------|
| Batarya SoC | Güç Yönetimi | **TBD:** minimum % SoC (tam dönüş + güvenlik marjı karşılanmalı) |
| Navigasyon doğruluğu | Navigasyon | <0.5 m RMS konum hatası |
| Yer iletişimi | Haberleşme | Son başarılı uplink < **TBD:** dakika önce |
| Termal bütçe | Termal Yönetimi | Tüm kritik bileşenler nominal aralıkta |
| Hava durumu (lokal) | Navigasyon | Toz fırtınası tespiti yok |
| FDIR durumu | FDIR | NOMINAL veya CAUTION (RETURN_REQUIRED'da giriş yok) |

**Tüm koşullar sağlanmazsa PSR girişi iptal edilir ve araç bekleme moduna geçer.**

### 4.2 PSR İçi Operasyon

| Adım | Açıklama | Kritik Parametre |
|------|----------|-----------------|
| 4.2.1 | PSR sınırını geç; FDIR PSR moduna geç (artırılmış izleme frekansı) | — |
| 4.2.2 | Aktif aydınlatma başlat (LED veya spotlight) | Güç tüketimi artışını enerji bütçesine ekle |
| 4.2.3 | Yerel Planlayıcı görüş kısıtlı navigasyon moduna geç | LiDAR/stereo ağırlığını artır |
| 4.2.4 | Her **TBD:** saniyede enerji tüketimi ve batarya durumunu değerlendir | Dönüş tetikleyici SoC eşiği |
| 4.2.5 | Bilimsel numune/ölçüm al | spektroskopi, termal ölçüm, fotoğraf |
| 4.2.6 | Haberleşme kaybı beklenir; otonom karar alma devreye girer | link_timeout = **TBD:** saniye |

### 4.3 Dönüş Kararı

Aşağıdaki koşullardan **herhangi biri** tetiklendiğinde araç PSR'dan çıkışa başlar:

| Tetikleyici | Eşik | Öncelik |
|------------|------|---------|
| Batarya SoC dönüş eşiği | **TBD:** % SoC | P1 (en yüksek) |
| Planlanan PSR görev süresi doldu | **TBD:** dakika | P2 |
| Yer "PSR çıkış" komutu alındı | — | P2 |
| Termal kritik uyarı | **TBD:** °C | P1 |
| Navigasyon lokalizasyon kaybı | Konum belirsizliği > **TBD:** m | P1 |

### 4.4 Acil Dönüş

P1 tetikleyici karşılandığında araç derhal **son bilinen güvenli waypoint**'e döner:

1. FDIR SURVIVAL durumuna geçer
2. Tüm bilimsel operasyonlar dondurulur
3. Hareket Kontrolü acil dönüş rotasını hesaplar (mevcut harita + son bilinen pozisyon)
4. Güç Yönetimi hayatta kalma modunu aktive eder (yalnızca navigasyon + FDIR + haberleşme beslemede kalır)
5. PSR dışına çıkıldığında yer segmentine acil durum paketi gönderilir

---

## 5. Kriz Senaryoları

### Senaryo A — Haberleşme Kaybı

**Tetikleyici:** Downlink veya uplink kesintisi > **TBD:** dakika (link_timeout)

| Adım | Araç Kararı | Yer Bildirimi |
|------|-------------|---------------|
| A.1 | Otonom mod aktif: görev planı yerel kopyadan devam | Yer, link kaybını anlık bildirir |
| A.2 | FDIR durum makinesi CAUTION → iç ses mesajı (PSR içinde değilse) | — |
| A.3 | Haberleşme modülü yeniden bağlantı girişimi (her **TBD:** saniyede retry) | — |
| A.4 | link_timeout_extended (> **TBD:** dakika) → RETURN_REQUIRED | Yer segmenti DF anteni ile konum arar |
| A.5 | Safe haven'a varış → sistem yeniden bağlantı bekler, düşük güç modunda bekle | Yer segmenti araçtan ping alınca bağlantıyı yeniden kurar |

**Kurallar:** Link yokken araç yeni risk almaz; sadece mevcut planı tamamlar veya döner.

---

### Senaryo B — Enerji Kritik (%15 SoC Altı)

**Tetikleyici:** SoC < %15 veya öngörülen dönüş enerjisi yetersiz

| Adım | Araç Kararı | Yer Bildirimi |
|------|-------------|---------------|
| B.1 | FDIR CAUTION → tüm bilimsel yükler ve opsiyonel subsistemler kesilir | Telemetride CAUTION flag |
| B.2 | Güç Yönetimi hayatta kalma güç bütçesini hesapla | — |
| B.3 | SoC < %15 ise RETURN_REQUIRED: safe haven rotasına başla | Kritik enerji uyarısı downlink |
| B.4 | SoC < %10 ise SURVIVAL: yalnızca navigasyon + FDIR + haberleşme beslemede | Acil enerji paketi gönder |
| B.5 | Safe haven ulaşımında güneş panelini konumlandır, şarj bekle | Yer segmenti enerji durumunu izler |

**Not:** %15 SoC nominal dönüş marjı; B.3 adımında araç konum ve termal kayıpları da hesaba katar.

---

### Senaryo C — Lokalizasyon Kaybı

**Tetikleyici:** Navigasyon konum belirsizliği > **TBD:** m RMS veya EKF (Extended Kalman Filter) uyumsuz

| Adım | Araç Kararı | Yer Bildirimi |
|------|-------------|---------------|
| C.1 | Hareket Kontrolü dur (position hold / sıfır hız komutu) | FDIR lokalizasyon kaybı uyarısı gönder |
| C.2 | Navigasyon son bilinen iyi pozisyonu referans al | — |
| C.3 | Yeniden lokalizasyon girişimi: IMU dead-reckoning + görsel landmark eşleştirme | — |
| C.4 | **TBD:** sn içinde lokalizasyon geri geldi → CAUTION'dan çık, harekete devam | — |
| C.5 | Lokalizasyon geri gelmediyse → RETURN_REQUIRED; last-known-good waypoint üzerinden geri dön | Yer segmenti lokalizasyon kaybı bildir |
| C.6 | Lokalizasyon hiç geri gelmezse → SURVIVAL; radar/kamera yardımıyla dead-reckoning safe haven | Acil önlem aktivasyon bildirimi |

---

### Senaryo D — Termal Kritik

**Tetikleyici:** Herhangi bir izlenen bileşen sıcaklığı makul eşik dışına çıkar

| Adım | Araç Kararı | Yer Bildirimi |
|------|-------------|---------------|
| D.1 | FDIR termal uyarısı üretir; Termal Yönetimi devreye girer | CAUTION flag downlink |
| D.2 | Isıtma/soğutma sistemi aktive et; sıcaklığı **TBD:** saniye içinde nominal aralığa çek | — |
| D.3 | Termal kritik bölge devam ediyorsa: sıcaklığa katkıda bulunan yükleri kes | — |
| D.4 | Sıcaklık `max_critical` eşiğini geçerse → RETURN_REQUIRED; güneşe dik yüzeyden uzaklaş | Kritik termal uyarısı gönder |
| D.5 | Hızlı aşırı ısınma (rate > **TBD:** °C/dak) → SURVIVAL; acil güç kesimi + konuma bak | Acil termal paketi gönder |

---

## 6. Yer-Araç Sınırı

### 6.1 Komut Tipleri

| Komut Tipi | Açıklama | Öncelik | Araç Üzerine Etkisi |
|------------|----------|---------|---------------------|
| **TC-IMMEDIATE** | Acil durdur, acil dönüş, acil güç kapat | P1 | FDIR bypass ile direkt icra |
| **TC-CONDITIONAL** | "X koşulu sağlanırsa yap" | P2 | FDIR doğrulaması sonra icra |
| **TC-PLAN** | Günlük görev paketi yükle | P3 | Görev Planlayıcı doğrular |
| **TC-PARAM** | Parametre güncelleme (eşik, zaman aşımı) | P3 | Subsistem onayı gerekir |
| **TC-QUERY** | Telemetri/durum isteği | P4 | Bilgi akışı, eylem yok |

### 6.2 Link Penceresi

**TBD:** Orbital mekanik simülasyonu tamamlandığında gerçek link pencere zamanları (başlangıç, süre, frekans) eklenecektir. Yüksek kazançlı anten yönelimi de bu analize bağlıdır.

**Tipik varsayım (yer değiştirilecek):** Günde yaklaşık 2–4 link penceresi, her pencere 15–45 dakika.

### 6.3 Link Yokken Kurallar

1. Araç aktif görev planını devam ettirir — yeni risk almaz, PSR girişi yapmaz.
2. Durum makinesi CAUTION'da kalır; RETURN_REQUIRED'a geçiş kendi tetikleyicileriyle olur.
3. Otonom karar alma yetkisi tam aktif: Görev Planlayıcı ve FDIR bağımsız çalışır.
4. Link penceresi açıldığında araç tamponlanmış tüm telemetriyi önce boşaltır, ardından yeni komut alır.
5. Çakışan komut + otonom karar: **TC-IMMEDIATE** her zaman önce gelir; diğer komutlar FDIR onayından geçer.

---

## 7. Temel Prensipler (Referans)

| Prensip | Açıklama |
|---------|----------|
| **Güvenlik Önce** | Hiçbir görev hedefi güvenlik durumu gerekliliklerini geçersiz kılamaz |
| **Yer-Uçuş Ayrımı** | Yer segmenti planlama ve analiz yapar; anlık kararlar uçuş segmentine aittir |
| **Belirsizlik Görünür** | Tüm tahmin ve hesaplamalar belirsizlik bandıyla yayımlanır |
| **Simülasyon Doğrulamadan Önce** | Her yeni görev parametresi dijital ikizde test edilmeden uygulanamaz |
| **Arayüz Tabanlı Modülerlik** | Modüller yalnızca tanımlı ICD mesajları üzerinden haberleşir |

---

*Sonraki adım: Donanım parametreleri (batarya kapasitesi, panel alanı, termal limitler) geldikten sonra tüm TBD alanları güncellenecek ve CONOPS versiyon 1.0 yayımlanacaktır.*
