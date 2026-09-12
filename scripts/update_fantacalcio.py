#!/usr/bin/env python3
import argparse,io,json,re,unicodedata,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from openpyxl import load_workbook

def norm(v):
 s='' if v is None else str(v).strip();s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c));return re.sub(r'[^a-z0-9]+','',s.lower())
def num(v,d=None):
 try:return float(str(v).replace(',','.')) if v not in(None,'','-','—') else d
 except:return d
def request(url,accept):return urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 Chrome/124 Safari/537.36','Accept':accept,'Referer':'https://www.fantacalcio.it/statistiche-serie-a'})
def load_json(url):
 with urllib.request.urlopen(request(url,'application/json,text/plain,*/*'),timeout=60) as r:return json.loads(r.read().decode('utf-8-sig'))
def walk(obj,path=()):
 if isinstance(obj,dict):
  yield path,obj
  for k,v in obj.items():yield from walk(v,path+(str(k),))
 elif isinstance(obj,list):
  for i,v in enumerate(obj):yield from walk(v,path+(str(i),))
def first(d,*keys):
 wanted={norm(k) for k in keys}
 for k,v in d.items():
  if norm(k) in wanted and v not in(None,'',[],{}):return v
 return None
def flatten_players(payload):
 candidates=[]
 for path,d in walk(payload):
  name=first(d,'name','playerName','nome','calciatore','nomeCompleto')
  role=first(d,'position','role','ruolo','r')
  if name and (role is not None or first(d,'qt_att','fvm','quote') is not None):candidates.append(d)
 return candidates
def quotation_rows(payload):
 out=[]
 for i,x in enumerate(flatten_players(payload)):
  name=first(x,'name','playerName','nome','calciatore');
  if not name:continue
  out.append({'id':first(x,'id','playerId','player_id') or i+1,'name':str(name).strip(),'team':str(first(x,'team','teamName','squadra','sq') or '').strip(),'role':str(first(x,'position','role','ruolo','r') or '').strip(),'quote':num(first(x,'qt_att','currentQuotation','quote'),0),'initialQuote':num(first(x,'qt_i','initialQuotation')),'quoteDifference':num(first(x,'diff')),'mantraQuote':num(first(x,'qt_att_m')),'mantraInitialQuote':num(first(x,'qt_i_m')),'mantraDifference':num(first(x,'diff_m')),'fvm':num(first(x,'fvm'),0),'mantraFvm':num(first(x,'fvm_m')),'image':first(x,'playerImage','image') or ''})
 return out
STAT_KEYS=('appearances','pv','presenze','apps','matches','partiteVoto','pg','mv','mediaVoto','averageRating','fm','fantamedia','fantasyAverage','goals','gol','assists','assist','amm','ammonizioni')
def stat_record(name,team,d):
 return {'name':str(name).strip(),'team':str(team or '').strip(),'appearances':num(first(d,'appearances','pv','presenze','apps','matches','partiteVoto','pg')),'mv':num(first(d,'mv','averageRating','mediaVoto','avg','media')),'fm':num(first(d,'fm','fantasyAverage','fantamedia','mf','mediaFantavoto')),'goals':num(first(d,'goals','gol','goal','reti'),0),'goalsConceded':num(first(d,'goalsConceded','gs','golSubiti'),0),'penalties':str(first(d,'penalties','rig','rigori') or ''),'penaltiesSaved':num(first(d,'penaltiesSaved','rp','rigoriParati'),0),'assists':num(first(d,'assists','assist','ass'),0),'yellowCards':num(first(d,'yellowCards','amm','yellow','ammonizioni'),0),'redCards':num(first(d,'redCards','esp','red','espulsioni'),0)}
def stats_json(url):
 payload=load_json(url);out=[];seen=set()
 for path,d in walk(payload):
  if not any(norm(k) in {norm(x) for x in STAT_KEYS} for k in d):continue
  name=first(d,'name','player','playerName','nome','calciatore','nomeCompleto')
  if not name and path:
   candidate=path[-1]
   if not candidate.isdigit() and len(candidate)>2:name=candidate
  if not name:continue
  season=' '.join(str(first(d,k) or '') for k in ('season','stagione','year','anno'))
  if season and not any(x in season for x in ('2026','26/27','2026/27','2627')):continue
  r=stat_record(name,first(d,'team','teamName','squadra','sq','club'),d);k=(norm(r['name']),norm(r['team']))
  score=sum(r[x] is not None for x in ('appearances','mv','fm'))
  if k not in seen and score:out.append(r);seen.add(k)
 return out
