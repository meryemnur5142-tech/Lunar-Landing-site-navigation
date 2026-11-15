// NASA JPL Horizons integration (via the local /horizons-proxy in serve.mjs).
// Query: target Moon (301), observer geocentre (500@399), quantities
//   14 = observer sub-point on the Moon (sub-Earth lon/lat)
//   15 = subsolar point on the Moon (lon/lat)
//   31 = Moon's ecliptic longitude/latitude seen from Earth
// Moon longitudes from Horizons are east-positive (0..360); normalised to -180..180.

const D2R=Math.PI/180;
const norm180=l=>((l+540)%360)-180;
const q=v=>`'${v}'`;
const fmt=d=>d.toISOString().slice(0,16).replace('T',' ');

export async function fetchMoonGeometry(date){
  const stop=new Date(date.getTime()+60000);
  const params=new URLSearchParams({
    format:'json',COMMAND:q('301'),OBJ_DATA:q('NO'),MAKE_EPHEM:q('YES'),EPHEM_TYPE:q('OBSERVER'),
    CENTER:q('500@399'),START_TIME:q(fmt(date)),STOP_TIME:q(fmt(stop)),STEP_SIZE:q('1m'),
    QUANTITIES:q('14,15,31'),ANG_FORMAT:q('DEG')
  });
  let res;
  try{res=await fetch('/horizons-proxy?'+params.toString());}
  catch(e){throw new Error('Horizons proxy erişilemedi: '+e.message);}
  const data=await res.json().catch(()=>{throw new Error('Horizons yanıtı JSON değil.');});
  if(data.error)throw new Error(data.error);
  const text=data.result||'';
  const soe=text.indexOf('$$SOE'),eoe=text.indexOf('$$EOE');
  if(soe<0||eoe<0)throw new Error('Horizons yanıtında efemeris tablosu yok: '+text.slice(0,200));
  const line=text.slice(soe+5,eoe).trim().split('\n')[0].trim();
  const nums=line.split(/\s+/).slice(2).map(Number);
  if(nums.length<6||nums.some(isNaN))throw new Error('Horizons satırı çözümlenemedi: '+line);
  const [obsLon,obsLat,sunLon,sunLat,eclLon,eclLat]=nums;
  return{
    date,
    subEarthLon:norm180(obsLon),subEarthLat:obsLat,
    subsolarLon:norm180(sunLon),subsolarLat:sunLat,
    moonEclLon:eclLon,moonEclLat:eclLat,
    source:`NASA JPL Horizons · ${fmt(date)} UTC`
  };
}

// Elevation (deg) of a body above the local horizon at (lat,lon), given the body's
// sub-point on the Moon. Smooth-sphere approximation: ignores local terrain/horizon masks.
function elevation(lat,lon,subLat,subLon){
  const s=Math.sin(lat*D2R)*Math.sin(subLat*D2R)+Math.cos(lat*D2R)*Math.cos(subLat*D2R)*Math.cos((lon-subLon)*D2R);
  return Math.asin(Math.max(-1,Math.min(1,s)))/D2R;
}
export const solarElevDeg=(lat,lon,g)=>elevation(lat,lon,g.subsolarLat,g.subsolarLon);
export const earthElevDeg=(lat,lon,g)=>elevation(lat,lon,g.subEarthLat,g.subEarthLon);
