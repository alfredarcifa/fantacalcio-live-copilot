#!/usr/bin/env python3
import argparse, io, json, re, unicodedata, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from openpyxl import load_workbook

def norm(v):
 s='' if v is None else str(v).strip();s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c));return re.sub(r'[^a-z0-9]+','',s.lower())
def flat(v):
 if isinstance(v,list) and all(isinstance(x,dict) for x in v):return v
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
  if v not in (None,''):return v.get('name') or v.get('code') or default if isinstance(v,dict) else v
 return default
def num(v,d=None):
 try:return float(str(v).replace(',','.')) if v not in(None,'') else d
 except:return d
def request(url,accept):
 return urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36','Accept':accept,'Referer':'https://www.fantacalcio.it/statistiche-serie-a','Cache-Control':'no-cache'})
def load_json(url):
 with urllib.request.urlopen(request(url,'application/json,text/plain,*/*'),timeout=45) as r:return json.loads(r.read().decode('utf-8-sig'))
def quotations(rows):
 out=[]
 for i,x in enumerate(rows):
  name=val(x,'name','playerName','nome','calciatore');role=val(x,'position','role','ruolo','r',default='')
  if not name:continue
  out.append({'id':val(x,'id','playerId',default=i+1),'name':str(name).strip(),'team':str(val(x,'team','teamName','squadra',default='')).strip(),'role':str(role).strip(),'quote':num(val(x,'qt_att','currentQuotation','quote'),0),'initialQuote':num(val(x,'qt_i','initialQuotation')),'quoteDifference':num(val(x,'diff')),'mantraQuote':num(val(x,'qt_att_m')),'mantraInitialQuote':num(val(x,'qt_i_m')),'mantraDifference':num(val(x,'diff_m')),'fvm':num(val(x,'fvm'),0),'mantraFvm':num(val(x,'fvm_m')),'image':val(x,'playerImage','image',default='')})
 return out
