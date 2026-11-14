# ADR-005: Güvenlik Durum Makinesi Mimarisi

**Durum:** Kabul Edildi  
**Tarih:** 2026-11-14  
**İlgili QAR:** FDIR-001, FDIR-002, FDIR-004, FDIR-005  
**İlgili Belge:** docs/architecture/SAFETY_STATE_MACHINE.md

---

## Bağlam

LUNA-AI, birden fazla risk katmanını eş zamanlı olarak yönetmek zorundadır:

- **Dört güvenlik durumu:** NOMINAL, CAUTION, RETURN_REQUIRED, SURVIVAL
- **Çoklu tetikleyici:** Enerji, termal, navigasyon, haberleşme, iç yazılım arızası
- **Öncelik hiyerarşisi:** Birden fazla tetikleyici aynı anda aktif olduğunda hangi durum üstün gelir?
- **Dışa bağımsızlık:** FDIR durum makinesi Mission Planner'dan bağımsız çalışmalı; planlayıcı donsa bile güvenlik kararları çalışmaya devam etmeli
- **Deterministik davranış:** Aynı girdi seti aynı durum geçişini üretmeli (FDIR-005 analog: formal doğrulama gerektiriyor)
- **İzlenebilirlik:** Her geçiş log'lanabilir, test edilebilir ve bağımsız denetlenebilir olmalı

---

## Değerlendirilen Alternatifler

### Alternatif 1: Hiyerarşik Durum Makinesi (HSM)

**Artılar:**
- Durumlar arasında hiyerarşi (üst durum ortak davranışı miras alır); CAUTION → NOMINAL dönüşünde ortak temizleme mantığı paylaşılır
- 4 durum az; HSM karmaşıklığı bu ölçekte yönetilebilir
- UML durum diyagramı ile tam ifade edilebilir; formal analiz ve test kolaylaşır
- C++ şablon tabanlı HSM kütüphaneleri (Boost.Statechart, QP/C++) ile olgun implementasyon mümkün
- Deterministik: her event → tek geçiş; FDIR-005 gereksinimini doğal karşılar
- Watchdog entegrasyonu doğrudan: her state'in giriş/çıkış eylemlerine heartbeat reset eklenebilir

**Eksiler:**
- Yeni durum ekleme ileride şema değişikliği gerektiriyor; esneklik kısıtlı
- Paralel bölgeler (enerji + termal aynı anda bağımsız davransın) modellemek karmaşıklaşabilir

---

### Alternatif 2: Davranış Ağacı (Behavior Tree)

**Artılar:**
- Modüler: yeni koşul/eylem düğümleri hiyerarşiyi bozmadan eklenebilir
- Oyun/robotik AI alanında kanıtlanmış; görsel araçlar (Groot) ile izlenebilir
- Paralel dallar doğal: enerji kontrolü ve termal kontrol eş zamanlı çalışabilir

**Eksiler:**
- **Güvenlik kritik uyum zorluğu:** Davranış ağacının her tick döngüsünde tüm ağacı gezen yapısı WCET analizini zorlaştırır; < 50 ms garanti vermek için ek kısıtlama gerekir
- Durum makinesinin açık geçiş tablosuna kıyasla "mevcut durum" sorgulamak daha dolaylı; loging/audit zorlaşır
- Uzay FDIR bağlamında referans sertifikasyon geçmişi yok

---

### Alternatif 3: Kural Tabanlı Sistem

**Artılar:**
- IF-THEN kuralları anlaşılması en kolay yaklaşım; operatörler kural tablosunu okuyabilir
- Yeni kural ekleme görece basit

**Eksiler:**
- **Çakışma sorunu:** Birden fazla kuralın aynı anda tetiklenmesi (enerji kritik + lokalizasyon kaybı) tutarsız davranışa yol açabilir; öncelik belirsizliği güvenlik açığı
- Durum kalıcılığı (state persistence) yok; hangi durumda olduğunu hatırlamak için ek yapı gerekir → fiilen durum makinesi olur
- Formal doğrulama zordur; kural kombinasyonları üstel büyür

---

## Karar

**Hiyerarşik Durum Makinesi (HSM)** seçilmiştir; implementasyon için **QP/C++ (Quantum Platform) veya eşdeğer MISRA uyumlu HSM kütüphanesi** kullanılacaktır.

**Gerekçe:**
- 4 durum az; HSM yönetilebilir karmaşıklıkta kalır.
- Deterministik geçiş garantisi FDIR-005 gereksinimini karşılar.
- Formal doğrulama (TLA+ veya durum makinesi model checker) HSM üzerinde doğrudan uygulanabilir.
- UML durum diyagramı (PlantUML) standart dokümantasyon formatı; operatör ve mühendis anlaşmasını kolaylaştırır.
- QP/C++ MISRA-C++ uyumlu, uçuş kodu kısıtlarıyla uyumlu; DO-178C referans uygulaması mevcuttur.

**Paralel bölge gereksinimi:**
Enerji ve termal izleme, navigasyon ve haberleşme izlemeleri farklı modüllerde bağımsız çalışır; bunlar HSM'e event gönderir. HSM bu event'leri tek bir geçiş tablosunda birleştirir. Bu yaklaşım Davranış Ağacının paralel avantajını kapsar, deterministik geçiş garantisini korur.

---

## Sonuçlar ve Kısıtlar

1. **Mission Planner bağımsızlığı:** HSM, Mission Planner sürecinden farklı bir FreeRTOS görevinde çalışır; aralarındaki mesaj kuyruğu tek yönlüdür (Planner → HSM event gönderir; HSM → Planner kararını bildirir). HSM'in Planner'a bağımlılığı yoktur.
2. **Formal doğrulama:** HSM durum geçiş tablosu TLA+ ile model check edilecektir; verifikasyon tamamlanmadan araç sahnaya alınamaz.
3. **Genişletme kısıtı:** Yeni durum ekleme yalnızca mimari gözden geçirme (Architecture Review Board eşdeğeri) onayı ile yapılabilir; anlık hotfix yasak.
4. **Test kapsamı:** Her durum geçişi için en az 3 test senaryosu (normal yol, sınır değeri, hata enjeksiyonu) zorunludur.
5. **Detaylı tasarım:** SAFETY_STATE_MACHINE.md dosyasında PlantUML diyagramı, watchdog tasarımı ve durum tanımları yer almaktadır.
