#!/usr/bin/env python3
import argparse,json,re,unicodedata,urllib.request
from datetime import datetime,timezone
from pathlib import Path

def norm(v):
 s='' if v is None else str(v).strip();s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c));return re.sub(r'[^a-z0-9]+','',s.lower())
def flat(v):
 if isinstance(v,list) and all(isinstance(x,dict) for x in v): return v
 if isinstance(v,dict):
  for k in ('players','data','results','response','calciatori'):
   if k in v:
    r=flat(v[k])
    if r:return r
  for x in v.values():
   r=flat(x)
   if r:return r
 return []
def val(d,*keys,default=None):
 nd={norm(k):v for k,v in d.items()}
 for k in keys:
  v=nd.get(norm(k))
  if v not in (None,''):
   if isinstance(v,dict):return v.get('name') or v.get('code') or default
   return v
 return default
def num(v,d=0):
 try:return float(str(v).replace(',','.')) if v not in(None,'') else d
 except:return d
def load_url(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode('utf-8-sig'))
def normalize(rows):
 out=[]
 for i,x in enumerate(rows):
  name=val(x,'name','playerName','nome','calciatore');team=val(x,'team','teamName','squadra','sq','club','teamShortName',default='')
  role=val(x,'position','role','ruolo','r',default='')
  if not name:continue
  q=num(val(x,'currentQuotation','quotation','quote','qa','quotazioneAttuale'),0);fvm=num(val(x,'fvm','fvm1000','fantaValue'),0)
  out.append({'id':val(x,'id','playerId','player_id',default=i+1),'name':str(name),'team':str(team),'role':str(role),'quote':q,'fvm':fvm,'mv':num(val(x,'mv','mediaVoto'),0),'fm':num(val(x,'fm','mf','fantamedia'),0),'goals':num(val(x,'goals','gol'),0),'assists':num(val(x,'assists','assist','ass'),0),'image':val(x,'playerImage','image','photo',default='')})
 # deduplicate
 seen=set();clean=[]
 for p in out:
  k=(norm(p['name']),norm(p['team']))
  if k not in seen:seen.add(k);clean.append(p)
 return clean
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--urls',nargs='+',required=True);ap.add_argument('--strategy',required=True);ap.add_argument('--all-output',required=True);ap.add_argument('--metadata-output',required=True);ap.add_argument('--minimum',type=int,default=100);a=ap.parse_args()
 strategy=json.loads(Path(a.strategy).read_text(encoding='utf-8'))
 source=None;players=[];errors=[]
 for url in a.urls:
  try:
   candidate=normalize(flat(load_url(url)))
   if len(candidate)>=a.minimum:source=url;players=candidate;break
   errors.append(f'{url}: only {len(candidate)} normalized records')
  except Exception as e:errors.append(f'{url}: {type(e).__name__}: {e}')
 if not players:
  print('::warning::Remote dataset unavailable or invalid. Keeping committed fallback. '+ ' | '.join(errors));return 0
 byname={norm(p['name']):p for p in players};matched=0
 for s in strategy:
  p=byname.get(norm(s['name']))
  if p:
   matched+=1
   for k in ('suggested','max','starter','risk','tier','notes'): 
    if k in s:p[k]=s[k]
   p['inStrategy']=True
 Path(a.all_output).write_text(json.dumps(players,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 meta={'source':source,'official':False,'retrievedAt':datetime.now(timezone.utc).isoformat(),'totalPlayers':len(players),'strategyMatched':matched,'strategyTotal':len(strategy),'status':'REMOTE_OK','errors':errors}
 Path(a.metadata_output).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(meta,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
