#!/usr/bin/env python3
import argparse
import json
import re
import unicodedata
import urllib.request
from collections import defaultdict
from pathlib import Path

NAME_KEYS = ('name','nome','calciatore','playername','player_name','player','n')
TEAM_KEYS = ('team','squadra','sq','club','teamname','team_name','s')
ROLE_KEYS = ('role','ruolo','r')
QUOTE_KEYS = ('quote','qa','quotazioneattuale','quotazione','quotation')
FVM_KEYS = ('fvm','fvm1000','fantavalue')
MV_KEYS = ('mv','mediavoto','average_rating')
FM_KEYS = ('fm','mf','fantamedia','fantasy_average')
GOAL_KEYS = ('goals','gol','gf','goal')
ASSIST_KEYS = ('assists','assist','ass')


def norm(value):
    text = '' if value is None else str(value).strip()
    text = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '', text.lower())


def normalized(record):
    return {norm(k): v for k, v in record.items() if k is not None}


def pick(record, keys, default=None):
    for key in keys:
        value = record.get(norm(key))
        if value not in (None, ''):
            if isinstance(value, dict):
                return value.get('name') or value.get('code') or value.get('shortName') or default
            return value
    return default


def number(value, default=0):
    if value in (None, ''):
        return default
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else round(float(value), 2)
    text = str(value).strip().replace('%','')
    if ',' in text:
        text = text.replace('.', '').replace(',', '.')
    try:
        parsed = float(text)
        return int(parsed) if parsed.is_integer() else round(parsed, 2)
    except ValueError:
        return default


def flatten(payload):
    if isinstance(payload, list) and all(isinstance(x, dict) for x in payload):
        return payload
    if isinstance(payload, dict):
        for key in ('players','data','results','response','calciatori'):
            if key in payload:
                found = flatten(payload[key])
                if found:
                    return found
        for value in payload.values():
            found = flatten(value)
            if found:
                return found
    return []


def download_json(url):
    request = urllib.request.Request(url, headers={'User-Agent':'fantacalcio-live-copilot/1.0','Accept':'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    payload = json.loads(body.decode('utf-8-sig'))
    records = flatten(payload)
    if not records:
        raise RuntimeError('La sorgente remota non contiene un array di giocatori riconoscibile')
    return [normalized(record) for record in records]


def indexes(records):
    by_name = defaultdict(list)
    by_name_team = {}
    for record in records:
        name = pick(record, NAME_KEYS, '')
        team = pick(record, TEAM_KEYS, '')
        if not name:
            continue
        nk, tk = norm(name), norm(team)
        by_name[nk].append(record)
        if tk:
            by_name_team[(nk, tk)] = record
    return by_name, by_name_team


def find(player, by_name, by_name_team):
    nk, tk = norm(player.get('name')), norm(player.get('team'))
    if (nk, tk) in by_name_team:
        return by_name_team[(nk, tk)]
    candidates = by_name.get(nk, [])
    return candidates[0] if len(candidates) == 1 else None


def merge(strategy, source):
    result = dict(strategy)
    result.update({
        'role': str(pick(source, ROLE_KEYS, result.get('role',''))),
        'quote': number(pick(source, QUOTE_KEYS, result.get('quote',0)), result.get('quote',0)),
        'fvm': number(pick(source, FVM_KEYS, result.get('fvm',0)), result.get('fvm',0)),
        'mv': number(pick(source, MV_KEYS, result.get('mv',0)), result.get('mv',0)),
        'fm': number(pick(source, FM_KEYS, result.get('fm',0)), result.get('fm',0)),
        'goals': number(pick(source, GOAL_KEYS, result.get('goals',0)), result.get('goals',0)),
        'assists': number(pick(source, ASSIST_KEYS, result.get('assists',0)), result.get('assists',0)),
        'dataSource': 'fantaleghe-api-json (unofficial)',
        'updatedAutomatically': True,
    })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--strategy', help='Default: usa il file indicato da --output come strategia esistente')
    parser.add_argument('--minimum-match-rate', type=float, default=0.70)
    args = parser.parse_args()

    output = Path(args.output)
    strategy_path = Path(args.strategy) if args.strategy else output
    if not strategy_path.is_file():
        raise RuntimeError(f'File strategia non trovato: {strategy_path}')
    strategy = json.loads(strategy_path.read_text(encoding='utf-8-sig'))
    if not isinstance(strategy, list) or not strategy:
        raise RuntimeError('La strategia deve essere un array JSON non vuoto')

    remote = download_json(args.url)
    by_name, by_name_team = indexes(remote)
    generated, unmatched = [], []
    for player in strategy:
        source = find(player, by_name, by_name_team)
        if source is None:
            unmatched.append(f"{player.get('name')} ({player.get('team')})")
            generated.append(dict(player))
        else:
            generated.append(merge(player, source))

    matched = len(strategy) - len(unmatched)
    rate = matched / len(strategy)
    print(json.dumps({'remoteRecords':len(remote),'strategyPlayers':len(strategy),'matched':matched,'matchRate':round(rate,4),'unmatched':unmatched}, ensure_ascii=False, indent=2))
    if rate < args.minimum_match_rate:
        raise RuntimeError(f'Dataset incompleto: riconosciuti {matched}/{len(strategy)} giocatori ({rate:.0%}); output non modificato')

    temp = output.with_suffix(output.suffix + '.tmp')
    temp.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(output)
    print(f'Aggiornato {output} in modo atomico')

if __name__ == '__main__':
    main()
