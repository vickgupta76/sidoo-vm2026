#!/usr/bin/env python3
"""
VM 2026 Tippekonkurranse - Auto score updater
Henter resultater og oppdaterer begge HTML-filer
"""
import json
import re
import sys
import urllib.request
import urllib.error

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
    ("United States", "Australia"),    # 10
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

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except Exception as e:
        print(f"  Feil ved henting av {url}: {e}")
        return None

def hent_fra_worldcup26():
    print("Prøver worldcup26.ir...")
    data = fetch_url("https://worldcup26.ir/get/games")
    if not data:
        return []
    try:
        games = json.loads(data)
        if isinstance(games, dict):
            games = games.get("games", games.get("matches", []))
        print(f"  Hentet {len(games)} kamper")
        return games
    except:
        return []

def hent_fra_openfootball():
    print("Prøver openfootball...")
    data = fetch_url("https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json")
    if not data:
        return []
    try:
        obj = json.loads(data)
        games = []
        for r in obj.get("rounds", []):
            for m in r.get("matches", []):
                games.append(m)
        print(f"  Hentet {len(games)} kamper")
        return games
    except:
        return []

def finn_score(games, home_hint, away_hint):
    for g in games:
        # worldcup26.ir format
        gh = (g.get("home_team", {}) or {}).get("name", "") if isinstance(g.get("home_team"), dict) else str(g.get("team1", ""))
        ga = (g.get("away_team", {}) or {}).get("name", "") if isinstance(g.get("away_team"), dict) else str(g.get("team2", ""))
        
        # openfootball format
        if not gh:
            gh = (g.get("team1", {}) or {}).get("name", "") if isinstance(g.get("team1"), dict) else str(g.get("team1", ""))
        if not ga:
            ga = (g.get("team2", {}) or {}).get("name", "") if isinstance(g.get("team2"), dict) else str(g.get("team2", ""))

        gh = gh.lower()
        ga = ga.lower()
        
        if home_hint.lower()[:4] not in gh or away_hint.lower()[:4] not in ga:
            continue

        # Prøv ulike score-formater
        hs = g.get("home_score")
        as_ = g.get("away_score")
        
        if hs is None:
            score_obj = g.get("score", {}) or {}
            ft = score_obj.get("ft", [])
            if ft and len(ft) >= 2:
                hs, as_ = ft[0], ft[1]

        if hs is not None and as_ is not None:
            try:
                score = f"{int(hs)}-{int(as_)}"
                status = str(g.get("status", "")).lower()
                finished = any(x in status for x in ["finish", "ft", "ended", "full", "complete"])
                return score, finished
            except:
                pass
    return None, False

def oppdater_html(filepath, resultater):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"  Finner ikke {filepath}")
        return False

    linjer = [
        "// ── RESULTATER – oppdateres etter hver kamp ──────────────────────────",
        "const RESULTATER = ["
    ]
    for idx, score, locked, label in resultater:
        status = "✅" if locked else "🔴 LIVE"
        linjer.append(f'  [{idx}, "{score}"],  // {label} {status}')
    linjer.append("];")
    linjer.append("// ─────────────────────────────────────────────────────────────────────")
    ny_blokk = "\n".join(linjer)

    pattern = r"// ── RESULTATER.*?// ─────────────────────────────────────────────────────────────────────"
    ny_content = re.sub(pattern, ny_blokk, content, flags=re.DOTALL)

    if ny_content == content:
        print(f"  Ingen endringer i {filepath}")
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ny_content)
    print(f"  Oppdatert: {filepath}")
    return True

def main():
    # Prøv API-er
    games = hent_fra_worldcup26()
    if not games:
        games = hent_fra_openfootball()
    
    if not games:
        print("Ingen data tilgjengelig – avslutter uten feil")
        sys.exit(0)  # Exit 0 så workflow ikke feiler

    resultater = []
    for idx, (home, away) in enumerate(KAMP_MAP):
        score, finished = finn_score(games, home, away)
        if score:
            label = f"{home}–{away}: {score}"
            resultater.append((idx, score, finished, label))
            status = "FERDIG" if finished else "LIVE"
            print(f"  Kamp {idx+1}: {score} [{status}]")

    if not resultater:
        print("Ingen resultater funnet ennå – avslutter uten feil")
        sys.exit(0)  # Exit 0 så workflow ikke feiler

    oppdater_html("index.html", resultater)
    oppdater_html("sioov/index.html", resultater)
    print(f"\nFerdig! {len(resultater)} kamper oppdatert.")

if __name__ == "__main__":
    main()
