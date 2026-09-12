# Pipeline v2.5

La pipeline mantiene il contratto dati v2.3 e aggiunge la build Tailwind v4.

1. aggiorna il listone da due endpoint alternativi;
2. mantiene il fallback se la sorgente è indisponibile o incompleta;
3. genera `VITE_APP_VERSION=2.5.<run>+<sha>`;
4. esegue `npm ci` e `npm run build`;
5. verifica che la versione sia presente negli asset;
6. pubblica GitHub Pages.
