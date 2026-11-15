# LUNA-AI güvenlik bütçesi — entegrasyon taslağı

Kaynak: LUNA-AI-DATA-REQ-001 §4–5. **Bu dosya çalışan uçuş güvenlik sistemi değildir.**

## Wh/m hesabı
Varsayımsal sabit güç/hız yaklaşımı:

\[e_{travel,model} = P_{drive}/(3600v) = 300/(3600\times0.1)=0.833333\ \mathrm{Wh/m}\]

Bu değer *ölçülmüş regolit tekerlek enerjisi* değildir; eğim/kayma/tekerlek verimi için düzeltme ve deney gerekir.

## Dönüş rezervi

\[E_{reserve}=D_{return}\,e_{travel}+P_{heater}t_{dark}+E_{margin}\]

Ölçülmüş `e_travel`, `P_heater`, `t_dark` ve rezerv marjı eksik olduğundan kesin sayı üretilemez. Yetersiz bilgiyi **UNKNOWN** say.

## Termal

Basitleştirilmiş düğüm modeli (ancak parametreler doğrulanınca):
\[(mc_p)\,\frac{dT}{dt} = P_{heater}+Q_{internal}-G(T-T_{env})-Q_{radiative}\]

`mc_p`, `G`, MLI/ışınım modeli, başlangıç sıcaklığı ve malzeme sınırları bilinmediği için termal hayatta kalma süresi hesaplanamaz. 5 °C emniyet marjı belge gereksinimidir, hesaplanan marj değildir.

## Haberleşme

15 dakika kesintide uyarı, 60 dakika kesintide zorunlu dönüş belge hedefidir. `ay_api` Dünya görüşünün geometrisini hesaplar; gerçek RF link bütçesi/anten/yer istasyonu ve FDIR zaman aşımı henüz uygulanmış değildir.

## İntegrasyon

Repo kökündeki mevcut `safety/safety_budget.md` dosyasıyla çatışma kontrolünden sonra elle bütünleştirilmelidir.