def stats_xlsx(url):
 with urllib.request.urlopen(request(url,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*'),timeout=60) as r:data=r.read()
 ws=load_workbook(io.BytesIO(data),data_only=True,read_only=True).active;rows=list(ws.iter_rows(values_only=True));hi=None
 for i,row in enumerate(rows[:30]):
  n=[norm(x) for x in row]
  if 'calciatore' in n and 'pv' in n:hi=i;headers=n;break
 if hi is None:raise RuntimeError('header statistiche non trovato')
 def idx(*names):return next((i for i,x in enumerate(headers) if x in {norm(n) for n in names}),None)
 ids={k:idx(*v) for k,v in {'name':['calciatore'],'team':['sq','squadra'],'appearances':['pv'],'mv':['mv'],'fm':['fm'],'goals':['gol'],'goalsConceded':['gs'],'penalties':['rig'],'penaltiesSaved':['rp'],'assists':['ass'],'yellowCards':['amm'],'redCards':['esp']}.items()}
 out=[]
 for row in rows[hi+1:]:
  get=lambda k:row[ids[k]] if ids[k] is not None and ids[k]<len(row) else None
  if get('name'):out.append({'name':str(get('name')).strip(),'team':str(get('team') or '').strip(),**{k:(str(get(k) or '') if k=='penalties' else num(get(k),0 if k not in ('mv','fm','appearances') else None)) for k in ids if k not in ('name','team')}})
 return out
def canon_team(v):
 n=norm(v);aliases={'atalanta':'ata','inter':'int','juventus':'juv','napoli':'nap','roma':'rom','lazio':'laz','milan':'mil','como':'com','frosinone':'fro','cagliari':'cag','sassuolo':'sas','udinese':'udi','torino':'tor','lecce':'lec','fiorentina':'fio','bologna':'bol','parma':'par','monza':'mon','genoa':'gen','venezia':'ven'};return aliases.get(n,n[:3])
def name_tokens(v):return [x for x in re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',str(v)).encode('ascii','ignore').decode().lower()).split() if len(x)>1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--urls',nargs='+',required=True);ap.add_argument('--stats-url');ap.add_argument('--stats-json-urls',nargs='*',default=[]);ap.add_argument('--strategy',required=True);ap.add_argument('--all-output',required=True);ap.add_argument('--metadata-output',required=True);ap.add_argument('--minimum',type=int,default=100);a=ap.parse_args();errors=[];players=[];qsource=None
 for u in a.urls:
  try:
   c=quotation_rows(load_json(u))
   if len(c)>=a.minimum:players=c;qsource=u;break
   errors.append(f'{u}: {len(c)} quote')
  except Exception as e:errors.append(f'{u}: {type(e).__name__}: {e}')
 if not players:print('::warning::quotazioni assenti, fallback invariato');return 0
 sources=[]
 if a.stats_url:
  try:sources.append((a.stats_url,stats_xlsx(a.stats_url)))
  except Exception as e:errors.append(f'xlsx: {type(e).__name__}: {e}')
 for u in a.stats_json_urls:
  try:
   c=stats_json(u)
   if c:sources.append((u,c))
  except Exception as e:errors.append(f'{u}: {type(e).__name__}: {e}')
 stats=[];source_names=[]
 for u,rows in sources:
  source_names.append(u);stats.extend(rows)
 exact={};byname={}
 for s in stats:
  exact.setdefault((norm(s['name']),canon_team(s['team'])),s);byname.setdefault(norm(s['name']),[]).append(s)
 strategy=json.loads(Path(a.strategy).read_text(encoding='utf-8'));sm={norm(x['name']):x for x in strategy};matched=0;methods={}
 for p in players:
  s=exact.get((norm(p['name']),canon_team(p['team'])));method='exact'
  if not s:
   choices=byname.get(norm(p['name']),[])
   if len(choices)==1:s=choices[0];method='name'
  if not s:
   pt=name_tokens(p['name']);candidates=[]
   for x in stats:
    xt=name_tokens(x['name'])
    if canon_team(x['team'])==canon_team(p['team']) and pt and xt and (pt[0]==xt[0] or pt[-1]==xt[-1]):candidates.append(x)
   if len(candidates)==1:s=candidates[0];method='token-team'
  if s:p.update({k:v for k,v in s.items() if k not in ('name','team')});matched+=1;methods[method]=methods.get(method,0)+1
  fallback=sm.get(norm(p['name']),{})
  for k in ('suggested','max','starter','risk','tier','notes','appearances','mv','fm','goals','goalsConceded','penalties','penaltiesSaved','assists','yellowCards','redCards'):
   if (p.get(k) is None or k in ('suggested','max','starter','risk','tier','notes')) and fallback.get(k) is not None:p[k]=fallback[k]
  for k in ('appearances','mv','fm','goals','goalsConceded','penalties','penaltiesSaved','assists','yellowCards','redCards'):p.setdefault(k,None)
  p['statisticsMatched']=bool(s)
 Path(a.all_output).write_text(json.dumps(players,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 meta={'quotationSource':qsource,'statisticsSources':source_names,'retrievedAt':datetime.now(timezone.utc).isoformat(),'totalPlayers':len(players),'statisticsRecords':len(stats),'statisticsMatched':matched,'statisticsUnmatched':len(players)-matched,'matchMethods':methods,'status':'REMOTE_OK_WITH_STATS' if matched else 'REMOTE_OK_STATS_UNAVAILABLE','errors':errors}
 Path(a.metadata_output).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(meta,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
