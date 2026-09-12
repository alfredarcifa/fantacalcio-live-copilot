import { useEffect, useMemo, useState } from "react";
import allPlayers from "./data/all-players.generated.json";
import strategy from "./data/player-strategy.json";
import metadata from "./data/data-metadata.json";
import "./style.css";

const BUDGET = 1000;
const TARGET = { P: 3, D: 8, C: 8, A: 6 };
const ROLE_ORDER = ["P", "D", "C", "A"];
const normalize = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");
const playerKey = player => `${normalize(player?.name)}|${normalize(player?.team)}`;
const load = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
const displayValue = value => value === null || value === undefined || value === "" ? "N/D" : value;
const hasValue = value => value !== null && value !== undefined && value !== "";
const defaultManagers = [
  { id: "me", name: "La mia squadra", mine: true },
  ...Array.from({ length: 7 }, (_, index) => ({ id: `rival-${index + 1}`, name: `Avversario ${index + 1}`, mine: false })),
];

function enrichStrategyPlayer(item, fullPlayers) {
  const exact = fullPlayers.find(player => playerKey(player) === playerKey(item));
  const sameName = fullPlayers.filter(player => normalize(player.name) === normalize(item.name));
  const source = exact || (sameName.length === 1 ? sameName[0] : null);
  return { ...(source || {}), ...item, inStrategy: true };
}

