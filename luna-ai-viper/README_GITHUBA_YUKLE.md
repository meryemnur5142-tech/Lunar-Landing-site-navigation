# LUNA-AI — 3 kaynakla uyumlu GitHub yükleme paketi

Kaynak dosyalar: `ay_api.py`, `ay_navigator(3).py` ve `LUNA_AI_Havacilik_Ekibi_Veri_Ihtiyac_Listesi_BU.md`.

**Ne hazır?** Tüm 36 gereksinimin JSON+CSV kataloğu, kodla eşlenmiş mühendislik parametreleri, önerilen YAML eşikleri, veri manifesti, boş/UNKNOWN GeoJSON ve krater CSV yapıları, iki Python analiz motoru, arayüz JSON adaptörü ve yerel API servisi.

**Ne hazır değil?** Gerçek NASA DEM/ERR rasterları, gerçek ShadowCam PSR, kaya/Diviner sıcaklık verileri, SPICE çekirdekleri, doğrulanmış iniş adayı ve eksik araç/termal/sensör ölçümleri. Bunları üretmiş ya da yüklemiş gibi davranılmadı.

## GitHub Desktop üzerinden güvenli ekleme

1. Repo `meryemnur5142-tech/Lunar-Landing-site-navigation` GitHub Desktop'ta açık olsun.
2. **Current branch** bölümüne bak; `main`e doğrudan göndermeyin. Önceki arazi dosyaları `veri/site20-arazi` dalında tutuluyordu; Python+data entegrasyonu için ayrı `luna-ai-viper-integration` dalı daha güvenlidir. Var olan dalın gerçekten hangisi olduğunu GitHub Desktop'ta kontrol edin.
3. ZIP'ten `luna-ai-viper/` klasörünü **deponun kök dizinine** kopyalayın. Üstteki mevcut `config/`, `data-platform/`, `domain/` klasörlerini **ASLA değiştirmeyin/silmeyin**.
4. GitHub Desktop **Changes** sekmesinde yalnız `luna-ai-viper/...` eklenen dosyaları seçip `Commit to luna-ai-viper-integration` deyin, ardından `Push origin`.
5. `Compare & pull request` otomatik birleştirme değildir; ileride ekip incelemesi için kullanılabilir. `main`e Merge yapmayın.

## Windows (Python kuruluysa) komutları

GitHub repo kökündeki `luna-ai-viper` klasörünün içine PowerShell ile girin:

```powershell
py -m pip install -r requirements.txt
py ay_api.py --test
py ay_navigator.py --test
py run_integration.py --mode demo
py server.py
```

Vite/React UI entegrasyonu için geliştirme sunucusu `http://127.0.0.1:8765`:

- `GET http://127.0.0.1:8765/api/status` → eksik/elde bulunan katmanlar
- `POST http://127.0.0.1:8765/api/analyze` body: `{"mode":"demo","utc":"2026-11-27T00:00:00Z"}` → anlık analiz
- `GET http://127.0.0.1:8765/api/result` → son analiz; daha önce analiz çalıştırılmazsa 404

Frontend arkadaşınla **önce** `examples/SENTETIK_DEMO_SADECE_UI/luna_frontend.json` dosyasını paylaşarak arayüz bileşenlerini ve dört nokta kartını test edebilirsin. Bu örnek NASA gerçek verisi olarak sunulamaz.
- `GET http://127.0.0.1:8765/assets/siteler/V1.png` → analiz sonrası harita

Sunucu yalnızca **localhost** için geliştirme aracıdır; internet üzerinde API olarak yayınlamayın. CORS varsayılanı Vite dev portu `http://localhost:5173`.

## Gerçek NASA veriyle çalıştırma

`config/mission_inputs.json` içindeki `real_data.dem_geotiff_path` alanına **yükseklik DEM** dosyasının gerçek yolunu yazın. Örneğin `data/terrain/site20/Site20_final_adj_5mpp_slp.tif` eğim dosyasıdır; **DEM yoluna yazmayın**.

`real_data.spice_kernel_directory` dizinini ayarlayın (ya da varsayılan `kernels/`; ilk çalıştırmada Internet isteyebilir). Sonra kesin görev tarihini `timeline.mission_epoch_utc` alanına **UTC** girin:

```powershell
py run_integration.py --mode real --utc 2026-11-27T00:00:00Z
```

**Dikkat:** Bu tarih yalnızca komut örneğidir, gerçek görev takvimi kararı değildir. `real` çıktı `real_preliminary` olur, `can_claim_safe_landing=false` kalır; eksik PSR/termal/kaya ve sensör verisi olmadan iniş güvenliği onayı verilmez.

## Çıktıların yeri

- `generated/arayuz_sonuc.json`: orijinal `ay_api` JSON yapısı
- `generated/luna_frontend.json`: frontend için normalize API sonucu
- `generated/siteler/*.png`, `generated/genel_harita.png`: 2D görseller

Çıktılar ve büyük haritalar `.gitignore` ile repoya alınmaz. Ancak `examples/SENTETIK_DEMO_SADECE_UI/` içinde **sadece arayüz önizlemesi için sentetik örnek sonuç ve PNG haritalar** bulunur; NASA ölçümü değildir. `config/requirements_catalog.csv` dosyasında **36 kaydın tamamı** ve kapsam durumları listelenmiştir.

## Belgeye uyarlama notu

Gereksinim belgesinin önerdiği mevcut repo dosyalarına doğrudan yazmak riskli olacağı için değişiklikler yalnız `luna-ai-viper/` içindeki `*_proposed` (taslak) dosyalarıdır. Ekip teknik değerlendirmesinden sonra asıl repo kataloglarına **merge** edilmeleri gerekir. Bu ZIP'in tek başına frontend'e/kökteki backend'e otomatik bağlandığını iddia etmiyoruz.
