#!/usr/bin/env python3
"""Merge Fantacalcio data into the local auction strategy.

Supports:
- official Fantacalcio XLSX files, when available;
- a JSON dataset supplied with --source-json;
- resilient matching by normalized player name, with team used as a preference;
- fail-safe output: the destination is written only after validation succeeds.
"""

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def normalize(value):
    text = "" if value is None else str(value).strip()
    text = "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def number(value, default=0):
    if value in (None, ""):
        return default
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else round(float(value), 2)
    text = str(value).strip().replace("%", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        parsed = float(text)
        return int(parsed) if parsed.is_integer() else round(parsed, 2)
    except ValueError:
        return default


def normalized_record(record):
    return {normalize(key): value for key, value in record.items() if key is not None}


def pick(record, aliases, default=None):
    for alias in aliases:
        key = normalize(alias)
        if key in record and record[key] not in (None, ""):
            return record[key]
    return default


def detect_header(rows):
    best = None
    for index, row in enumerate(rows[:40]):
        headers = [normalize(cell) for cell in row]
        score = 0
        for aliases in (
            ("nome", "calciatore", "player", "name"),
            ("squadra", "sq", "team"),
            ("ruolo", "r", "role"),
            ("qa", "quotazioneattuale", "quotation"),
            ("fvm", "fvm1000"),
            ("pv", "pg", "presenze", "appearances"),
            ("mv", "mediavoto"),
            ("fm", "mf", "fantamedia"),
        ):
            if any(normalize(alias) in headers for alias in aliases):
                score += 1
        if best is None or score > best[0]:
            best = (score, index, headers)
    if not best or best[0] < 2:
        raise RuntimeError("Impossibile riconoscere la riga di intestazione del file XLSX")
    return best[1], best[2]


def read_xlsx(path):
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("Dipendenza mancante: installare openpyxl==3.1.5") from exc

    workbook = load_workbook(path, read_only=True, data_only=True)
    candidates = []
    for worksheet in workbook.worksheets:
        rows = list(worksheet.iter_rows(values_only=True))
        if not rows:
            continue
        try:
            header_index, headers = detect_header(rows)
        except RuntimeError:
            continue
        records = []
        for row in rows[header_index + 1 :]:
            record = {}
            duplicate_count = Counter()
            for index, header in enumerate(headers):
                if not header or index >= len(row):
                    continue
                duplicate_count[header] += 1
                unique_header = header if duplicate_count[header] == 1 else f"{header}{duplicate_count[header]}"
                record[unique_header] = row[index]
            if any(value not in (None, "") for value in record.values()):
                records.append(record)
        score = len(records)
        candidates.append((score, worksheet.title, records))

    if not candidates:
        raise RuntimeError(f"Nessun foglio dati riconosciuto in {path}")
    _, sheet_name, records = max(candidates, key=lambda item: item[0])
    print(f"XLSX {path}: foglio '{sheet_name}', {len(records)} righe", file=sys.stderr)
    return records


def flatten_json(value):
    if isinstance(value, list):
        if all(isinstance(item, dict) for item in value):
            return value
        for item in value:
            result = flatten_json(item)
            if result:
                return result
    if isinstance(value, dict):
        preferred = ("players", "data", "results", "response", "calciatori")
        for key in preferred:
            if key in value:
                result = flatten_json(value[key])
                if result:
                    return result
        for child in value.values():
            result = flatten_json(child)
            if result:
                return result
    return []


def read_json(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    records = [normalized_record(item) for item in flatten_json(payload)]
    if not records:
        raise RuntimeError(f"Nessun record giocatore trovato in {path}")
    print(f"JSON {path}: {len(records)} record", file=sys.stderr)
    return records


def player_name(record):
    return pick(record, ["name", "nome", "calciatore", "playerName", "player", "player_name"], "")


def player_team(record):
    team = pick(record, ["team", "squadra", "sq", "club", "teamName", "team_name"], "")
    if isinstance(team, dict):
        team = team.get("name") or team.get("code") or ""
    return team


def build_indexes(records):
    by_name = defaultdict(list)
    by_name_team = {}
    for raw in records:
        record = normalized_record(raw)
        name = player_name(record)
        team = player_team(record)
        if not name:
            continue
        name_key = normalize(name)
        team_key = normalize(team)
        by_name[name_key].append(record)
        if team_key:
            by_name_team[(name_key, team_key)] = record
    return by_name, by_name_team


def find_record(player, indexes):
    by_name, by_name_team = indexes
    name_key = normalize(player.get("name"))
    team_key = normalize(player.get("team"))
    exact = by_name_team.get((name_key, team_key))
    if exact:
        return exact
    candidates = by_name.get(name_key, [])
    if len(candidates) == 1:
        return candidates[0]
    return None


def merge_player(strategy_player, price_record, stats_record):
    price_record = price_record or {}
    stats_record = stats_record or {}
    merged = dict(strategy_player)

    merged.update(
        {
            "role": str(pick(price_record, ["r", "ruolo", "role"], merged.get("role", ""))).strip(),
            "quote": number(
                pick(price_record, ["qa", "qa2", "quotazioneattuale", "quotation", "quote"], merged.get("quote", 0)),
                merged.get("quote", 0),
            ),
            "fvm": number(
                pick(price_record, ["fvm1000", "fvm", "fvm10002", "fantaValue"], merged.get("fvm", 0)),
                merged.get("fvm", 0),
            ),
            "appearances": number(
                pick(stats_record, ["pv", "pg", "presenze", "appearances"], merged.get("appearances", 0)),
                merged.get("appearances", 0),
            ),
            "mv": number(
                pick(stats_record, ["mv", "mediavoto", "averageRating"], merged.get("mv", 0)),
                merged.get("mv", 0),
            ),
            "fm": number(
                pick(stats_record, ["fm", "mf", "fantamedia", "fantasyAverage"], merged.get("fm", 0)),
                merged.get("fm", 0),
            ),
            "goals": number(
                pick(stats_record, ["gol", "gf", "goals", "goal"], merged.get("goals", 0)),
                merged.get("goals", 0),
            ),
            "assists": number(
                pick(stats_record, ["ass", "assist", "assists"], merged.get("assists", 0)),
                merged.get("assists", 0),
            ),
            "yellowCards": number(
                pick(stats_record, ["amm", "ammonizioni", "yellowCards"], merged.get("yellowCards", 0)),
                merged.get("yellowCards", 0),
            ),
            "redCards": number(
                pick(stats_record, ["esp", "espulsioni", "redCards"], merged.get("redCards", 0)),
                merged.get("redCards", 0),
            ),
            "updatedAutomatically": True,
        }
    )
    return merged


def validate_strategy(strategy):
    if not isinstance(strategy, list) or not strategy:
        raise RuntimeError("Il file strategy deve contenere un array JSON non vuoto")
    required = {"id", "name", "team", "role", "suggested", "max"}
    for index, player in enumerate(strategy, start=1):
        missing = required.difference(player)
        if missing:
            raise RuntimeError(f"Strategy player #{index}: campi mancanti {sorted(missing)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prices")
    parser.add_argument("--stats")
    parser.add_argument("--source-json")
    parser.add_argument("--minimum-match-rate", type=float, default=0.70)
    args = parser.parse_args()

    strategy = json.loads(Path(args.strategy).read_text(encoding="utf-8-sig"))
    validate_strategy(strategy)

    if args.source_json:
        source_records = read_json(args.source_json)
        price_records = source_records
        stats_records = source_records
        source_name = "JSON esterno"
    else:
        if not args.prices or not args.stats:
            parser.error("usare --source-json oppure entrambi --prices e --stats")
        price_records = read_xlsx(args.prices)
        stats_records = read_xlsx(args.stats)
        source_name = "Fantacalcio XLSX"

    price_indexes = build_indexes(price_records)
    stats_indexes = build_indexes(stats_records)

    generated = []
    unmatched = []
    for player in strategy:
        price_record = find_record(player, price_indexes)
        stats_record = find_record(player, stats_indexes)
        if price_record is None and stats_record is None:
            unmatched.append(f"{player.get('name')} ({player.get('team')})")
            continue
        generated.append(merge_player(player, price_record, stats_record))

    total = len(strategy)
    matched = len(generated)
    match_rate = matched / total if total else 0
    report = {
        "source": source_name,
        "strategyPlayers": total,
        "matched": matched,
        "matchRate": round(match_rate, 4),
        "unmatched": unmatched,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if match_rate < args.minimum_match_rate:
        raise RuntimeError(
            f"Dataset incompleto: riconosciuti {matched}/{total} giocatori "
            f"({match_rate:.0%}), soglia {args.minimum_match_rate:.0%}. "
            f"Non è stato sovrascritto alcun output."
        )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(f"Scritto {output} con {matched} giocatori")


if __name__ == "__main__":
    main()
