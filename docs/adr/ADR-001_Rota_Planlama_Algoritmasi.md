# ADR-001: Rota Planlama Algoritması

**Durum:** Kabul Edildi  
**Tarih:** 2026-11-14  
**İlgili QAR:** PLAN-001, PLAN-002, PLAN-004, NAV-001

---

## Bağlam

LUNA-AI, Ay yüzeyinde PSR (Kalıcı Gölge Bölgesi) içeren kraterlere gidip dönmek zorundadır. Rota planlaması aşağıdaki kısıtlar altında çalışır:

- **Enerji bütçesi:** Rota yalnızca geometrik optimum değil, enerji maliyetli (eğim, aydınlanma, motor gücü) olmalıdır. Yokuş çıkmak daha fazla enerji tüketir; yokuş aşağı rejenerasyon varsa modele dahil edilmelidir.
- **Termal state:** Araç gölgeli bölgelerde uzun kalmak isteyebilir (soğutma) veya istemeyebilir (ısınma gereksinimi). Rota bu tercihi yansıtmalıdır.
- **Kaynak kısıtı:** Araç üzerindeki işlemci gücü ve bellek sınırlıdır. Algoritmik karmaşıklık pratik çalışma süresi içinde kalmalıdır.
- **Dinamik engel:** PSR içinde ve dışında önceden bilinmeyen engeller (kayalar, çukurlar) mevcuttur. Planlama hem global hem de lokal düzeyde çalışmalıdır.
- **Replanning:** Yeni engel tespitinde < 30 saniye içinde yeniden planlama yapılmalıdır (PLAN-002).

---

## Değerlendirilen Alternatifler

### Alternatif 1: A* (A-Yıldız)

**Artılar:**
- Optimal çözüm garantisi (admissible heuristic ile)
- Geniş literatür desteği; uzay görevlerinde kullanım geçmişi var
- Statik harita üzerinde verimli; bellek yönetimi öngörülebilir
- Heuristic fonksiyonuna enerji maliyeti ve termal tercih eklemek görece kolay (weighted A*)
- Formal doğrulama kolaylaştıran deterministik yapı

**Eksiler:**
- Dinamik engellerde haritanın tamamı veya büyük bölümü yeniden planlanabilir
- PSR içi yüksek çözünürlüklü harita ile bellek tüketimi artabilir
- Çok boyutlu maliyet fonksiyonu (enerji + termal + mesafe) heuristic tasarımını karmaşıklaştırır

---

### Alternatif 2: D* Lite (Dinamik A*)

**Artılar:**
- Dinamik engellerde inkremental replanning → sadece değişen kısımlar yeniden hesaplanır
- A*'dan türetildiği için optimal çözüm korunur
- Gerçek zamanlı değişen haritalarda belirgin verimlilik artışı

**Eksiler:**
- Referans implementasyonlar A*'dan daha az test edilmiş uzay ortamında
- Durum güncelleme mekanizması enerji/termal ağırlıklı heuristic ile entegrasyonda ekstra tasarım gerektirir
- Debug ve formal doğrulama A*'dan daha zor

---

### Alternatif 3: RRT* (Rapidly-exploring Random Tree)

**Artılar:**
- Yüksek boyutlu durum uzaylarında (6-DOF araç) verimli
- Non-holonomik kısıtları (araç dönüş yarıçapı) doğal olarak modelleyebilir

**Eksiler:**
- Stokastik yapı: aynı girdiyle farklı sonuç → deterministik gereksinim ihlali (FDIR-005 analog)
- Optimal çözüm garantisi yalnızca asimptotik; pratik sürede optimal olmayabilir
- Hesaplama maliyeti A* ve D*'dan tipik olarak yüksek; kaynak kısıtlı ortamda risk
- Tekrarlanabilirlik ve formal doğrulama güçtür

---

### Alternatif 4: Potential Field (Potansiyel Alan)

**Artılar:**
- Son derece hızlı ve hafif; gerçek zamanlı yerel engel kaçınma için uygun
- Implementasyon basitliği; hata ayıklama kolay

**Eksiler:**
- Lokal minimum tuzakları: krater geçitlerinde veya dar koridorlarda takılabilir
- Güvenli dönüş yolu garantisi yok; bu görev için kabul edilemez güvenlik riski (P1)
- Global optimum garanti edilmez; uzun rotalarda enerji israfı

---

## Karar

**Hibrit mimari benimsenmiştir:**

- **Global Planlama:** Weighted A* — enerji, termal tercih ve eğim maliyeti heuristic'e dahil edilmiş A* varyantı. Görev başında ve replanning gerektiğinde çalışır (< 60 s garantisi, PLAN-001).
- **Yerel/Reaktif Planlama:** D* Lite tabanlı inkremental güncelleme — LiDAR/kamera'dan gelen yeni engel verisi geldiğinde sadece etkilenen alanı günceller (< 30 s replanning, PLAN-002).
- **Kısa mesafe engel kaçınma:** Potential Field kullanılmaz; D* Lite lokal güncellemesi bu rolü üstlenir.

**Gerekçe:** RRT* deterministik gereksinimi karşılamadığı için elendi. Potential Field lokal minimum riski nedeniyle güvenlik açısından kabul edilemez. A* ve D* Lite'ın hibrit kullanımı hem optimal global çözümü hem de dinamik verimliliği sağlar.

---

## Sonuçlar ve Kısıtlar

1. **Heuristic bakımı:** Enerji-ağırlıklı heuristic fonksiyonu donanım enerji parametreleri gelince (TBD-PWR) kalibre edilmelidir; başlangıçta konservatif (overestimate etmez) değerlerle devreye alınacaktır.
2. **Harita çözünürlüğü:** Global harita çözünürlüğü (**TBD:** m/piksel — DEM verisi bekleniyor) bellek bütçesini belirleyecektir.
3. **Yeniden planlama eşiği:** D* Lite güncelleme tetikleyicisi engel boyutu ve konum farkı üzerinden ayarlanmalıdır; çok sık tetiklemek işlemci yükünü artırır.
4. **Simülasyon önce:** Her heuristic değişikliği dijital ikizde doğrulanmadan üretime alınamaz (Simülasyon Doğrulamadan Önce prensibi).
5. **ICD bağımlılığı:** Planlayıcı, Güç Yönetiminden (ICD-001) ve Termal Yönetiminden (ICD-002) enerji/termal state alır; bu arayüzler kilitlenene kadar heuristic basit mesafe hedefleriyle çalışır.