def stats_xlsx(url):
 with urllib.request.urlopen(request(url,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*'),timeout=60) as r:data=r.read()
 wb=load_workbook(io.BytesIO(data),data_only=True,read_only=True);ws=wb[wb.sheetnames[0]];rows=list(ws.iter_rows(values_only=True))
 header_i=None;mapping={}
 aliases={'name':['calciatore','nome'],'team':['sq','squadra'],'appearances':['pv','presenze'],'mv':['mv'],'fm':['fm','mf'],'goals':['gol'],'goalsConceded':['gs'],'penalties':['rig'],'penaltiesSaved':['rp'],'assists':['ass','assist'],'yellowCards':['amm'],'redCards':['esp']}
 for i,row in enumerate(rows[:30]):
  n=[norm(x) for x in row]
  if 'calciatore' in n and ('pv' in n or 'presenze' in n):header_i=i;mapping={k:next((j for j,c in enumerate(n) if c in [norm(a) for a in aa]),None) for k,aa in aliases.items()};break
 if header_i is None:raise RuntimeError('Header statistiche non riconosciuto')
 out=[]
 for row in rows[header_i+1:]:
  def cell(k):
   j=mapping.get(k);return row[j] if j is not None and j<len(row) else None
  name=cell('name')
  if not name:continue
  out.append({'name':str(name).strip(),'team':str(cell('team') or '').strip(),'appearances':num(cell('appearances'),0),'mv':num(cell('mv')),'fm':num(cell('fm')),'goals':num(cell('goals'),0),'goalsConceded':num(cell('goalsConceded'),0),'penalties':str(cell('penalties') or ''),'penaltiesSaved':num(cell('penaltiesSaved'),0),'assists':num(cell('assists'),0),'yellowCards':num(cell('yellowCards'),0),'redCards':num(cell('redCards'),0)})
 return out
def stats_json(url):
 data=flat(load_json(url));out=[]
 for x in data:
  name=val(x,'name','player','playerName','nome','calciatore')
  if not name:continue
  # Accept both current-season Fantacalcio-style fields and enriched public datasets.
  out.append({'name':str(name).strip(),'team':str(val(x,'team','teamName','squadra','sq',default='')).strip(),
   'appearances':num(val(x,'appearances','pv','presenze','apps','matches')),
   'mv':num(val(x,'mv','averageRating','mediaVoto','avg')),
   'fm':num(val(x,'fm','fantasyAverage','fantamedia','mf')),
   'goals':num(val(x,'goals','gol','goal'),0),'goalsConceded':num(val(x,'goalsConceded','gs'),0),
   'penalties':str(val(x,'penalties','rig',default='') or ''),'penaltiesSaved':num(val(x,'penaltiesSaved','rp'),0),
   'assists':num(val(x,'assists','assist','ass'),0),'yellowCards':num(val(x,'yellowCards','amm','yellow'),0),
   'redCards':num(val(x,'redCards','esp','red'),0)})
 return out
def main():
 a=argparse.ArgumentParser();a.add_argument('--urls',nargs='+',required=True);a.add_argument('--stats-url');a.add_argument('--stats-json-urls',nargs='*',default=[]);a.add_argument('--strategy',required=True);a.add_argument('--all-output',required=True);a.add_argument('--metadata-output',required=True);a.add_argument('--minimum',type=int,default=100);o=a.parse_args()
 errors=[];players=[];qsource=None
 for url in o.urls:
  try:
   candidate=quotations(flat(load_json(url)))
   if len(candidate)>=o.minimum:players=candidate;qsource=url;break
   errors.append(f'{url}: {len(candidate)} quote')
  except Exception as e:errors.append(f'{url}: {type(e).__name__}: {e}')
 if not players:print('::warning::Quotazioni non disponibili; fallback invariato. '+' | '.join(errors));return 0
 stats=[];stats_source=None
 if o.stats_url:
  try:stats=stats_xlsx(o.stats_url);stats_source=o.stats_url
  except Exception as e:errors.append(f'stats xlsx: {type(e).__name__}: {e}')
 if not stats:
  for url in o.stats_json_urls:
   try:
    candidate=stats_json(url)
    if len(candidate)>=o.minimum:stats=candidate;stats_source=url;break
    errors.append(f'{url}: only {len(candidate)} statistics records')
   except Exception as e:errors.append(f'{url}: {type(e).__name__}: {e}')
 by_exact={(norm(x['name']),norm(x['team'])):x for x in stats};by_name={}
 for x in stats:by_name.setdefault(norm(x['name']),[]).append(x)
 matched=0;ambiguous=[]
 for p in players:
  s=by_exact.get((norm(p['name']),norm(p['team'])))
  if not s:
   choices=by_name.get(norm(p['name']),[])
   if len(choices)==1:s=choices[0]
   elif len(choices)>1:ambiguous.append(p['name'])
  if s:p.update({k:v for k,v in s.items() if k not in ('name','team')});p['statisticsMatched']=True;matched+=1
  else:
   # Never destroy valid committed/strategy statistics when the remote statistics source is unavailable.
   for k in ('appearances','mv','fm','goals','goalsConceded','penalties','penaltiesSaved','assists','yellowCards','redCards'):
    p.setdefault(k,None)
   p['statisticsMatched']=False
 strategy=json.loads(Path(o.strategy).read_text(encoding='utf-8'));sm={norm(x['name']):x for x in strategy}
 for p in players:
  if norm(p['name']) in sm:
   # Strategy file is also the committed last-known-good fallback for the selected players.
   for k in ('suggested','max','starter','risk','tier','notes','appearances','mv','fm','goals','goalsConceded','penalties','penaltiesSaved','assists','yellowCards','redCards'):
    if k in sm[norm(p['name'])] and sm[norm(p['name'])][k] is not None:
     p[k]=sm[norm(p['name'])][k]
 Path(o.all_output).write_text(json.dumps(players,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 meta={'quotationSource':qsource,'statisticsSource':stats_source,'officialStatistics':True,'retrievedAt':datetime.now(timezone.utc).isoformat(),'totalPlayers':len(players),'statisticsRecords':len(stats),'statisticsMatched':matched,'statisticsUnmatched':len(players)-matched,'ambiguousMatches':ambiguous,'status':'REMOTE_OK_WITH_STATS' if matched else 'REMOTE_OK_STATS_UNAVAILABLE','errors':errors}
 Path(o.metadata_output).write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(meta,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
