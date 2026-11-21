# epson-ipp-bridge

Pont d'impression custom pour l'**EPSON XP-4200 Series** (192.168.1.55).

## Pourquoi

Le serveur d'impression de l'Epson n'accepte que de l'**IPP over TLS** sur le port 631.
Le spooler Windows (port RAW) envoie des données brutes que l'imprimante ignore :
Windows croit la page envoyée, mais rien n'imprime.

Ce pont écoute en local sur `127.0.0.1:9100`, empaquette chaque job reçu dans une
requête **IPP Print-Job** (`document-format: application/vnd.epson.escpr`) et la
transmet chiffrée (TLS) à l'imprimante.

```
App Windows -> Spooler -> 127.0.0.1:9100 (RAW)
   -> ipp_bridge.py
   -> IPP/TLS -> 192.168.1.55:631 -> EPSON XP-4200
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `ipp_bridge.py` | Le pont (écoute 127.0.0.1:9100, forward IPP/TLS vers 192.168.1.55:631) |
| `ipp_bridge_start.bat` | Lanceur au démarrage (à placer dans le dossier Startup) |

## Installation

1. `pip install` (rien, bibliothèque standard uniquement — Python 3)
2. Copier `ipp_bridge_start.bat` dans
   `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
3. Dans Windows : ajouter une imprimante sur le port `127.0.0.1:9100` (RAW),
   pilote **Epson ESC/P-R V4 Class Driver**, nom conseillé :
   `EPSON XP-4200 Series (Reseau)`

## Journal

Le pont écrit dans `ipp_bridge.log` (même dossier que le script).
Les sondes du moniteur de port Windows (< 1 Ko) sont ignorées automatiquement.

## Note

L'imprimante se met en veille profonde après quelques minutes d'inactivité :
appuyer sur son bouton d'alimentation pour la réveiller avant d'imprimer.
