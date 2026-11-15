# Üç dosyanın birlikte uyumu — teknik rapor

## Kapsam
1. `ay_api.py`: sıralama (% verimlilik/% risk), elips içi eğim/pürüzlülük, zamanlı Güneş/Dünya görüşü, 2D harita ve JSON.
2. `ay_navigator.py`: LOLA yükseklik DEM, Horn eğimi ve blok maksimum, SPICE, A* rota, enerji döngüsü, katalogdan krater mesafesi, CSV/PNG çıktıları.
3. `LUNA_AI_DATA_REQ_001_ORIJINAL.md`: ENV 6 + VEH 8 + PWR 8 + THM 5 + NAV 5 + COM 4 = **36** giriş.

`config/requirements_catalog.json` ve `.csv` içinde **36/36 satır**, asıl belgedeki alanları ve kodun ne ölçüde karşıladığını birleştirir. `null` değer = veri henüz bilinmiyor; 0 değildir.

## Kritik teknik farklar (üstü örtülmedi)

- 447 kg VIPER referansı belgedeki 100–300 kg genel şablonundan farklıdır. 5.420 Wh batarya, belgedeki 500–1500 Wh aralığından farklıdır. Bunlar aynı araç spesifikasyonuymuş gibi karıştırılmadı.
- Kodun 15° **rota sınırı** ile belgedeki 20–30° **tırmanma beklentisi** farklıdır. 15° **iniş** sınırı ayrı değerlendirilir.
- `ay_api`deki 100 m yerel detrend yükseklik standart sapması (10 m skor sıfırlama) ile belgedeki iniş ayağı için 0,30 m RMS sınırı fiziksel olarak eşdeğer değildir; 20m LOLA DEM ile <=0.30m güvenlik onayı verilemez.
- `%100 verimlilik` veya `%0 risk` tanımı ağırlıklı göreli/ampirik skordur, olasılıksal kaza riski değildir.
- `ay_api`de gölge oranından çıkarılan `karanlik` haritası onaylanmış kalıcı **ShadowCam PSR sınırı** değildir.
- Kaya haritası yok; Diviner sıcaklık haritası yok; sensör/EKF ve regolit parametreleri yok. Radar/kaya/termal güvenliği hesaplandı diye sunulamaz.
- `spiceypy` gerekli; SPICE kernelleri internetten indirilebilir ama bu ZIP içinde bulunmaz. `ay_navigator` NASA DEM'in yalnız ROI parçasını almaya çalışır; bu işlem bu ortamda gerçek ağda doğrulanmış değildir.
- İletişim yalnızca **geometrik Dünya görüşü**; gerçek RF link, anten kazancı ve yer istasyonu şartları yok.
- `-85.42°, +31.62°` sabit bir ROI merkezi (kodda referans), doğrulanmış tekil iniş yeri/krater merkezi değildir.
- Enerjiye göre karanlıkta dayanma (Wh/W), **termal hayatta kalma süresi** değildir.
- Depoda önceden bulunan `Site20_final_adj_5mpp_slp.tif` dosyası **slope/eğim** verisidir; doğrudan yükseklik DEM `--dem` olarak kullanılamaz.
- PGDA referans ürünlerinin DEM raster çerçevesi DE421/MOON_ME etiketi taşıyabilir; SPICE DE440 başka efemeris modelidir. Koordinat/projeksiyon dönüşümü test edilmelidir.

## Tamamlanmayan kritik girdiler

`COM-01` kesin görev tarihi, `PWR-02` kimya+SoC güvenlik sınırları, `VEH-06` ölçülmüş Wh/m, `THM-02/03` ısıtma+termal karanlık süresi, `NAV-01/02/03` sensor EKF, `VEH-08` gerçek mast yüksekliği, `ENV-03` gerçek PSR, `ENV-05` kaya, `ENV-06` sıcaklık, `COM-02` RF modeli.

`config/tbd_register_luna.md` tüm açık gereksinimleri listeler; mevcut `config/tbd_register.md` üzerinde otomatik değişiklik yapılmaz.

## Repo dosyalarıyla eşleme

| Belgenin hedefi | Paket içeriği | İlgili işlem |
|---|---|---|
| `domain/mission/constraints/hard_constraints_catalog.yaml` | `domain/mission/constraints/hard_constraints_proposed.yaml` | Mevcut katalogla elle merge |
| `config/tbd_register.md` | `config/tbd_register_luna.md` | Eşikler teyit edilince açık kaydı kapat |
| `data-platform/` | `data-platform/inputs/planetary/data_manifest.json` | Harita rasterlarını ROI ve CRS ile veri hattına bağla |
| `safety/safety_budget.md` | `safety/safety_budget_luna_proposed.md` | Eksik güç, termal ve rezerv modelini doğrulayıp merge et |
| `interfaces/v1/*` | `interfaces/v1/luna_ui_contract.json`, `run_integration.py`, `server.py` | Frontend JSON ve API ile bağlansın |

ÖNEMLİ: Bunlar kendi `luna-ai-viper/` alanında **önerilen dosyalar**dır, mevcut repo servislerini kendiliğinden değiştirmez.
