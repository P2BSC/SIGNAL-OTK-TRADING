"""SIGNAL OTK V4: experimental multi-timeframe scanner, no trading execution."""
import os,time,threading,datetime,logging
from flask import Flask,jsonify,send_from_directory
import requests
from zoneinfo import ZoneInfo
app=Flask(__name__,static_folder='.')
API=os.getenv('TWELVE_DATA_API_KEY','')
INTERVALS={'M5':('5min',300),'M15':('15min',900),'H1':('1h',3600),'H4':('4h',14400)}
POLL_SECONDS=int(os.getenv('POLL_SECONDS','600'))  # 4 API calls / 10 minutes = 576/day, excluding retries/restarts
state={'status':'INITIALISATION','updated':None,'frames':{},'message':'En attente de données','signal':'ATTENTE','analysis':{}}
lock=threading.Lock()
def fetch(interval):
    r=requests.get('https://api.twelvedata.com/time_series',params={'symbol':'XAU/USD','interval':interval,'outputsize':120,'apikey':API,'timezone':'UTC'},timeout=25)
    r.raise_for_status(); j=r.json()
    if j.get('status')=='error' or not j.get('values'): raise ValueError(j.get('message','Réponse API vide'))
    return [{'t':x['datetime'],'o':float(x['open']),'h':float(x['high']),'l':float(x['low']),'c':float(x['close'])} for x in reversed(j['values'])]
def ema(values,n):
    v=values[0]; a=2/(n+1)
    for x in values[1:]:v=a*x+(1-a)*v
    return v
def analyze(rows,seconds):
    if len(rows)<55:raise ValueError('Historique insuffisant (55 bougies minimum)')
    # Exclude the most recent candle because it may still be forming.
    closed=rows[:-1]; last=closed[-1]; prices=[r['c'] for r in closed]
    e20=ema(prices,20); e50=ema(prices,50)
    bias='HAUSSIER' if e20>e50 and last['c']>e20 else 'BAISSIER' if e20<e50 and last['c']<e20 else 'NEUTRE'
    ts=datetime.datetime.strptime(last['t'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
    age=(datetime.datetime.now(datetime.timezone.utc)-ts).total_seconds()
    # Latest closed candle OPEN time should be within 2.5 interval lengths of now; tolerate API latency.
    fresh=(-seconds<=age<=max(seconds*2.5,POLL_SECONDS+seconds*1.5))
    return {'last_closed':last['t']+' UTC','close':round(last['c'],3),'bias':bias,'ema20':round(e20,3),'ema50':round(e50,3),'high20':round(max(x['h'] for x in closed[-20:]),3),'low20':round(min(x['l'] for x in closed[-20:]),3),'candles':len(closed),'fresh':fresh,'age_minutes':round(age/60,1),'_rows':closed}
def evaluate(frames):
    reasons=[]; out={'direction':'ATTENTE','readiness':'NON VALIDÉ','reasons':reasons,'fib_zone':None,'entry_reference':None,'stop_reference':None,'target_reference':None,'method':'Prototype EMA20/50 + swing20 + Fibonacci 50–61,8 % + confirmation M5; méthode vidéo NON certifiée'}
    if len(frames)!=4: reasons.append('Unités de temps manquantes');return out
    if not all(f['fresh'] for f in frames.values()):reasons.append('Données périmées ou horodatages incohérents');return out
    h4,h1,m15,m5=(frames[k] for k in ('H4','H1','M15','M5'))
    if h4['bias'] not in ('HAUSSIER','BAISSIER') or h1['bias']!=h4['bias']:
        reasons.append('H4 et H1 ne confirment pas la même direction');return out
    direction=h4['bias']; out['direction']='ACHAT POTENTIEL' if direction=='HAUSSIER' else 'VENTE POTENTIELLE'
    candles=m15['_rows'][-20:]; hi=max(x['h'] for x in candles);lo=min(x['l'] for x in candles);span=hi-lo
    if span<=0:reasons.append('Amplitude M15 insuffisante');return out
    zone=(hi-0.618*span,hi-0.5*span) if direction=='HAUSSIER' else (lo+0.5*span,lo+0.618*span)
    zone=tuple(sorted(zone));out['fib_zone']=[round(v,3) for v in zone]
    if not(zone[0]<=m15['close']<=zone[1]):reasons.append('Cours M15 hors zone Fibonacci expérimentale 50–61,8 %')
    if m5['bias']!=direction:reasons.append('Confirmation directionnelle M5 absente')
    last=m5['_rows'][-1]; candle_ok=last['c']>last['o'] if direction=='HAUSSIER' else last['c']<last['o']
    if not candle_ok:reasons.append('Dernière bougie clôturée M5 non confirmante')
    if reasons:return out
    out['readiness']='CONFIGURATION EXPÉRIMENTALE';out['entry_reference']=round(m5['close'],3)
    out['stop_reference']=round(lo,3) if direction=='HAUSSIER' else round(hi,3)
    risk=abs(out['entry_reference']-out['stop_reference'])
    if risk<=0 or (direction=='HAUSSIER' and out['stop_reference']>=out['entry_reference']) or (direction=='BAISSIER' and out['stop_reference']<=out['entry_reference']):
        out['readiness']='NON VALIDÉ';out['reasons'].append('Stop de référence incohérent');return out
    out['target_reference']=round(out['entry_reference']+(2*risk if direction=='HAUSSIER' else -2*risk),3)
    reasons.append('Configuration candidate seulement : règles de la formation et backtest encore à confirmer')
    return out
def worker():
    global state
    while True:
        if not API:
            with lock:state.update(status='CONFIGURATION',message='Clé serveur TWELVE_DATA_API_KEY manquante',signal='ATTENTE')
            time.sleep(60);continue
        frames={};errors=[]
        for key,(interval,seconds) in INTERVALS.items():
            try:frames[key]=analyze(fetch(interval),seconds)
            except Exception as e:errors.append(key+': '+str(e)[:120])
            time.sleep(9)
        analysis=evaluate(frames)
        public={k:{a:b for a,b in v.items() if a!='_rows'} for k,v in frames.items()}
        with lock:state={'status':'OK' if not errors and all(v['fresh'] for v in frames.values()) else 'PARTIEL / PÉRIMÉ','updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frames':public,'message':' | '.join(errors) if errors else 'Moteur expérimental actif — aucune recommandation de trading validée','signal':'ATTENTE','analysis':analysis}
        time.sleep(max(600,POLL_SECONDS))
@app.route('/')
def home():return send_from_directory('.','index.html')
@app.route('/api/status')
def status():
    with lock:return jsonify(dict(state))
if __name__=='__main__':
    threading.Thread(target=worker,daemon=True).start()
    app.run(host='0.0.0.0',port=int(os.getenv('PORT','8080')))
