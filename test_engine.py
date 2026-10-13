"""Offline tests; never require an API key or place trades."""
import unittest,datetime,sys,types
try:
    import flask,requests
except ImportError:
    flask=types.ModuleType('flask')
    class Flask:
        def __init__(self,*args,**kwargs):pass
        def route(self,*args,**kwargs):return lambda fn:fn
    flask.Flask=Flask
    flask.jsonify=lambda x:x
    flask.send_from_directory=lambda *args:None
    sys.modules['flask']=flask
    sys.modules['requests']=types.ModuleType('requests')
from app import analyze,evaluate

def candles(direction=1, count=120, interval=300):
    start=datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(seconds=interval*(count-1))
    rows=[]
    for i in range(count):
        p=4100+direction*i*.45
        rows.append({'t':(start+datetime.timedelta(seconds=i*interval)).strftime('%Y-%m-%d %H:%M:%S'), 'o':p-.1,'h':p+.6,'l':p-.6,'c':p+.2})
    return rows
class EngineTests(unittest.TestCase):
    def test_bull_trend(self):
        x=analyze(candles(),300)
        self.assertEqual(x['bias'],'HAUSSIER')
        self.assertTrue(x['fresh'])
    def test_bear_trend(self):
        self.assertEqual(analyze(candles(-1),300)['bias'],'BAISSIER')
    def test_old_data_rejected(self):
        x=candles()
        for r in x:
            r['t']='2020-01-01 00:00:00'
        self.assertFalse(analyze(x,300)['fresh'])
    def test_missing_frames_wait(self):
        self.assertEqual(evaluate({})['direction'],'ATTENTE')
    def test_conflict_wait(self):
        f={k:analyze(candles(1 if k!='H1' else -1,interval=n),n) for k,n in [('H4',14400),('H1',3600),('M15',900),('M5',300)]}
        self.assertEqual(evaluate(f)['direction'],'ATTENTE')
if __name__=='__main__':unittest.main()
