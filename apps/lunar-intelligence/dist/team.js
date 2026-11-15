// Team analysis (arayuz_sonuc.json, main branch) — loaded at runtime like an API response.
// Source: LOLA 20 m DEM + NASA/JPL SPICE sun/Earth geometry, produced by the team's pipeline.
const EN={egim:'Slope (p95 in ellipse)',puruzluluk:'Surface roughness',iletisim:'Earth visibility (comms)',gunes:'Solar illumination (energy)',karanlik_hedef:'Access to dark (PSR) target',yerel_rolyef:'Local relief',veri_guvenilirligi:'Data reliability'};
const UNIT={egim:'° (95th pct in landing ellipse)',puruzluluk:'m (100 m window std)',iletisim:'fraction of time Earth visible',gunes:'fraction of time sunlit',karanlik_hedef:'m to nearest dark target',yerel_rolyef:'m (height range in ellipse)',veri_guvenilirligi:'fraction of measured pixels'};
import {teamProfiles} from './team_profiles.js';
let data=null;
try{const r=await fetch('./arayuz_sonuc.json',{cache:'no-store'});if(r.ok)data=await r.json();}catch(e){console.warn('team analysis not loaded',e);}
function toZone(z,missions){
  const k=z.kriterler,m=missions.find(x=>x.site_id===z.id)?.ozet;
  const contributions=Object.entries(k).map(([key,c])=>({key,name:EN[key]||c.ad,weight:c.agirlik/100,value:c.skor*100,contribution:c.puan,
    explanation:`Team pipeline criterion. Raw value: ${c.ham_deger} ${UNIT[key]||c.birim}. Score 1 = ideal, 0 = must not land.`,
    formula:`raw ${c.ham_deger} → score ${c.skor} (0–1)`}));
  const mission=m?`Rover mission: route ${m.rota_uzunluk_m} m, max slope ${m.rota_maks_egim_deg}°, drive ${m.gidis_suresi_saat} h, SOC on arrival ${m.soc_varis_pct}%, enough energy to return: ${m.donus_icin_yeterli_enerji?'yes':'no'}.`:'';
  return {id:z.id,lat:z.lat,lon:z.lon,x:0,y:0,profileSeed:z.sira,
    slopeDeg:k.egim.ham_deger,roughness:k.puruzluluk.ham_deger,rockCover:null,hazardFree:k.veri_guvenilirligi.ham_deger,
    edgeKm:k.karanlik_hedef.ham_deger/1000,referenceClearance:1,stability:null,
    team:true,profile:teamProfiles[z.id],teamContributions:contributions,teamTotal:z.verimlilik_yuzde,teamRisk:z.risk_yuzde,hardLimitExceeded:z.sert_sinir_asildi,
    teamNote:`Team analysis (LOLA 20 m DEM + SPICE) · ${z.tur==='en_verimli'?'most efficient':'most risky'} #${z.sira} · efficiency ${z.verimlilik_yuzde}% / risk ${z.risk_yuzde}%${z.sert_sinir_asildi?' · HARD LIMIT EXCEEDED':''}. ${mission}`};
}
export const teamSite=data?{
  id:'mons-mouton-team',name:'Mons Mouton — Team analysis (SPICE, 20 m)',kind:'team',
  lat:data.ortam.bolge_merkez.lat,lon:data.ortam.bolge_merkez.lon,diameter:10,depth:0,
  depthLabel:'Sun / Earth elev.',depthText:`${data.ortam.gunes.yukseklik_deg}° / ${data.ortam.dunya.yukseklik_deg}°`,
  region:'SOUTH POLAR HIGHLAND · MONS MOUTON · TEAM PIPELINE',
  description:`Team result ${data.tarih_utc} · ${data.istatistik.aday_sayisi} candidates, ${data.istatistik.sert_sinir_asan_aday} exceeded hard limits · ${data.veri_kaynaklari.gunes_dunya}`,
  shift:5,warnings:data.uyarilar,
  zones:[...data.en_verimli,...data.en_riskli].map(z=>toZone(z,data.gorev_ozetleri||[]))
}:null;
