# LUNA-AI — Havacılık ve Uzay Mühendisliği Veri İhtiyaç Belgesi

**Belge ID:** LUNA-AI-DATA-REQ-001  
**Versiyon:** 1.0  
**Tarih:** 2026-11-14  
**Hedef Sistem:** LUNA-AI (Ay Krateri Keşif ve Otonom Görev Sistemi)  
**İlgili Repo:** `meryemnur5142-tech/Lunar-Landing-site-navigation`  
**Referans Standartlar:** IAU_MOON_2015, NASA SPICE DE440, MIL-STD-1629A  

---

## 1. Yönetici Özeti ve Hızlı Kontrol Listesi (P-CRIT — Bloke Edici Veriler)

Aşağıdaki **7 parametre**, simülasyon ve rota planlama motorunu doğrudan bloke eden en kritik (P-CRIT) girdilerdir. Havacılık ekibinden ilk aşamada bu değerlerin kesinleştirilmesi beklenmektedir:

- [ ] **1. Görev Başlangıç Tarihi (UTC Epoch):** Ephemeris ve aydınlanma pencereleri için tarih (2024–2035 aralığı).
- [ ] **2. Batarya Kapasitesi ve Kimyası:** $Wh$ kapasitesi, min/maks güvenli şarj-deşarj limitleri ve kimyasal türü (LiFePO4, NMC vb.).
- [ ] **3. Zemin Tüketim Katsayısı ($e_{\text{travel}}$):** Ay regolitinde rover'ın 1 metre ilerlemesi için harcanan enerji ($Wh/m$).
- [ ] **4. Isıtıcı Gücü ($P_{\text{heater}}$) ve Karanlık Toleransı:** PSR içinde donmadan hayatta kalabileceği maksimum süre (dakika).
- [ ] **5. Sensör Paketi & Gürültü Modeli:** LiDAR/Kamera tipi, IMU gyro/akselerometre sürüklenme katsayıları ($\sigma_{\text{drift}}$).
- [ ] **6. Mast / Anten Yüksekliği ($h_{\text{mast}}$):** Ufuk taraması ve Dünya görüşü için rover direk yüksekliği ($m$).
- [ ] **7. Hedef Krater Bölgesi Koordinatları:** İniş ve analiz yapılacak kraterin merkez enlem/boylamı (LOLA/ShadowCam veri çekimi için).

---

## 2. Gezegensel & Çevresel Veriler (Planetary & Environment Data)

Krater analizi, iniş alanı seçimi, aydınlanma ve PSR tespiti için gerekli uzaktan algılama ve orbital veriler:

| No | Veri / Katman Adı | Fiziksel Format / Tip | Çözünürlük & Kapsam | İlgili Repo Modülü / Şema | Açıklama |
|:---|:---|:---|:---|:---|:---|
| **ENV-01** | **LOLA DEM (Yükseklik Modeli)** | GeoTIFF (`.tif`) / 2D NumPy array | 5m – 20m/px (bölgesel 80m/px) | `data-platform/processing/terrain_analyzer.py` | Horn (1981) yöntemi ile eğim ve pürüzlülük türetimi için. |
| **ENV-02** | **DEM Doğruluk Payı ($\sigma_{\text{vertical}}$)** | Float (metre) | 1-sigma dikey hata payı ($\approx 1.0\text{ m}$) | `environment_product.schema.yaml` | Belirsizlik yayılımı (*Uncertainty Visible*) hesabı için zorunludur. |
| **ENV-03** | **ShadowCam PSR Maskesi** | GeoJSON Poligon / Binary Raster | $< 2\text{ m/px}$ çözünürlük | `domain/environment/models.py` | Kalıcı gölge bölgelerinin sınırları ve erişilebilirlik alanı. |
| **ENV-04** | **SPICE DE440 Efemeris Verileri** | SPICE Kernelleri (`.bsp`, `.tpc`) | 2024–2035 zaman aralığı | `earth_visibility_windows.schema.yaml` | Güneş ve Dünya'nın yerel ufuk üstü yükseklik açıları ve tutulmalar. |
| **ENV-05** | **Kaya & Engel Yoğunluk Haritası** | 2D Float Array (`[0.0 - 1.0]`) | $\le 5\text{ m/px}$ (LROC NAC bazlı) | `hard_constraints_catalog.yaml` (`HC-003`) | Engel fraksiyonu ($\le 0.20$ eşiği; aşan alanlar elenir). |
| **ENV-06** | **Diviner Yüzey Sıcaklık Haritası** | Kelvin ($K$) veya $^\circ\text{C}$ Grid | Ay Kutbu ($40\text{ K} - 120\text{ K}$) | `hard_constraints_catalog.yaml` (`HC-013`) | Safe haven ve iniş elipsi termal uygunluğu. |

---

## 3. Araç Fiziksel & Mobilite Parametreleri (§10 Araç Tasarımı)

İniş dinamiği, devrilme kararlılığı ve otonom rota planlayıcı ($A^*$) için araç spesifikasyonları:

