import json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
class TestPackage(unittest.TestCase):
 def test_source_requirements_36(self):
  d=json.loads((ROOT/'config/requirements_catalog.json').read_text(encoding='utf8'))
  codes={r['kod'] for r in d['gereksinimler']}
  self.assertEqual(len(codes),36)
  self.assertEqual({c.split('-')[0]:len([x for x in codes if x.startswith(c.split('-')[0]+'-')]) for c in codes},
                   {'ENV':6,'VEH':8,'PWR':8,'THM':5,'NAV':5,'COM':4})
 def test_scorer_and_source_defaults_agree(self):
  import ay_api,ay_navigator
  p=json.loads((ROOT/'config/mission_inputs.json').read_text(encoding='utf8'))
  self.assertEqual(p['scoring']['weights'],ay_api.VARSAYILAN_AGIRLIK)
  self.assertEqual(p['rover']['parameters']['batarya_Wh'],ay_navigator.RoverParam().batarya_Wh)
  self.assertEqual(sum(p['scoring']['weights'].values()),100)
 def test_missing_remains_unset(self):
  p=json.loads((ROOT/'config/mission_inputs.json').read_text(encoding='utf8'))
  self.assertIsNone(p['real_data']['dem_geotiff_path'])
  self.assertIsNone(p['unresolved_critical']['battery_chemistry'])
  self.assertIsNone(p['timeline']['mission_epoch_utc'])
 def test_nonsafety(self):
  p=json.loads((ROOT/'config/mission_inputs.json').read_text(encoding='utf8'))
  self.assertEqual(p['status'],'INCOMPLETE_REAL_FLIGHT_NOT_VALIDATED')
if __name__=='__main__':unittest.main()
