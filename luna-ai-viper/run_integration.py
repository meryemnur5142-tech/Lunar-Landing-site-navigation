#!/usr/bin/env python3
"""Repo içinde çakışmadan ay_api gerçek/sentetik JSON'unu arayüze uyarlar."""
from __future__ import annotations
import argparse,json,pathlib,sys
from ay_api import analiz, json_guvenli
HERE=pathlib.Path(__file__).resolve().parent

def read_conf():
    return json.loads((HERE/'config'/'mission_inputs.json').read_text(encoding='utf-8'))

def assemble(mode='demo', utc=None, output=None, *, generate_images=True, mission_data_override=None):
    conf=mission_data_override or read_conf()
    region=conf['region'];timeline=conf['timeline'];params=conf['scoring'];dat=conf['real_data']
    if mode not in ('demo','real'): raise ValueError("mode must be 'demo' or 'real'")
    t=(utc or (timeline['demo_epoch_utc'] if mode=='demo' else timeline['mission_epoch_utc']))
    if not t: raise ValueError('Gerçek analiz için tarih girin (--utc veya mission_epoch_utc).')
    out=pathlib.Path(output) if output else HERE/'generated'
    out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    if mode=='real':
        demfile=dat['dem_geotiff_path']
        if not demfile: raise ValueError('Gerçek DEM dosya yolu tanımlı değil; config/mission_inputs.json real_data.dem_geotiff_path gerekli.')
        dem=pathlib.Path(demfile)
        if not dem.is_absolute(): dem=(HERE/dem).resolve()
        if not dem.is_file(): raise ValueError(f'Gerçek yükseklik DEM bulunamadı: {dem}; EĞİM rasterını DEM diye kullanmayın.')
        err=dat.get('dem_error_geotiff_path')
        if err:
            err=pathlib.Path(err)
            if not err.is_absolute(): err=(HERE/err).resolve()
            if not err.is_file(): raise ValueError(f'ERR dosyası bulunamadı: {err}')
        kernel=dat.get('spice_kernel_directory') or str(HERE/'kernels')
        if not pathlib.Path(kernel).is_absolute(): kernel=str((HERE/kernel).resolve())
    else:
        dem=None;err=None;kernel=str(HERE/'kernels')
    result=analiz(t,dem_yolu=str(dem) if dem else None,err_yolu=str(err) if err else None,
          lon=region['center_lon_deg_east'],lat=region['center_lat_deg'],yari_km=region['roi_radius_km'],
          sentetik=(mode=='demo'),cikti=str(out),agirliklar=params['weights'],ayar=params['settings'],
          kernel_dir=kernel,gorsel=generate_images,gorev_adedi=1 if mode=='demo' else 2,
          log=lambda *a:print(*a,file=sys.stderr))
    requirements=json.loads((HERE/'config'/'requirements_catalog.json').read_text(encoding='utf-8'))['gereksinimler']
    missing=[r['kod'] for r in requirements if r.get('teyit_gerekiyor')]
    def local_path(full):
        if not full:return None
        p=pathlib.Path(full).resolve()
        try: return p.relative_to(out).as_posix()
        except ValueError: return None
    sites=[]
    for site in result['en_verimli']+result['en_riskli']:
        sites.append({'id':site['id'],'kind':site['tur'],'longitude_deg_east':site['lon'],'latitude_deg':site['lat'],
          'efficiency_pct':site['verimlilik_yuzde'],'risk_pct':site['risk_yuzde'],
          'constraints_violated':site['sert_sinir_asildi'],'criteria':site['kriterler'],'warnings':site['uyarilar'],
          'image_relative_path':local_path(site['gorsel_png'])})
    portable_raw=json.loads(json.dumps(json_guvenli(result),ensure_ascii=False))
    portable_raw['genel_harita_png']=local_path(result['genel_harita_png'])
    for group in ('en_verimli','en_riskli'):
        for site in portable_raw[group]:
            site['gorsel_png']=local_path(site['gorsel_png'])
    payload={'schema_version':'1.0','mode':'demo_synthetic' if mode=='demo' else 'real_preliminary',
       'is_synthetic':bool(result['sentetik_demo']),'can_claim_safe_landing':False,
       'source_data_ready':False, 'terrain_and_spice_computed':bool(mode=='real'), 'missing_requirements':missing,
       'sites':sites,'environment':result['ortam'],'rover_reference':result['rover_bilgi'],
       'assets':{'general_map':local_path(result['genel_harita_png'])},'warnings':result['uyarilar'],
       'raw_result':portable_raw}
    (out/'luna_frontend.json').write_text(json.dumps(json_guvenli(payload),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return payload

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['demo','real'],required=True)
    ap.add_argument('--utc',help='ISO UTC date e.g. 2026-11-27T00:00:00Z')
    ap.add_argument('--out',help='Output folder (defaults to generated)')
    ap.add_argument('--no-images',action='store_true')
    a=ap.parse_args()
    try:
        p=assemble(a.mode,a.utc,a.out,generate_images=not a.no_images)
        print(json.dumps({'output':str(pathlib.Path(a.out or HERE/'generated')/'luna_frontend.json'),
                          'mode':p['mode'],'site_count':len(p['sites']), 'safe_landing_certified':False},ensure_ascii=False))
    except Exception as e: sys.exit(f'HATA: {e}')
