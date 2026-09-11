#!/usr/bin/env python3
import argparse
import json
import math
import time
import urllib.request
from pathlib import Path

ALIASES = {
    "id": ["id", "playerId", "calciatore_id", "Id"],
    "name": ["name", "nome", "player", "calciatore", "Nome"],
    "team": ["team", "squadra", "club", "Squadra"],
    "role": ["role", "ruolo", "r", "R"],
    "quote": ["quote", "quotation", "qa", "quotazione", "Qt.A", "QA"],
    "fvm": ["fvm", "FVM", "fvm1000", "FVM/1000"],
    "appearances": ["appearances", "presenze", "pg", "pv", "Pg", "PV"],
    "mv": ["mv", "mediaVoto", "media_voto", "Mv", "MV"],
    "fm": ["fm", "fantamedia", "mf", "Mf", "FM"],
    "goals": ["goals", "gol", "goal", "gf", "Gf"],
    "assists": ["assists", "assist", "ass", "Ass"],
}

def pick(record, field, default=None):
    for key in ALIASES[field]:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return default

def number(value, default=0):
    if isinstance(value, (int, float)):
        return value
    try:
        value = str(value).strip().replace(".", "").replace(",", ".")
        result = float(value)
        return int(result) if result.is_integer() else round(result, 2)
    except (TypeError, ValueError):
        return default

def download_json(url):
    request = urllib.request.Request(url, headers={
        "User-Agent": "fantacalcio-live-copilot/1.0",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)

def normalize_role(value):
    role = str(value or "").strip().upper()
    mapping = {"POR": "P", "PORTIERE": "P", "DIF": "D", "DIFENSORE": "D", "CEN": "C", "CENTROCAMPISTA": "C", "ATT": "A", "ATTACCANTE": "A"}
    return mapping.get(role, role[:1])

def strategy(role, quote, fvm, mv, fm, appearances):
    base = fvm if fvm > 0 else quote * {"P": 2.4, "D": 2.8, "C": 4.0, "A": 6.0}.get(role, 3.0)
    performance = max(0.75, min(1.35, 1 + (fm - 6) * 0.08)) if fm else 1
    suggested = max(1, round(base * performance))
    maximum = max(suggested, round(suggested * 1.18))
    starter = min(98, max(20, round(45 + min(38, appearances * 1.5) + max(0, mv - 5.5) * 12)))
    risk = "Basso" if starter >= 85 else "Medio" if starter >= 60 else "Alto"
    if suggested >= 180: tier = "Top assoluto"
    elif suggested >= 100: tier = "Primo slot"
    elif suggested >= 55: tier = "Semitop"
    elif suggested >= 25: tier = "Titolare"
    else: tier = "Low cost"
    return suggested, maximum, starter, risk, tier

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    raw = download_json(args.url)
    records = raw.get("players", raw.get("data", raw)) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        raise RuntimeError("Formato sorgente non riconosciuto")

    generated = []
    for index, item in enumerate(records, 1):
        if not isinstance(item, dict):
            continue
        name = str(pick(item, "name", "")).strip()
        role = normalize_role(pick(item, "role", ""))
        if not name or role not in {"P", "D", "C", "A"}:
            continue
        quote = number(pick(item, "quote", 0))
        fvm = number(pick(item, "fvm", 0))
        appearances = number(pick(item, "appearances", 0))
        mv = number(pick(item, "mv", 0))
        fm = number(pick(item, "fm", 0))
        suggested, maximum, starter, risk, tier = strategy(role, quote, fvm, mv, fm, appearances)
        generated.append({
            "id": pick(item, "id", index), "name": name,
            "team": str(pick(item, "team", "")).strip().upper(), "role": role,
            "quote": quote, "fvm": fvm, "suggested": suggested, "max": maximum,
            "appearances": appearances, "mv": mv, "fm": fm,
            "goals": number(pick(item, "goals", 0)), "assists": number(pick(item, "assists", 0)),
            "starter": starter, "risk": risk, "tier": tier,
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "dataSource": "live-external-feed"
        })

    if len(generated) < 400:
        raise RuntimeError(f"Dataset incompleto: riconosciuti solo {len(generated)} giocatori")
    Path(args.output).write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sourceRecords": len(records), "generatedPlayers": len(generated)}, indent=2))

if __name__ == "__main__":
    main()