| Parametre Kodu | Parametre Adı | Birim | Beklenen Aralık | İlgili Kısıt / Modül | Öncelik |
|:---|:---|:---|:---|:---|:---|
| **VEH-01** | Araç Kütlesi ($M_{\text{rover}}$) | $\text{kg}$ | $100 - 300\text{ kg}$ | `vehicle/mobility-control` | P-MED |
| **VEH-02** | Maksimum Tırmanma Açısı ($\theta_{\text{climb}}$) | Derece ($^\circ$) | $20^\circ - 30^\circ$ | `HC-005` (Çevre Profil Eğimi) | P-HIGH |
| **VEH-03** | Maksimum İniş Eğim Sınırı ($\theta_{\text{max}}$) | Derece ($^\circ$) | $\le 15^\circ$ | `HC-001` (İniş Alanı Eğimi) | P-HIGH |
| **VEH-04** | Maksimum Yüzey Pürüzlülüğü ($RMS_{\text{max}}$) | Metre ($\text{m}$) | $\le 0.30\text{ m}$ | `HC-002` (İniş Bacak Limiti) | P-HIGH |
| **VEH-05** | Nominal Gezinti Hızı ($v_{\text{nom}}$) | $\text{m/s}$ | $0.05 - 0.15\text{ m/s}$ | `autonomy/global-planner` | P-HIGH |
| **VEH-06** | Zemin Enerji Tüketim Katsayısı ($e_{\text{travel}}$) | $\text{Wh/m}$ | Araç tekerlek/motor eğrisi | `safety/safety_budget.md` | **P-CRIT** |
| **VEH-07** | 3-Sigma İniş Elipsi Yarı Eksenleri | Metre ($\text{m}$) | $a=500\text{m},\ b=250\text{m}$ | `domain/crater/models.py` | P-MED |
| **VEH-08** | Mast / Anten Yüksekliği ($h_{\text{mast}}$) | Metre ($\text{m}$) | $0.5 - 2.0\text{ m}$ | `simulation/environment-model` | P-HIGH |

---

## 4. Enerji Alt Sistemi Parametreleri (Power Subsystem)

Planlayıcının güvenli dönüş garantisi vermesini sağlayan bütçe verileri:

| Parametre Kodu | Parametre Adı | Birim | Beklenen / Varsayılan Değer | İlgili Kısıt / Modül | Öncelik |
|:---|:---|:---|:---|:---|:---|
| **PWR-01** | Toplam Batarya Kapasitesi ($C_{\text{bat}}$) | $\text{Wh}$ | $500 - 1500\text{ Wh}$ | `resource_state.schema.yaml` | P-HIGH |
| **PWR-02** | Batarya Kimyası & Güvenli Sınırlar | Metin / Tip | LiFePO4 / NMC / Li-Po | `power/`, `thermal/` | **P-CRIT** |
| **PWR-03** | Minimum PSR Giriş SoC Eşiği | Yüzde ($\%$) | $\ge \%80 - \%90$ | `HC-008` | **P-CRIT** |
| **PWR-04** | Dönüş Enerji Rezervi Modeli ($E_{\text{reserve}}$) | $\text{Wh}$ | $(D \times Wh/m) + E_{\text{heat}} + Margin$ | `HC-006` | **P-CRIT** |
| **PWR-05** | Güneş Paneli Nominal Gücü ($P_{\text{panel}}$) | $\text{Watt}$ | $300 - 800\text{ W}$ | `power/`, `HC-009` | P-HIGH |
| **PWR-06** | Panel Yönelim / Verim Fonksiyonu | Model | $\cos(\theta_{\text{sun}})$ veya servo takip | `domain/mission/models.py` | P-HIGH |
| **PWR-07** | Sistem Taban Yükü (Avionik/Hotel) | $\text{Watt}$ | $50 - 100\text{ W}$ (Sabit tüketim) | `power/` | P-HIGH |
| **PWR-08** | Enerji Tahmin Belirsizliği ($\sigma_{\text{energy}}$) | Yüzde ($\%$) | $\pm \%10 - \%20$ | `domain/environment/uncertainty_policy.md` | P-HIGH |

---

## 5. Termal Alt Sistem Parametreleri (Thermal Subsystem)

PSR içindeki aşırı soğuk ortamda ($\sim 40\text{ K}$) bileşen hasarını önleyen termal kısıtlar:

