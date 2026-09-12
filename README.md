# Fantacalcio Live Copilot v2

Dashboard completa con listone, lista 25, statistiche e asta. La pipeline tenta due endpoint pubblici non ufficiali; se entrambi falliscono mantiene il fallback versionato e pubblica comunque il sito.


## Versione 2.2

- dashboard a quattro viste: tutti, lista 25, avversari e statistiche;
- otto fantallenatori con budget, acquisti, slot e massima offerta sostenibile;
- versione build visibile nell'interfaccia;
- mapping corretto della quotazione corrente dal campo `qt_att`;
- strategia separata dal listone completo.


## Versione 2.3

Il feed quotazioni viene interpretato integralmente: `qt_att`, `qt_i`, `diff`, `qt_att_m`, `qt_i_m`, `diff_m`, `fvm`, `fvm_m` e `playerImage`. MV, FM, gol e assist non sono presenti nel feed e non vengono rappresentati come zero.


## Versione 2.4
Restyling dark analytics con navigazione laterale, top bar, pannelli compatti, immagini giocatore, gestione lega e versionamento visibile. Rimossi duplicati visuali e metriche non disponibili dalle righe del listone.
