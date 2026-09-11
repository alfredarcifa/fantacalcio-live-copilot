# Pipeline

`player-strategy.json` contiene la shortlist. `all-players.generated.json` contiene il listone completo o il fallback. Lo script non sovrascrive i dati se la sorgente ha meno di 100 giocatori. Il deploy non viene bloccato da indisponibilità esterne.


## Contratto sorgente v2.2

Il normalizzatore legge `position` come ruolo, `team` come squadra, `qt_att` come quotazione corrente, `fvm` come FVM e `playerImage` come immagine. La strategia viene riconciliata prima per nome+squadra e poi per nome univoco.


## Mapping v2.3

- `qt_att` → quotazione Classic attuale
- `qt_i` → quotazione Classic iniziale
- `diff` → variazione Classic
- `qt_att_m` → quotazione Mantra attuale
- `qt_i_m` → quotazione Mantra iniziale
- `diff_m` → variazione Mantra
- `fvm` → FVM Classic
- `fvm_m` → FVM Mantra
- `playerImage` → immagine giocatore

Il feed non contiene statistiche di rendimento. I relativi campi restano `null`/N/D.