| Parametre Kodu | Parametre Adı | Birim | Beklenen / Varsayılan Değer | İlgili Kısıt / Modül | Öncelik |
|:---|:---|:---|:---|:---|:---|
| **THM-01** | Termal Kütle ($m \cdot c_p$) & İletkenlik ($G$) | $\text{J/K}$ ve $\text{W/K}$ | Araç gövdesi & MLI izolasyonu | `thermal/`, `HC-007` | **P-CRIT** |
| **THM-02** | Isıtıcı Güç Tüketimi ($P_{\text{heater}}$) | $\text{Watt}$ | $50 - 200\text{ W}$ | `safety/safety_budget.md` | P-HIGH |
| **THM-03** | Maksimum Karanlık Dayanım Süresi | Dakika | $30\text{ dk} - 120\text{ dk}$ | `HC-007`, `HC-010` | **P-CRIT** |
| **THM-04** | Kritik Bileşen Min/Maks Çalışma Limitleri | $^\circ\text{C}$ | Batarya: $[0^\circ\text{C}, 45^\circ\text{C}]$<br>Avionik: $[-40^\circ\text{C}, +60^\circ\text{C}]$ | `interfaces/v1/thermal_state.py` | **P-CRIT** |
| **THM-05** | Termal Marj Güvenlik Eşiği ($\Delta T_{\text{margin}}$)| $^\circ\text{C}$ | $5^\circ\text{C}$ (FDIR erken uyarı) | `safety/safety_budget.md` | P-HIGH |

---

## 6. Algı, GNC ve Navigasyon Parametreleri (Sensors & GNC)

Lokalizasyon, Kalman Filtresi (EKF) ve FDIR (Arıza Tespiti) eşikleri için:

| Parametre Kodu | Parametre Adı | Birim | Beklenen Değer | İlgili Kısıt / Modül | Öncelik |
|:---|:---|:---|:---|:---|:---|
| **NAV-01** | Sensör Paketi Konfigürasyonu | Liste / Model | LiDAR (Menzil, FOV), Stereo Kamera | `vehicle/localization`, `perception` | **P-CRIT** |
| **NAV-02** | IMU Gyro/İvmeölçer Sürüklenme ($\sigma_{\text{drift}}$) | $^\circ/\text{hr},\ \text{m/s}^2$ | EKF sensör gürültü kovaryansı | `uncertainty_policy.md §3.1` | **P-CRIT** |
| **NAV-03** | Tekerlek Odometri Hata Oranı ($\sigma_{\text{odo}}$) | Yüzde ($\%$) | Mesafe başına kayma oranı | `uncertainty_policy.md §3.1` | **P-CRIT** |
| **NAV-04** | İniş GNC Handover Konum Belirsizliği | Metre ($\text{m}$) | Yüzeye iniş anındaki ilk hata | `vehicle/landing-gnc` | P-HIGH |
| **NAV-05** | İzin Verilen Maksimum Konum Hatası | Metre ($\text{m}$) | Düz arazi: $<0.5\text{m}$, PSR: $<1.0\text{m}$, Alarm: $>2.0\text{m}$ | `docs/qar/QAR_TABLE.md` (`NAV-001..006`) | P-HIGH |

---

## 7. İletişim & Görev Zamanı Parametreleri (Communication & Timeline)

| Parametre Kodu | Parametre Adı | Birim | Beklenen Değer | İlgili Kısıt / Modül | Öncelik |
|:---|:---|:---|:---|:---|:---|
| **COM-01** | Görev Başlangıç Tarihi (Epoch) | UTC (`YYYY-MM-DD`) | 2024–2035 arası bir tarih | `config/open_inputs.md` | **P-CRIT** |
| **COM-02** | Anten Tipi ve Kazanç Profili | Tip / dBi | Low-Gain / High-Gain Anten | `communication/`, `HC-014` | **P-CRIT** |
| **COM-03** | Minimum Dünya Görünürlük Açısı ($\theta_{\text{elev}}$)| Derece ($^\circ$) | $\ge 5^\circ$ (Ufuk maskesi) | `HC-014`, `HC-018` | P-HIGH |
| **COM-04** | İletişim Zaman Aşımı (Link Timeout) | Saniye / Dk | Uyarı: $15\text{ dk}$, Zorunlu Dönüş: $60\text{ dk}$ | `safety/safety_budget.md` | P-HIGH |

---

## 8. Verilerin Repoya Entegrasyon Kılavuzu

Havacılık ekibiniz verileri hazırladığında dosyalar aşağıdaki konumlara entegre edilecektir:

1. **Sayısal Eşik Değerleri:** [`domain/mission/constraints/hard_constraints_catalog.yaml`](file:///C:/Users/MSİ/.gemini/antigravity/scratch/Lunar-Landing-site-navigation/domain/mission/constraints/hard_constraints_catalog.yaml) içindeki `threshold: null` olan satırlara yazılır.
2. **Kapanan TBD Kayıtları:** [`config/tbd_register.md`](file:///C:/Users/MSİ/.gemini/antigravity/scratch/Lunar-Landing-site-navigation/config/tbd_register.md) dosyasında ilgili satır `KAPALI` olarak işaretlenir.
3. **Raster ve Harita Verileri (DEM, PSR):** `data-platform/` altındaki veri alım hattına girdi olarak bağlanır.
4. **Fiziksel Formüller (Dönüş Rezervi, Termal Marj):** [`safety/safety_budget.md`](file:///C:/Users/MSİ/.gemini/antigravity/scratch/Lunar-Landing-site-navigation/safety/safety_budget.md) dosyasına kesin formül olarak işlenir.

