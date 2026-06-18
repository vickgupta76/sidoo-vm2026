#!/usr/bin/env python3
"""
VM 2026 Tippekonkurranse - Auto score updater
Henter resultater fra worldcup26.ir og oppdaterer begge HTML-filer
"""
import json
import re
import sys
import urllib.request
from datetime import datetime

# Kampene vi følger med på (0-indeksert)
KAMP_MAP = [
    ("Mexico",      "South Africa"),   # 0
    ("Canada",      "Bosnia"),         # 1
    ("Brazil",      "Morocco"),        # 2
    ("Netherlands", "Japan"),          # 3
    ("Spain",       "Cape Verde"),     # 4
    ("Belgium",     "Egypt"),          # 5
    ("France",      "Senegal"),        # 6
    ("Iraq",        "Norway"),         # 7
    ("England",     "Croatia"),        # 8
    ("Czech",       "South Africa"),   # 9
    ("USA",         "Australia"),      # 10
    ("Scotland",    "Morocco"),        # 11
    ("Netherlands", "Sweden"),         # 12
    ("Spain",       "Saudi"),          # 13
    ("Belgium",     "Iran"),           # 14
    ("Argentina",   "Austria"),        # 15
    ("Norway",      "Senegal"),        # 16
    ("England",     "Ghana"),          # 17
    ("Switzerland", "Canada"),         # 18
    ("Ecuador",     "Germany"),        # 19
    ("Norway",      "France"),         # 20
    ("Colombia",    "Portugal"),       # 21
]

def tegn(score):
    h, b = map(int, score.split("-"))
    return "H" if h > b else ("B" if h < b else "U")

def hent_resultater():
    print("Henter data fra worldcup26.ir...")
    try:
        req = urllib.request.Request(
            "https://worldcup26.ir/get/games",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"Feil ved henting: {e}")
        return None

    games = data if isinstance(data, list) else data.get("games", data.get("matches", []))
    print(f"Hentet {len(games)} kamper")
    return games

def finn_resultat(games, home_hint, away_hint):
    for g in games:
        gh = (g.get("home_team", {}).get("name", "") or g.get("team1", "")).lower()
        ga = (g.get("away_team", {}).get("name", "") or g.get("team2", "")).lower()
        if home_hint.lower()[:4] in gh and away_hint.lower()[:4] in ga:
            hs = g.get("home_score") if g.get("home_score") is not None else (g.get("score", {}) or {}).get("ft", [None, None])[0]
            as_ = g.get("away_score") if g.get("away_score") is not None else (g.get("score", {}) or {}).get("ft", [None, None])[1]
            status = (g.get("status", "") or "").lower()
            if hs is not None and as_ is not None:
                score = f"{hs}-{as_}"
                finished = any(x in status for x in ["finish", "ft", "ended", "full", "complete"])
                return score, finished
    return None, False

def oppdater_html(filepath, resultater_liste):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Bygg ny RESULTATER array
    linjer = ["// ── RESULTATER – oppdateres etter hver kamp ──────────────────────────",
              "const RESULTATER = ["]
    for idx, score, locked, label in resultater_liste:
        status = "✅" if locked else "🔴 LIVE"
        linjer.append(f'  [{idx}, "{score}"],  // {label} {status}')
    linjer.append("];")
    linjer.append("// ─────────────────────────────────────────────────────────────────────")
    ny_resultater = "\n".join(linjer)

    # Erstatt eksisterende RESULTATER-blokk
    pattern = r"// ── RESULTATER.*?// ─────────────────────────────────────────────────────────────────────"
    ny_content = re.sub(pattern, ny_resultater, content, flags=re.DOTALL)

    # Oppdater locked i JavaScript
    locked_idxs = [str(idx) for idx, _, locked, _ in resultater_liste if locked]
    locked_str = ",".join(locked_idxs)
    # Oppdater timestamp
    now = datetime.utcnow().strftime("%d.%m %H:%M UTC")
    ny_content = re.sub(
        r'document\.getElementById\(\'apiStatus\'\)\.textContent=`.*?`;',
        f"document.getElementById('apiStatus').textContent=`✓ Oppdatert {now}`;",
        ny_content
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ny_content)
    print(f"Oppdatert: {filepath}")

def main():
    games = hent_resultater()
    if not games:
        print("Ingen data – avslutter")
        sys.exit(1)

    resultater = []
    for idx, (home, away) in enumerate(KAMP_MAP):
        score, finished = finn_resultat(games, home, away)
        if score:
            label = f"{home}–{away}: {score}"
            resultater.append((idx, score, finished, label))
            status = "FERDIG" if finished else "LIVE"
            print(f"  Kamp {idx+1} ({home} vs {away}): {score} [{status}]")

    if not resultater:
        print("Ingen resultater funnet ennå")
        sys.exit(0)

    oppdater_html("index.html", resultater)
    oppdater_html("sioov/index.html", resultater)
    print(f"\nFerdig! {len(resultater)} kamper oppdatert.")

if __name__ == "__main__":
    main()
