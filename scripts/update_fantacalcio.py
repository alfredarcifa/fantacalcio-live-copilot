#!/usr/bin/env python3
import argparse, json, re, unicodedata
from pathlib import Path
from openpyxl import load_workbook

def norm(v):
    s = '' if v is None else str(v).strip()
    s = ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9+]+', '', s.lower())

def num(v, default=0):
    if v is None or v == '': return default
    if isinstance(v, (int, float)): return v
    s = str(v).strip().replace('.', '').replace(',', '.')
    try:
        x = float(s)
        return int(x) if x.is_integer() else round(x, 2)
    except ValueError:
        return default

def sheet_rows(path):
    wb = load_workbook(path, read_only=True, data_only=True)
    candidates = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        for i, row in enumerate(rows[:20]):
            headers = [norm(x) for x in row]
            score = sum(h in headers for h in ('nome','squadra','r')) + sum(h in headers for h in ('qa','fvm','pg','mv','mf','ass'))
            candidates.append((score, rows, i, ws.title))
    score, rows, idx, title = max(candidates, key=lambda x: x[0])
    if score < 2:
        raise RuntimeError(f'Intestazioni non riconosciute in {path}; foglio migliore: {title}')
    headers = [norm(x) for x in rows[idx]]
    out=[]
    for row in rows[idx+1:]:
        rec={headers[i]: row[i] for i in range(min(len(headers),len(row))) if headers[i]}
        if any(v not in (None,'') for v in rec.values()): out.append(rec)
    return out

def pick(rec, aliases, default=None):
    for a in aliases:
        k=norm(a)
        if k in rec and rec[k] not in (None,''): return rec[k]
    return default

def key(name, team=''):
    return norm(name) + '|' + norm(team)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--prices', required=True); ap.add_argument('--stats', required=True)
    ap.add_argument('--strategy', required=True); ap.add_argument('--output', required=True)
    args=ap.parse_args()
    strategy=json.loads(Path(args.strategy).read_text(encoding='utf-8'))
    price_rows=sheet_rows(args.prices); stat_rows=sheet_rows(args.stats)
    prices={}; stats={}
    for r in price_rows:
        name=pick(r,['Nome','Calciatore']); team=pick(r,['Squadra','Sq'],'')
        if name: prices[key(name,team)]=r
    for r in stat_rows:
        name=pick(r,['Nome','Calciatore']); team=pick(r,['Squadra','Sq'],'')
        if name: stats[key(name,team)]=r
    found=0; missing=[]; generated=[]
    for p in strategy:
        k=key(p.get('name'),p.get('team')); pr=prices.get(k); st=stats.get(k)
        if pr or st: found += 1
        else: missing.append(f"{p.get('name')} ({p.get('team')})")
        q=num(pick(pr or {},['Qt.A','QA','Quotazione Attuale','Quotazione'],p.get('quote',0)),p.get('quote',0))
        generated.append({**p,
          'role': str(pick(pr or {},['R','Ruolo'],p.get('role',''))).strip() or p.get('role',''),
          'quote': q,
          'fvm': num(pick(pr or {},['FVM','FVM/1000'],p.get('fvm',0)),p.get('fvm',0)),
          'appearances': num(pick(st or {},['Pg','PV','Presenze'],p.get('appearances',0))),
          'mv': num(pick(st or {},['Mv','MV','Media Voto'],p.get('mv',0)),p.get('mv',0)),
          'fm': num(pick(st or {},['Mf','FM','Fantamedia'],p.get('fm',0)),p.get('fm',0)),
          'goals': num(pick(st or {},['Gf','Gol','Goal'],p.get('goals',0)),p.get('goals',0)),
          'assists': num(pick(st or {},['Ass','Assist'],p.get('assists',0)),p.get('assists',0)),
          'yellowCards': num(pick(st or {},['Amm','Ammonizioni'],p.get('yellowCards',0))),
          'redCards': num(pick(st or {},['Esp','Espulsioni'],p.get('redCards',0))),
          'dataSource':'Fantacalcio.it','updatedAutomatically':True})
    if found == 0: raise RuntimeError('Nessun giocatore riconciliato: blocco di sicurezza attivato')
    Path(args.output).write_text(json.dumps(generated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'strategyPlayers':len(strategy),'matched':found,'missing':missing},ensure_ascii=False,indent=2))
    if found < max(1, int(len(strategy)*0.7)):
        raise RuntimeError('Meno del 70% dei giocatori riconciliato: dataset non pubblicato')
if __name__=='__main__': main()