export default function App() {
  const appVersion = import.meta.env.VITE_APP_VERSION || 'local';
  const deployedAt = import.meta.env.VITE_DEPLOYED_AT || 'sviluppo locale';
  const [tab, setTab] = useState("all");
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("ALL");
  const [team, setTeam] = useState("ALL");
  const [sort, setSort] = useState("fvm");
  const [selected, setSelected] = useState(allPlayers[0] || strategy[0]);
  const [bid, setBid] = useState(1);
  const [buyerId, setBuyerId] = useState("me");
  const [managers, setManagers] = useState(() => load("fc-managers-v2", defaultManagers));
  const [purchases, setPurchases] = useState(() => load("fc-purchases-v2", []));

  useEffect(() => localStorage.setItem("fc-managers-v2", JSON.stringify(managers)), [managers]);
  useEffect(() => localStorage.setItem("fc-purchases-v2", JSON.stringify(purchases)), [purchases]);

  const strategyPlayers = useMemo(() => strategy.map(item => enrichStrategyPlayer(item, allPlayers)), []);
  const strategyKeys = useMemo(() => new Set(strategyPlayers.map(playerKey)), [strategyPlayers]);
  const players = useMemo(() => allPlayers.map(player => ({ ...player, inStrategy: strategyKeys.has(playerKey(player)) })), [strategyKeys]);
  const teams = useMemo(() => [...new Set(players.map(player => player.team).filter(Boolean))].sort(), [players]);
  const purchasedKeys = useMemo(() => new Set(purchases.map(item => item.playerKey)), [purchases]);

  const managerStats = useMemo(() => managers.map(manager => {
    const roster = purchases.filter(item => item.managerId === manager.id);
    const counts = roster.reduce((acc, item) => ({ ...acc, [item.role]: (acc[item.role] || 0) + 1 }), {});
    const spent = roster.reduce((sum, item) => sum + Number(item.paid || 0), 0);
    const slotsLeft = ROLE_ORDER.reduce((sum, currentRole) => sum + Math.max(0, TARGET[currentRole] - (counts[currentRole] || 0)), 0);
    const remaining = BUDGET - spent;
    const maxAffordable = Math.max(0, remaining - Math.max(0, slotsLeft - 1));
    return { ...manager, roster, counts, spent, remaining, slotsLeft, maxAffordable };
  }), [managers, purchases]);

  const selectedManager = managerStats.find(manager => manager.id === buyerId) || managerStats[0];
  const selectedStrategy = strategyPlayers.find(player => normalize(player.name) === normalize(selected?.name));
  const selectedAlreadyPurchased = purchases.find(item => item.playerKey === playerKey(selected));
  const selectedRoleFull = selectedManager && (selectedManager.counts[selected?.role] || 0) >= (TARGET[selected?.role] || 99);
  const canBuy = selected && !selectedAlreadyPurchased && !selectedRoleFull && bid >= 1 && bid <= (selectedManager?.maxAffordable || 0);
  const strategicMax = selectedStrategy?.max || selected?.fvm || selected?.quote || 1;
  const effectiveMax = Math.min(strategicMax, selectedManager?.maxAffordable || 0);

  const filteredPlayers = useMemo(() => players
    .filter(player => (role === "ALL" || player.role === role) && (team === "ALL" || player.team === team) && `${player.name} ${player.team}`.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => Number(b[sort] || 0) - Number(a[sort] || 0)), [players, query, role, team, sort]);

  function selectPlayer(player) {
    setSelected(player);
    const strategic = strategyPlayers.find(item => normalize(item.name) === normalize(player.name));
    setBid(Number(strategic?.suggested || player.quote || 1));
  }

  function registerPurchase() {
    if (!canBuy) return;
    setPurchases(current => [...current, {
      id: crypto.randomUUID(), managerId: buyerId, playerKey: playerKey(selected),
      playerId: selected.id, name: selected.name, team: selected.team, role: selected.role,
      paid: Number(bid), createdAt: new Date().toISOString(),
    }]);
  }

  function removePurchase(id) { setPurchases(current => current.filter(item => item.id !== id)); }
  function renameManager(id, name) { setManagers(current => current.map(manager => manager.id === id ? { ...manager, name } : manager)); }
  function resetAuction() { if (window.confirm("Azzerare acquisti e nomi dei fantallenatori?")) { setPurchases([]); setManagers(defaultManagers); } }

  const topLists = ["quote", "quoteDifference", "fvm", "mantraFvm"].map(metric => ({ metric, items: players.filter(player => hasValue(player[metric])).sort((a, b) => Number(b[metric]) - Number(a[metric])).slice(0, 10) }));

  return <div className="app-shell">
    <aside className="side-nav"><div className="side-brand">FC</div>{[["all","▦","Listone"],["mine","★","Lista 25"],["managers","◎","Fanta"],["stats","↗","Stats"]].map(([id,icon,label]) => <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)} title={label}><b>{icon}</b><small>{label}</small></button>)}<button className="side-reset" onClick={resetAuction} title="Reset asta"><b>↻</b><small>Reset</small></button></aside>
    <div className="app"><header className="topbar"><div><small>AI AUCTION ROOM</small><h1>Fantacalcio Live Copilot</h1><p>Listone completo, lista 25 e controllo live di tutti gli 8 fantallenatori.</p></div><span className="league">Classic · 8 squadre · 1000 crediti · Mod. difesa e capitano</span><div className="build-badge">Build {appVersion} · {deployedAt}</div></header>
    <div className="notice">Fonte tecnica: {metadata.source} · stato {metadata.status} · listone {metadata.totalPlayers} giocatori · shortlist {strategyPlayers.length}/25</div>

    {tab === "managers" ? <section className="manager-grid">{managerStats.map(manager => <article className={`card manager-card ${manager.mine ? "mine" : ""}`} key={manager.id}>
      <input className="manager-name" value={manager.name} onChange={event => renameManager(manager.id, event.target.value)} />
      <div className="manager-numbers"><span>Residuo <b>{manager.remaining}</b></span><span>Spesi <b>{manager.spent}</b></span><span>Max rilancio <b>{manager.maxAffordable}</b></span></div>
      <div className="roles">{ROLE_ORDER.map(currentRole => <span key={currentRole}><b>{manager.counts[currentRole] || 0}/{TARGET[currentRole]}</b>{currentRole}</span>)}</div>
      <div className="roster-list">{manager.roster.length === 0 ? <p>Nessun acquisto</p> : manager.roster.map(item => <div className="row" key={item.id}><span>{item.name} <em>{item.role}</em> <b>{item.paid}</b></span><button onClick={() => removePurchase(item.id)}>×</button></div>)}</div>
    </article>)}</section> : tab === "stats" ? <section className="card leaders"><h2>Classifiche al volo</h2>{topLists.map(list => <div key={list.metric}><h3>{list.metric.toUpperCase()}</h3>{list.items.map((player,index) => <button key={playerKey(player)} onClick={() => { selectPlayer(player); setTab("all"); }}>{index + 1}. {player.name} <b>{player[list.metric] || 0}</b></button>)}</div>)}</section> : <>
      <section className="stats">{managerStats.slice(0,1).flatMap(manager => [["Budget",BUDGET],["Spesi",manager.spent],["Disponibili",manager.remaining],["Slot mancanti",manager.slotsLeft]]).map(([label,value]) => <div className="card stat" key={label}><span>{label}</span><b>{value}</b></div>)}</section>
      <main><section className="card list"><div className="filters"><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Cerca nome o squadra"/><select value={role} onChange={event => setRole(event.target.value)}><option value="ALL">Tutti i ruoli</option>{ROLE_ORDER.map(item => <option key={item}>{item}</option>)}</select><select value={team} onChange={event => setTeam(event.target.value)}><option value="ALL">Tutte le squadre</option>{teams.map(item => <option key={item}>{item}</option>)}</select><select value={sort} onChange={event => setSort(event.target.value)}>{["quote","initialQuote","quoteDifference","fvm","mantraQuote","mantraFvm"].map(item => <option key={item} value={item}>Ordina {item}</option>)}</select></div>
      <div className="scroll">{(tab === "mine" ? strategyPlayers : filteredPlayers).map(player => { const purchase = purchases.find(item => item.playerKey === playerKey(player)); return <button className={`player ${playerKey(selected) === playerKey(player) ? "active" : ""} ${purchase ? "sold" : ""}`} key={playerKey(player)} onClick={() => selectPlayer(player)}><b>{player.name}{player.inStrategy ? " ★" : ""}</b><i>{player.role}</i><span>{player.team} · Q {displayValue(player.quote)} · FVM {displayValue(player.fvm)} · Δ {displayValue(player.quoteDifference)}{purchase ? ` · PRESO DA ${managers.find(item => item.id === purchase.managerId)?.name} A ${purchase.paid}` : ""}</span></button>})}</div></section>
      <section className="card detail"><div className="player-identity">{selected?.image ? <img className="player-image" src={selected.image} alt={`Foto giocatore ${selected.name}`} /> : <div className="player-image placeholder">{selected?.role || "?"}</div>}<div><h2>{selected?.name}</h2><p>{selected?.team} · {selected?.role} · {selected?.inStrategy ? "Nella lista 25" : "Fuori lista"}</p></div></div><div className="metrics">{[["Q attuale",selected?.quote],["Q iniziale",selected?.initialQuote],["Variazione",selected?.quoteDifference],["FVM",selected?.fvm],["Q Mantra",selected?.mantraQuote],["FVM Mantra",selected?.mantraFvm]].map(([label,value]) => <div key={label}><b>{displayValue(value)}</b><span>{label}</span></div>)}</div><p className="data-note">La sorgente quotazioni non contiene MV, FM, gol o assist. Questi dati non vengono inventati e sono indicati come non disponibili finché non sarà collegata una fonte statistiche separata.</p>
      {selectedStrategy && <div className="strategy"><h3>Strategia</h3><p>Target {selectedStrategy.suggested} · Max {selectedStrategy.max} · Titolarità {selectedStrategy.starter}% · {selectedStrategy.tier} · rischio {selectedStrategy.risk}</p></div>}
      {selectedAlreadyPurchased ? <div className="verdict stop"><b>GIÀ ASSEGNATO</b><span>{managers.find(item => item.id === selectedAlreadyPurchased.managerId)?.name} · {selectedAlreadyPurchased.paid} crediti</span></div> : <><label className="field-label">Acquirente</label><select value={buyerId} onChange={event => setBuyerId(event.target.value)}>{managerStats.map(manager => <option key={manager.id} value={manager.id}>{manager.name} · residuo {manager.remaining} · max {manager.maxAffordable}</option>)}</select><div className="buyer-info"><span>Residuo <b>{selectedManager?.remaining}</b></span><span>Slot {selected?.role} <b>{selectedManager?.counts[selected?.role] || 0}/{TARGET[selected?.role] || "-"}</b></span><span>Può rilanciare fino a <b>{selectedManager?.maxAffordable}</b></span></div><div className="bid"><button onClick={() => setBid(Math.max(1,bid - 1))}>−</button><input type="number" min="1" value={bid} onChange={event => setBid(Number(event.target.value) || 0)}/><button onClick={() => setBid(bid + 1)}>+</button></div><div className={`verdict ${canBuy && bid <= effectiveMax ? "ok" : "stop"}`}><b>{selectedRoleFull ? "RUOLO COMPLETO" : bid > (selectedManager?.maxAffordable || 0) ? "NON PUÒ PERMETTERSELO" : bid <= effectiveMax ? "PUÒ RILANCIARE" : "OLTRE IL TETTO"}</b><span>Tetto effettivo {effectiveMax}</span></div><button className="buy" disabled={!canBuy} onClick={registerPurchase}>Assegna a {selectedManager?.name} per {bid}</button></>}
      </section><aside className="card"><h3>Situazione avversari</h3>{managerStats.map(manager => <button className="manager-line" key={manager.id} onClick={() => { setBuyerId(manager.id); setTab("managers"); }}><span>{manager.name}</span><b>{manager.remaining}</b><small>max {manager.maxAffordable} · slot {manager.slotsLeft}</small></button>)}<button className="reset" onClick={resetAuction}>Reset asta</button></aside></main></>}
    <footer>Dataset tecnico non ufficiale · Strategy {strategyPlayers.length}/25 · Build {appVersion}</footer>
    </div>
  </div>;
}
