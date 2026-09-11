#!/usr/bin/env python3
import argparse, json, time, urllib.request
from pathlib import Path

ALIASES={
'id':['id','playerId','Id'],'name':['name','nome','player','calciatore','Nome'],
'team':['team','squadra','club','Squadra'],'role':['role','ruolo','r','R'],
'quote':['quote','quotation','qa','quotazione','QA'],'fvm':['fvm','FVM','fvm1000'],
'appearances':['appearances','presenze','pg','pv','PG','PV'],'mv':['mv','mediaVoto','media_voto','MV'],
'fm':['fm','fantamedia','mf','MF','FM'],'goals':['goals','gol','goal','gf','GF'],
'assists':['assists','assist','ass','ASS']}
def pick(r,k,d=None):
 for a in ALIASES[k]:
  if r.get(a) not in (None,''): return r[a]
 return d
def num(v,d=0):
 try:
  if isinstance(v,(int,float)): return v
  x=float(str(v).replace('.','').replace(',','.')); return int(x) if x.is_integer() else round(x,2)
 except: return d
def role(v):
 r=str(v or '').strip().upper(); return {'POR':'P','PORTIERE':'P','DIF':'D','DIFENSORE':'D','CEN':'C','CENTROCAMPISTA':'C','ATT':'A','ATTACCANTE':'A'}.get(r,r[:1])
def strategy(r,q,f,mv,fm,pg):
 base=f if f>0 else q*{'P':2.4,'D':2.8,'C':4,'A':6}.get(r,3)
 perf=max(.75,min(1.35,1+(fm-6)*.08)) if fm else 1
 sug=max(1,round(base*perf)); mx=max(sug,round(sug*1.18)); st=min(98,max(20,round(45+min(38,pg*1.5)+max(0,mv-5.5)*12)))
 risk='Basso' if st>=85 else 'Medio' if st>=60 else 'Alto'
 tier='Top assoluto' if sug>=180 else 'Primo slot' if sug>=100 else 'Semitop' if sug>=55 else 'Titolare' if sug>=25 else 'Low cost'
 return sug,mx,st,risk,tier
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--url',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
 req=urllib.request.Request(a.url,headers={'User-Agent':'fantacalcio-live-copilot/1.0','Accept':'application/json','Cache-Control':'no-cache'})
 with urllib.request.urlopen(req,timeout=60) as res: raw=json.load(res)
 rows=raw.get('players',raw.get('data',raw)) if isinstance(raw,dict) else raw
 if not isinstance(rows,list): raise RuntimeError('Formato sorgente non riconosciuto')
 out=[]; now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
 for i,x in enumerate(rows,1):
  if not isinstance(x,dict): continue
  n=str(pick(x,'name','')).strip(); r=role(pick(x,'role',''))
  if not n or r not in {'P','D','C','A'}: continue
  q=num(pick(x,'quote',0)); f=num(pick(x,'fvm',0)); pg=num(pick(x,'appearances',0)); mv=num(pick(x,'mv',0)); fm=num(pick(x,'fm',0)); sug,mx,st,risk,tier=strategy(r,q,f,mv,fm,pg)
  out.append({'id':pick(x,'id',i),'name':n,'team':str(pick(x,'team','')).strip().upper(),'role':r,'quote':q,'fvm':f,'suggested':sug,'max':mx,'appearances':pg,'mv':mv,'fm':fm,'goals':num(pick(x,'goals',0)),'assists':num(pick(x,'assists',0)),'starter':st,'risk':risk,'tier':tier,'updatedAt':now,'dataSource':'live-external-feed'})
 if len(out)<400: raise RuntimeError(f'Dataset incompleto: {len(out)} giocatori')
 Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'sourceRecords':len(rows),'generatedPlayers':len(out)}))
if __name__=='__main__': main()
