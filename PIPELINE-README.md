# Pipeline

`player-strategy.json` contiene la shortlist. `all-players.generated.json` contiene il listone completo o il fallback. Lo script non sovrascrive i dati se la sorgente ha meno di 100 giocatori. Il deploy non viene bloccato da indisponibilità esterne.


## Contratto sorgente v2.2

Il normalizzatore legge `position` come ruolo, `team` come squadra, `qt_att` come quotazione corrente, `fvm` come FVM e `playerImage` come immagine. La strategia viene riconciliata prima per nome+squadra e poi per nome univoco.
