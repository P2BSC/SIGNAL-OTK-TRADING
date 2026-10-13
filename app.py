"""SIGNAL OTK V2: read-only market monitor; no trade execution."""
import os,time,threading,datetime
from flask import Flask,jsonify,send_from_directory
import requests
app=Flask(__name__,static_folder='.')
API=os.getenv('TWELVE_DATA_API_KEY','')
INTERVALS={'M5':'5min','M15':'15min','H1':'1h','H4':'4h'}
state={'status':'INITIALISATION','updated':None,'frames':{},'message':'En attente de données','signal':'ATTENTE'}
lock=threading.Lock()
def fetch(interval):
    r=requests.get('https://api.twelvedata.com/time_series',params={'symbol':'XAU/USD','interval':interval,'outputsize':120,'apikey':API},timeout=20)
    r.raise_for_status(); j=r.json()
    if j.get('status')=='error' or not j.get('values'):raise ValueError(j.get('message','Réponse API vide'))
    rows=list(reversed(j['values']))
    return [{'t':x['datetime'],'o':float(x['open']),'h':float(x['high']),'l':float(x['low']),'c':float(x['close'])} for x in rows]
def analyze(rows):
    # Descriptive metrics only: NOT verified strategy signals.
    close=rows[-2]['c'] if len(rows)>1 else rows[-1]['c']
    previous=[x['c'] for x in rows[-22:-2]]
    mean=sum(previous)/len(previous) if previous else close
    return {'last_closed':rows[-2]['t'] if len(rows)>1 else rows[-1]['t'],'close':round(close,3),'bias':'HAUSSIER' if close>mean else 'BAISSIER' if close<mean else 'NEUTRE','high20':round(max(x['h'] for x in rows[-21:-1]),3),'low20':round(min(x['l'] for x in rows[-21:-1]),3),'candles':len(rows)}
def worker():
    global state
    while True:
        if not API:
            with lock:state.update(status='CONFIGURATION',message='Clé serveur TWELVE_DATA_API_KEY manquante',signal='ATTENTE')
            time.sleep(60);continue
        frames={};errors=[]
        for key,interval in INTERVALS.items():
            try:frames[key]=analyze(fetch(interval))
            except Exception as e:errors.append(key+': '+str(e)[:140])
            time.sleep(9) # Conservative pacing for free-tier API limits.
        with lock:
            state={'status':'OK' if not errors else 'PARTIEL','updated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frames':frames,'message':' | '.join(errors) if errors else 'Données disponibles; stratégie vidéo non codée intégralement','signal':'ATTENTE'}
        time.sleep(300)
@app.route('/')
def home():return send_from_directory('.','index.html')
@app.route('/api/status')
def status():
    with lock:return jsonify(dict(state))
if __name__=='__main__':
    threading.Thread(target=worker,daemon=True).start()
    app.runapp.run(host='0.0.0.0', port=int(os.getenv('PORT', '8080')))