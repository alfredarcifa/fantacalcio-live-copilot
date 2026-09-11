# Fantacalcio Live Copilot

Prototipo interattivo per supportare un'asta Fantacalcio Classic da 8 squadre con budget 1000, modificatore difesa e modificatore capitano.

## Funzioni incluse
- Lista iniziale di 25 giocatori
- Ricerca e filtro per ruolo
- Offerta corrente e tetto dinamico
- Verdetto RILANCIA / ULTIMO RILANCIO / LASCIA
- Budget, spesa, slot e rosa personale
- Registrazione manuale delle scelte avversarie

> I dati giocatore inclusi sono una base di lavoro e devono essere verificati/aggiornati prima dell'asta.

## Avvio locale
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
npm run preview
```

## Pubblicazione iniziale su GitHub
```bash
git init
git add .
git commit -m "feat: bootstrap fantacalcio live copilot"
git branch -M main
git remote add origin <URL_REPOSITORY>
git push -u origin main
```

## Struttura
- `src/App.jsx`: interfaccia e stato dell'asta
- `src/data/players.js`: dataset iniziale
- `src/components/ui`: primitive UI locali
- `docs`: visione prodotto, regole, motore decisionale e fonti dati
