# ADR-002: Yer Segmenti Programlama Dili

**Durum:** Kabul Edildi  
**Tarih:** 2026-11-14  
**İlgili Bileşenler:** Ground Segment — Bilimsel Analiz, Görev Tasarımı, Operatör Arayüzü

---

## Bağlam

Ground Segment aşağıdaki görevleri yerine getirir:

- **GDAL tabanlı DEM (Digital Elevation Model) işleme:** Ay yüzey yükseklik verileri (örn. LOLA, MiniRF) yükleme, dönüştürme, analiz
- **SPICE/SpiceyPy entegrasyonu:** NASA NAIF SPICE aracı kiti — orbital mekanik, aydınlanma analizi, güneş açısı hesaplama
- **Bilimsel veri analizi:** Spektroskopi, termal haritalama, PSR kaynak tahmin modelleri
- **Operatör arayüzü:** Web tabanlı veya masaüstü araç (görev planı görselleştirme, telemetri izleme)
- **Gerçek zamanlı gereksinim yok:** Yer segmenti soft-realtime; saniyeler mertebesinde gecikme tolere edilir

---

## Değerlendirilen Alternatifler

### Alternatif 1: Python

**Artılar:**
- SpiceyPy resmi Python bağlayıcısıdır; tam SPICE desteği
- GDAL/Rasterio Python ekosisteminde en olgun; kapsamlı dokümantasyon ve topluluk
- NumPy, SciPy, Pandas: bilimsel hesaplama için endüstri standardı
- Matplotlib, Plotly: görselleştirme
- NASA/ESA görev analiz araçlarının büyük çoğunluğu Python'da; interoperability yüksek
- Prototipleme hızı: hızlı iterasyon, küçük ekip için kritik avantaj
- Mevcut astro-veri bilim ekibi Python yetkin (varsayım)

**Eksiler:**
- GIL (Global Interpreter Lock): CPU-yoğun paralel işlemde performans sorunu; multiprocessing ile aşılabilir ama karmaşıklık artar
- Dinamik tip sistemi: büyük kod tabanında runtime hatalarına zemin hazırlar; tip ipuçları (mypy) ile kısmen azaltılır
- Bellek yönetimi kontrolsüz; büyük DEM dosyalarında dikkatli bellek yönetimi gerekir

---

### Alternatif 2: Go

**Artılar:**
- Güçlü eşzamanlılık modeli (goroutines): telemetri akışı ve paralel veri işleme için uygun
- Statik tip sistemi: derleme zamanı hata tespiti
- Küçük binary boyutu; deployment kolaylığı
- Hızlı derleme

**Eksiler:**
- **Kritik engel:** SpiceyPy / NAIF SPICE için Go bağlayıcısı bulunmuyor; CSPICE C kütüphanesi üzerinden CGO wrapper yazılması gerekir — bakımı zor, güvenlik riski
- GDAL Go bağlayıcısı (go-gdal) olgunlaşmamış; büyük DEM işlemede test edilmemiş
- Bilimsel hesaplama ekosistemi Python'a kıyasla son derece kısıtlı

---

### Alternatif 3: Rust

**Artılar:**
- Bellek güvenliği garantisi (ownership/borrow checker): kritik sistemlerde güçlü avantaj
- Yüksek performans; GIL yok
- Statik tip sistemi, kapsamlı derleme zamanı kontrolü

**Eksiler:**
- **Kritik engel:** SpiceyPy eşdeğeri Rust binding'i yok; CSPICE FFI katmanı yazılması gerekir — önemli mühendislik maliyeti
- GDAL Rust bağlayıcısı (gdal crate) gelişmekte ama olgunluk seviyesi Python/GDAL'ın çok altında
- Öğrenme eğrisi: Ay yüzey görevi kadrosu için rust yetkinliği kısa sürede kazanmak zor
- Bilimsel/veri analiz ekosistemi (plotting, stats) Python'a kıyasla yetersiz

---

## Karar

**Python 3.11+ (tip ipuçlı, mypy ile)** seçilmiştir.

**Gerekçe:**
- SpiceyPy ve GDAL/Rasterio entegrasyonu doğrudan ve olgun Python ekosisteminde mevcuttur; Go ve Rust için kritik bağımlılık engeli aşılamaz kabul edilmiştir.
- Yer segmentinin gerçek zamanlı kısıtı yoktur; Python performans eksiklikleri kabul edilebilir sınır içindedir.
- NASA açık kaynak uzay görev araçlarının (GMAT, OpenSPIFe, Basilisk) Python entegrasyonları mevcut; ekosistem uyumluluğu korunur.
- Küçük ekipte bilimsel üretkenlik kritik; Python prototipleme hızı rekabetsizdir.

**Kod kalitesi garantileri:**
- `mypy --strict` zorunlu (CI'da gate olarak)
- `ruff` / `black` stil denetimi
- Temel modüller için birim testi (%80 kapsam hedefi)
- Büyük DEM işleme: `rasterio`'nun `windowed reading` API'si ile bellek pencereleme

---

## Sonuçlar ve Kısıtlar

1. **Performans sınırı:** CPU yoğun rota analizi (büyük DEM üzerinde A* önizleme) için `multiprocessing` veya `Cython` eklentisi kullanılabilir; bu durum ortaya çıkana kadar saf Python tercih edilir.
2. **API sürüm kilitleme:** SpiceyPy, GDAL ve bilimsel kütüphane sürümleri `requirements.txt` + `poetry.lock` ile sabitlenir; otomatik yükseltme yasak.
3. **Uçuş segmentiyle dil sınırı:** Python kodu hiçbir zaman uçuş segmentine taşınamaz; yer-araç sınırı katı biçimde uygulanır.
4. **Veri formatı bağımsızlığı:** Yer segmenti Python'a bağımlı olmayan dosya formatları (GeoTIFF, FITS, JSON/CBOR) üzerinden çalışır; başka bir dile geçiş halinde veri miraslanabilir.
