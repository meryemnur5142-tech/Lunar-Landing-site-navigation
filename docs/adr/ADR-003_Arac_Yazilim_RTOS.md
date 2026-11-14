# ADR-003: Araç Yazılım Platformu ve RTOS Seçimi

**Durum:** Kabul Edildi  
**Tarih:** 2026-11-14  
**İlgili QAR:** FDIR-001, FDIR-002, FDIR-005, THM-001, PWR-003

---

## Bağlam

Flight Segment yazılımı aşağıdaki gereksinimleri karşılamalıdır:

- **Deterministik zamanlama:** FDIR < 50 ms anomali tespit (FDIR-001), < 10 ms yük kesme (PWR-004) gibi hard deadline'lar mevcuttur
- **FDIR güvenilirliği:** Kritik güvenlik kararları preempt edilemez veya stall edilemez; worst-case execution time (WCET) analizi yapılabilmeli
- **Radyasyon toleransı:** Uzay ışıması nedeniyle SEU (Single Event Upset) olayları beklenir; yazılım bu olaylardan sonra kurtarılabilir olmalı
- **Bellek kısıtı:** Araç üzerindeki RAM ve Flash **TBD** (donanım seçimine bağlı); deterministik bellek yönetimi kritik
- **Uzun görev ömrü:** Yazılım günler/haftalar boyunca hatasız çalışmalı; bellek sızıntısı tolerans edilemez
- **Donanım bağımsızlığı (kısmi):** Sensor ve motor arayüzleri değişebilir; sürücü katmanı ayrışık olmalı

---

## Değerlendirilen Alternatifler

### Alternatif 1: C++ / FreeRTOS

**Artılar:**
- FreeRTOS: geniş uzay proje kullanım geçmişi (CubeSat, küçük gezegen araçları)
- Açık kaynak; tam kaynak kodu erişimi; özelleştirme esnekliği
- C++ ile modern yazılım tasarımı (RAII, interface segregation); FDIR ve durum makineleri için güçlü araçlar
- Kütüphane ekosistemi geniş: CAN, SPI, I2C sürücüler kolayca eklenebilir
- Gerçek zamanlı performans yeterli: tick granülaritesi < 1 ms, preemptive scheduling
- MISRA-C++ uyumu zor değil; düşük seviyeli kontrol kolaylaşır

**Eksiler:**
- FreeRTOS zaman damgaları ve özellikler platform bağımlı; portability sınırlı
- Resmi DO-178C / ECSS sertifikası yok (ek çaba gerekir)
- C++ dinamik bellek yönetimi (new/delete) dikkatli kısıtlanmalı; operator override gerektirir

---

### Alternatif 2: C++ / VxWorks

**Artılar:**
- Havacılık/uzay sektöründe geniş sertifikasyon geçmişi; DO-178C desteği
- Determinizm ve WCET analizi araçları olgun
- Yüksek güvenilirlik kanıtlanmış; Mars Rover (Spirit, Opportunity) VxWorks kullanmıştır

**Eksiler:**
- **Lisans maliyeti:** Ticari lisans; proje bütçesine önemli yük ekler
- Kaynak kodu erişimi kısıtlı; bağımsız audit zorlaşır
- Topluluk desteği ve açık kaynak ekosistemi FreeRTOS/Zephyr'e kıyasla daha kapalı
- Küçük geliştirme ekibi için öğrenme eğrisi ve araç bağımlılığı

---

### Alternatif 3: Ada / RTEMS

**Artılar:**
- Ada güçlü tip sistemi ve derleme zamanı güvenlik kontrolleri: overflow, range, null dereference büyük oranda derleme zamanında yakalanır
- RTEMS (Real-Time Executive for Multiprocessor Systems): NASA projeleri kökenli, uzay sektöründe sertifikalı kullanım geçmişi
- SPARK Ada alt kümesi formal doğrulamayı mümkün kılar; FDIR durum makinesi formal kanıtlanabilir

**Eksiler:**
- Ada yetkin geliştirici bulmak son derece güç; ekip kadrosu riski yüksek
- Topluluk ve kütüphane ekosistemi C/C++'a kıyasla çok küçük; sürücü yazımı büyük oranda sıfırdan
- Geliştirme araçları (GNAT) ticari; açık kaynak GNAT FSF versiyonu bazı platform kısıtları içerir
- Prototipleme hızı yavaş; erken dönem iterasyon için olumsuz

---

## Karar

**C++ / FreeRTOS** seçilmiştir; ilerleyen fazlarda ECSS-E-ST-40C uyum çalışması planlanmıştır.

**Gerekçe:**
- VxWorks lisans maliyeti ve bağımlılığı proje için orantısız; açık kaynak mimarisi tercih edilir.
- Ada/RTEMS formal doğrulama avantajı cazip olmakla birlikte, ekip geliştirme kapasitesi ve kütüphane yokluğu riski kabul edilemez büyüklüktedir.
- FreeRTOS, ihtiyaç duyulan hard-realtime garantileri (preemptive scheduling, deterministic context switch) C++'ın güçlü tip sistemi ile birlikte sağlar.
- CubeSat ve küçük gezegen araçlarında kanıtlanmış kombinasyon olması olgunluk güvencesi verir.

**Zorunlu C++ kısıtları (uçuş kodu):**
- Dinamik bellek tahsisi (`new`/`delete`) uçuş kodu kritik yollarında yasak; önceden ayrılmış bellek havuzları (memory pool) kullanılır
- İstisnalar (exceptions) disabled; hata yönetimi return code + FDIR yoluyla
- RTTI (runtime type information) disabled
- Şablon kullanımı WCET etkisiz olanlarla sınırlı
- MISRA-C++ 2008 profiline uyum zorunlu; statik analiz (cppcheck, clang-tidy) CI'da gate

---

## Sonuçlar ve Kısıtlar

1. **Scheduler konfigürasyonu:** FreeRTOS görev öncelikleri FDIR > Navigasyon > Güç > Termal > Planlayıcı > Haberleşme olarak yapılandırılır; öncelik inversiyon mekanizması (priority inheritance mutex) aktif edilir.
2. **Watchdog tasarımı:** Her kritik görev (task) FreeRTOS watchdog timer'a heartbeat gönderir; heartbeat kaybı FDIR'ı doğrudan tetikler (ADR-005 ve SAFETY_STATE_MACHINE.md ile uyumlu).
3. **WCET analizi:** Kritik yollar (FDIR karar, yük kesme, navigasyon güncelleme) için WCET analizi yapılması zorunludur; araç: **TBD** (AbsInt aiT veya eşdeğeri).
4. **Bellek bütçesi:** Flash ve RAM kullanımı **TBD** (donanım BoM bekleniyor); statik bellek bütçesi analizi tasarım aşamasında tamamlanacak.
5. **Sürüm kontrolü:** Uçuş kodu build'ı git hash ile etiketlenir; bootloader sürüm doğrulaması yapılır.
