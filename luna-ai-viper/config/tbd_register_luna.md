# LUNA-AI: Açık Kararlar / TBD (Repo için ek liste)

| ID | Durum | Neden | İstenen doğrulama |
|---|---|---|---|
| ENV-01 | AÇIK | KAYNAK_TANIMLI_DOSYA_YOK | 20m kaynak URL kodda mevcut; gerçek GeoTIFF bu pakete eklenmedi. Önceden yüklenen Site20 eğim dosyası DEM yükseklik verisi değildir. |
| ENV-02 | AÇIK | OLCUM_DOSYASI_YOK | Belgedeki yaklaşık 1m bir ölçüm değil hedef bilgisi; ilgili ERR rasterı olmadıkça belirsizlik hesabı geçerli sayı vermez. |
| ENV-03 | AÇIK | KAYNAK_TESPITI_GEREK | Kodun karanlık hedefi 30gün örneklenmiş aydınlanmadan ürettiği yaklaşık maske; bu ShadowCam PSR poligonu değildir. |
| ENV-04 | AÇIK | KAYNAK_TANIMLI_DOSYA_YOK | Çekirdekler çalışma sırasında indirilebilir; MOON_ME frame ve dönem kapsamı çalışma zamanında doğrulanmalı. PGDA DEM üretimindeki DE421 referansı ile DE440 ephemeris aynı şey değildir. |
| ENV-05 | AÇIK | SADECE_BELGE_ESIGI | LROC NAC görüntüsü hazır kaya yoğunluğu rasterı değildir; kaya sınıflama doğrulanmadan değer yok. |
| ENV-06 | AÇIK | VERI_YOK | Diviner gerçek sıcaklık rastrı yok; 40–120K belge aralığı ölçüm yerine geçmez. |
| VEH-01 | AÇIK | VIPER_REFERANSI | 447 kg VIPER referansı; belgedeki 100–300 kg genel beklenen aralıkla ÇELİŞİYOR. |
| VEH-02 | AÇIK | TAKIM_VARSAYIMI | Rota max=15°; belgedeki 20–30° tırmanma hedefiyle FARKLI; bu eşik araç tarafından kanıtlanmadı. |
| VEH-04 | AÇIK | ESIK_UYUMSUZ | 0.3m iniş bacağı limitini, kodun 100m penceredeki 10m skor eşiği sağlamıyor; altmetre veri ve sert kısıt gerekli. |
| VEH-05 | AÇIK | TAKIM_VARSAYIMI | 0.10m/s; belge 0.05–0.15 m/s aralığına uyuyor. |
| VEH-06 | AÇIK | TÜRETILMIS_VARSAYIM | Bu basitleştirilmiş Wh/m=0.8333 tahminidir. Regolit, eğim, kayma, ısıtma ve gerçek sürüş eğrisi içermez; P-CRIT kapanmadı. |
| VEH-07 | AÇIK | TAKIM_VARSAYIMI | Yarı eksenler belgeye uyuyor fakat iniş GNC dağılımıyla teyit edilmedi. |
| VEH-08 | AÇIK | VARSAYIM_OLCUM_YOK | Varsayılan 2m yalnızca CLI için; ay_api Dünya oran hesabına mast yüksekliğini geçirmiyor. |
| PWR-01 | AÇIK | VIPER_REFERANSI | 5420Wh VIPER referansı; belgedeki 500–1500Wh genel aralıkla ÇELİŞİYOR. |
| PWR-02 | AÇIK | KIMYA_BELIRSIZ | Batarya kimyası ile donanım güvenli alt/üst SoC sınırları doğrulanmadı. 0.10 rezerv takım varsayımıdır. |
| PWR-03 | AÇIK | TAKIM_VARSAYIMI | 0.85 (85%) belge aralığına uyuyor; ancak ay_api puanlamasında ve navigatörde zorunlu PSR giriş kontrolü olup olmadığı ayrıca doğrulanmalı. |
| PWR-04 | AÇIK | FORMUL_VAR_EKSIK_GIRDI | Kod mevcut batarya döngüsünü simüle eder ama heater+belirsizlik güvenlik marjı için doğrulanmış girdiler yok. |
| PWR-05 | AÇIK | VIPER_REFERANSI | 320W tek yüz TEPE güç; toplam/nominal tüm panel gücü değildir. |
| PWR-06 | AÇIK | TAKIM_VARSAYIMI | Yönelim varsayımları araç kontrollü panel yönelimi ölçümü değildir. |
| PWR-07 | AÇIK | OLCUM_YOK | P_hibernasyon=108W toplam türetilmiş yük, aviyonik taban yükü olduğunu kanıtlamaz. |
| PWR-08 | AÇIK | BELGE_HEDEF_ARALIGI | ±%10–20 güven aralığı değil hedef; enerji belirsizlik yayılımı kodda yok. |
| THM-01 | AÇIK | VERI_YOK | None |
| THM-02 | AÇIK | BELGE_HEDEF_ARALIGI | 108W hibernasyon tüketimini ısıtıcı gücü olarak değerlendirmeyin. |
| THM-03 | AÇIK | TERMIK_SURE_OLCULMEDI | Karanlıkta enerjiyle çalışma saati, donmadan termal hayatta kalma süresi değildir. |
| THM-04 | AÇIK | BELGE_HEDEF_ARALIGI | None |
| NAV-01 | AÇIK | VERI_YOK | None |
| NAV-02 | AÇIK | VERI_YOK | None |
| NAV-03 | AÇIK | VERI_YOK | None |
| NAV-04 | AÇIK | VERI_YOK | None |
| COM-01 | AÇIK | DEMO_TARIH_VAR_GERCEK_YOK | Demo tarihi kesin görev tarihi yerine kullanılamaz. |
| COM-02 | AÇIK | VERI_YOK | None |

Bu dosyadaki AÇIK kayıtlar, mevcut repodaki `config/tbd_register.md` satırlarını otomatik KAPALI yapmaz.
