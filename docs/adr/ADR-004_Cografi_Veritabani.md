# ADR-004: Coğrafi Veritabanı Seçimi

**Durum:** Kabul Edildi  
**Tarih:** 2026-11-14  
**İlgili Bileşenler:** Ground Segment — Bilimsel Analiz, Görev Tasarımı, DEM İşleme

---

## Bağlam

Ground Segment, aşağıdaki uzamsal veri gereksinimlerini karşılamalıdır:

- **DEM (Digital Elevation Model):** Ay LOLA (Lunar Orbiter Laser Altimeter) ve Kaguya/SELENE verileri; güney kutup için 5–60 m/piksel çözünürlük; dosya boyutları GB mertebesinde
- **PSR haritalama:** Kalıcı gölge bölgeleri polygon olarak saklanır; ışın izleme simülasyonu sonuçları
- **Uzamsal sorgular:** "Belirli koordinat etrafında X km yarıçaplı alanda güvenli arazi var mı?", "Bu rotada eğim > Y° olan segmentler hangileri?" gibi sorguların hızlı yanıtlanması gerekir
- **Raster + vektör:** DEM raster (grid), PSR ve hedef bölgeler vektör (polygon); ikisi birlikte sorgulanmalı
- **Versiyon ve provenance:** Farklı DEM kaynaklarının (LOLA v1, LOLA v2, Kaguya) sürüm yönetimi; hangi verinin hangi kararı etkilediği izlenebilmeli

---

## Değerlendirilen Alternatifler

### Alternatif 1: PostgreSQL + PostGIS

**Artılar:**
- PostGIS: endüstri standardı açık kaynak uzamsal veritabanı eklentisi; GDAL ile tam entegrasyon
- OGC standardı uzamsal sorgular (ST_Within, ST_Distance, ST_Slope, raster analiz) eksiksiz destekli
- Raster ve vektör aynı motorda; karışık sorgular mümkün
- Python eklentisi (psycopg2, SQLAlchemy+GeoAlchemy2): doğrudan entegrasyon
- ACID uyumlu; veri tutarlılığı garantili
- Versiyon yönetimi ve provenance için tablo şeması esnekliği yüksek
- Uzay/coğrafya sektöründe (EO veri katalogları, USGS, NASA) geniş kullanım geçmişi

**Eksiler:**
- Ek servis gerektiriyor (PostgreSQL sunucusu); altyapı karmaşıklığı artar
- Büyük DEM raster verilerini veritabanına yüklemek (pg_raster_loader) zaman alabilir
- Uzak sahada offline kullanım için taşınabilirlik zorlukları (çözüm: SQLite/SpatiaLite yedek)

---

### Alternatif 2: MongoDB

**Artılar:**
- Esnek şema: gelişen veri modeli için düşük maliyet
- Coğrafi sorgular için 2dsphere indeksleme destekli (GeoJSON)
- Yatay ölçekleme kolay

**Eksiler:**
- **Kritik eksik:** Raster analiz (DEM işleme) yerel olarak desteklenmiyor; GDAL ile entegrasyon için ara katman yazılması gerekir
- PostGIS'in uzamsal analiz fonksiyonlarının (ST_Slope, raster istatistik) MongoDB'de karşılığı yok
- ACID garantisi daha kısıtlı; veri tutarlılığı için ekstra dikkat
- Uzay bilimi topluluğunda MongoDB kullanım geçmişi PostGIS'e kıyasla çok sınırlı

---

### Alternatif 3: Flat-file + GDAL

**Artılar:**
- Altyapı bağımlılığı yok; saf dosya sistemi
- GDAL: endüstri standardı coğrafi veri formatları (GeoTIFF, Shapefile, GeoPackage, HDF5)
- Çok büyük DEM dosyaları için streaming/windowed okuma verimliliği yüksek
- Araştırma ortamında hızlı prototipleme

**Eksiler:**
- Uzamsal sorgular için tüm filtreleme Python kodu gerektirir; PostGIS optimizasyonları (R-tree indeksleme) yok
- Birden fazla veri kaynağı ve sürüm yönetimi için ad-hoc çözümler gerekir
- Eşzamanlı erişim (birden fazla kullanıcı aynı anda sorgu çalıştırması) yönetimsiz
- Veri bütünlüğü garantisi yok; risk proje büyüdükçe artar

---

## Karar

**PostgreSQL 15+ + PostGIS 3.4+** seçilmiştir; büyük DEM raster dosyaları için GDAL flat-file katmanı **yardımcı araç** olarak korunur.

**Mimarisi:**
- Vektör verisi (PSR polygonları, hedef noktalar, güzergah segmentleri, waypoint'ler): PostGIS geometri tablolarında
- Raster metadata ve örneklenmiş DEM verisi (ör. analiz sonucu ızgara): PostGIS raster tablolarında
- Ham DEM dosyaları (büyük boyutlu orijinaller): GeoTIFF flat-file deposunda; PostGIS'e yalnızca gerekli kesitler yüklenir
- Versiyon ve provenance: `data_source`, `loaded_at`, `version_tag` sütunları; tam değişim geçmişi event tablosunda

**Gerekçe:** MongoDB raster analizi için yetersizdir. Flat-file indeks ve eşzamanlılık eksikliği nedeniyle operasyonel kullanım için uygun değildir. PostGIS+GDAL kombinasyonu hem uzamsal analiz gücü hem de Python ekosistemi entegrasyonu açısından en güçlü seçenektir.

---

## Sonuçlar ve Kısıtlar

1. **Offline/Uzak kullanım:** İnternet bağlantısız yerde (saha operasyonu veya entegrasyon testi) `SpatiaLite` (SQLite üzerine PostGIS benzeri eklenti) yedek olarak sağlanacaktır; otomatik sync mekanizması tasarlanacaktır.
2. **Büyük DEM performansı:** Boyutu > **TBD** GB olan DEM dosyaları raster tabloya doğrudan yüklenmeyecek; GDAL windowed okuma ile analiz yapılacaktır. Eşik belirleme için benchmark testi gereklidir.
3. **Şema sürüm yönetimi:** Alembic (migration aracı) zorunlu; şema değişiklikleri migration dosyası olmadan uygulanamaz.
4. **Yedekleme:** PostGIS verisi günlük pg_dump ile yedeklenir; DEM flat-file deposu checksumlu arşivleme ile korunur.
5. **Lisans:** PostgreSQL ve PostGIS açık kaynak (PostgreSQL License / GPL); maliyet yok.
