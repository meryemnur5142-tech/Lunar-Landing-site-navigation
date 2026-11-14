# ADR-006: Yer-Araç Haberleşme Protokolü

**Durum:** Kabul Edildi  
**Tarih:** 2026-11-14  
**İlgili QAR:** COM-001, COM-002, COM-003, COM-005  
**İlgili ICD:** ICD-005 (Uplink), ICD-006 (Downlink)

---

## Bağlam

Yer-araç haberleşmesi Ay mesafesinde (yaklaşık 384.000 km) gerçekleşmektedir:

- **Link budget kısıtı:** Zayıf sinyal, sınırlı anten kazancı ve bant genişliği; paket boyutunu küçük tutmak kritik
- **Gecikme:** Işık hızı gecikmesi ~1.3 saniye (tek yön); protokol bu gecikmeyle çalışmaya tasarlanmalı
- **Güvenilirlik önce:** Paket kaybı ve bitlerin bozulması beklenir; hata tespiti ve düzeltme zorunlu
- **Komut önceliği:** TC-IMMEDIATE komutları TC-PLAN komutlarından önce işlenmeli; protokol öncelik sıralamasını desteklemeli
- **Bant genişliği tasarrufu:** Tüm uplink/downlink verisi sıkıştırılabilir veya delta-encode edilebilir olmalı
- **Otonom çalışma:** Araç link yokken protokolden bağımsız çalışmalı; protokol durum makinesini etkilememeli
- **Standartlara uyumluluk:** İleride diğer ajans araçlarıyla veya yer istasyonlarıyla interoperability gerekebilir

---

## Değerlendirilen Alternatifler

### Alternatif 1: CCSDS (Consultative Committee for Space Data Systems)

**Artılar:**
- Uzay sektörü endüstri standardı (NASA, ESA, JAXA tüm misyonlarda kullanır)
- **Space Packet Protocol (CCSDS 133.0-B):** Telemetri paketleri için optimize edilmiş; başlık küçük, yük verimliliği yüksek
- **Telecommand (CCSDS 232.0-B):** Komut sırası yönetimi, onay mekanizması, öncelik sıralaması yerleşik
- **CCSDS File Delivery Protocol (CFDP):** Zaman gecikmeli linkler için güvenilir dosya transferi
- Reed-Solomon ve LDPC hata düzeltme kodları standart içinde tanımlı
- Interoperability: diğer ajans altyapısıyla doğrudan çalışabilir
- Açık standart; referans implementasyonlar mevcut (cFS/NASA, yamCS)

**Eksiler:**
- Standart öğrenmesi ve tam implementasyonu zaman alıcı; başlangıçta mühendislik yükü
- CCSDS araçları (packet decoder, telemetry monitor) uzman gerektirir
- Küçük ölçekli test ortamında overkill görünebilir

---

### Alternatif 2: MQTT (Message Queuing Telemetry Transport)

**Artılar:**
- Çok yaygın, öğrenmesi kolay; kapsamlı araç ekosistemi
- Publish-subscribe modeli esnek topolojilere uygun
- QoS seviyeleri (0/1/2) güvenilirlik kontrolü sağlar
- Prototip geliştirme hızlı

**Eksiler:**
- **Link budget sorunu:** TCP/IP altyapısı gerektirir; Ay mesafesinde TCP üç yönlü el sıkışma pratikte imkânsız (1.3 s RTT × handshake döngüleri)
- Paket öncelik yönetimi (TC-IMMEDIATE vs TC-PLAN) MQTT'de yerleşik değil; uygulamak için ek katman gerekir
- Hata düzeltme kodu (FEC) yok; uzay radyasyon ortamında bit hataları telafi edilemez
- Uzay görev iletişimi için sertifikalı referans uygulaması yok

---

### Alternatif 3: gRPC (Google Remote Procedure Call)

**Artılar:**
- Protocol Buffers: verimli ikili serileştirme; bant genişliği tasarrufu
- Güçlü tip sistemi ve API tanımı; yer-araç arayüz tanımı (ICD) kolaylaşır
- İki yönlü streaming desteği

**Eksiler:**
- **Kritik engel:** HTTP/2 üzerine kurulu; Ay linkinde HTTP/2 bağlantı durumunu yönetmek pratikte imkânsız (sürekli kopan link, gecikmeli ACK)
- Uzay haberleşmesi için tasarlanmamış; link budget optimizasyonu yok
- FEC ve öncelik yönetimi yoktur; ek katman gerektirir
- Uzay sektöründe kullanım geçmişi yok

---

## Karar

**CCSDS (Space Packet Protocol + Telecommand + CFDP)** seçilmiştir; implementasyon referansı olarak **NASA cFS (core Flight System)** uyumlu yapı benimsenecektir.

**Protokol katmanı:**
| Katman | Kullanılan Standart | Amaç |
|--------|--------------------|----|
| Veri bağlantı | CCSDS TM/TC Sync & Channel Coding | Bit hata düzeltme (Reed-Solomon veya LDPC) |
| Paket | CCSDS Space Packet (133.0-B) | Telemetri ve bilimsel veri downlink |
| Komut | CCSDS Telecommand (232.0-B) | Uplink; öncelik ve ACK yerleşik |
| Dosya transferi | CCSDS CFDP (727.0-B) | Görev planı yükleme, yazılım güncelleme |

**Öncelik yönetimi:** CCSDS TC katmanındaki `Priority` alanı TC-IMMEDIATE (P1) → TC-PLAN (P3) sıralamasını doğrudan karşılar.

**Gerekçe:** MQTT ve gRPC Ay link koşullarında fiziksel olarak çalışamaz (TCP handshake). CCSDS bağlantı bağımsız (connectionless) tasarımı ve link intermittency desteğiyle tek gerçekçi seçenektir.

---

## Sonuçlar ve Kısıtlar

1. **yamCS entegrasyonu:** Yer segmenti operatör arayüzü yamCS (Python tabanlı açık kaynak Mission Control System) üzerine kurulabilir; CCSDS natif desteklidir.
2. **Bant genişliği bütçesi:** Her paketin boyutu **TBD:** link bütçesi analizi tamamlandıktan sonra ayarlanacak; telemetri güncelleme periyotları buna göre belirlenir.
3. **Şifreleme:** CCSDS Security Layer (355.0-B) ilerleyen fazda değerlendirilecek; başlangıçta yalnızca CRC bütünlük kontrolü.
4. **Test ortamı:** CCSDS link simülatörü (örn. Linux'ta socat + paket kayıp enjeksiyonu) entegrasyon test ortamında kurulur; COM-005 bütünlük testi bu ortamda çalışır.
5. **Araç yük:**  CCSDS araçları mühendislik yükü taşır; ilk 2 aya araç eğitim planı zorunludur.
