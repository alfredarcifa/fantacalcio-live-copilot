# Pipeline dati Fantacalcio

Questo pacchetto sostituisce il workflow di deploy e aggiunge lo script di aggiornamento.

## File

- `.github/workflows/deploy.yml`
- `scripts/update_fantacalcio.py`

Il workflow scarica quotazioni e statistiche ufficiali Fantacalcio.it, aggiorna in memoria `src/players.json`, costruisce l'app e pubblica GitHub Pages. Non effettua commit automatici e non richiede token o secret.

## Frequenza

- a ogni push su `main`;
- ogni giorno alle 04:17 UTC;
- manualmente da Actions tramite `workflow_dispatch`.

## Sicurezza

La pubblicazione viene bloccata se nessun giocatore viene riconciliato o se il match è inferiore al 70%. I campi strategici `suggested`, `max`, `starter`, `risk` e `tier` restano invariati.
