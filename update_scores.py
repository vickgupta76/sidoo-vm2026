#!/usr/bin/env python3
import json, re, sys, urllib.request

KAMP_MAP = [
    ("Mexico", "South Africa"), ("Canada", "Bosnia"),
    ("Brazil", "Morocco"), ("Netherlands", "Japan"),
    ("Spain", "Cape Verde"), ("Belgium", "Egypt"),
    ("France", "Senegal"), ("Iraq", "Norway"),
    ("England", "Croatia"), ("Czech Republic", "South Africa"),
    ("USA", "Australia"), ("Scotland", "Morocco"),
    ("Netherlands", "Sweden"), ("Spain", "Saudi Arabia"),
    ("Belgium", "Iran"), ("Argentina", "Austria"),
    ("Norway", "Senegal"), ("England", "Ghana"),
    ("Switzerland", "Canada"), ("Ecuador", "Germany"),
    ("Norway", "France"), ("Colombia", "Portugal"),
]

def tegn(score):
    h, b = map(int, score.split("-"))
    return "H" if h > b else ("B" if h < b else "U")

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Feil: {e}")
        return None

def hent_espn():
    print("Henter fra ESPN...")
    # ESPN API for FIFA World Cup 2026
    urls = [
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?limit=50",
    ]
    for url in urls:
        data = fetch(url)
        if data:
            events = data.get("events", [])
            if events:
                print(f"  Hentet {len(events)} kamper fra ESPN")
                return events
    return []

def parse_espn(events):
    resultater = []
    for event in events:
        comps = event.get("competitions", [{}])
        if not comps:
            continue
        comp = comps[0]
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue

        # Finn hjemme og borte
        home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

        home_name = home.get("team", {}).get("displayName", "")
        away_name = away.get("team", {}).get("displayName", "")
        home_score = home.get("score", None)
        away_score = away.get("score", None)
        status = event.get("status", {}).get("type", {}).get("completed", False)

        if home_score is not None and away_score is not None:
            for idx, (h_hint, a_hint) in enumerate(KAMP_MAP):
                if h_hint.lower()[:4] in home_name.lower() and a_hint.lower()[:4] in away_name.lower():
                    score = f"{int(home_score)}-{int(away_score)}"
                    resultater.append((idx, score, status, f"{home_name}–{away_name}: {score}"))
                    print(f"  Kamp {idx+1}: {score} {'✅' if status else '🔴'}")
    return resultater

def oppdater_html(filepath, resultater):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Finner ikke {filepath}")
        return

    linjer = [
        "// ── RESULTATER – oppdateres etter hver kamp ──────────────────────────",
        "const RESULTATER = ["
    ]
    for idx, score, locked, label in resultater:
        status = "✅" if locked else "🔴 LIVE"
        linjer.append(f'  [{idx}, "{score}"],  // {label} {status}')
    linjer.append("];")
    linjer.append("// ─────────────────────────────────────────────────────────────────────")

    pattern = r"// ── RESULTATER.*?// ─────────────────────────────────────────────────────────────────────"
    ny = re.sub(pattern, "\n".join(linjer), content, flags=re.DOTALL)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(ny)
    print(f"Oppdatert: {filepath}")

def main():
    events = hent_espn()
    if not events:
        print("Ingen data – avslutter")
        sys.exit(0)

    resultater = parse_espn(events)
    if not resultater:
        print("Ingen VM-kamper funnet ennå")
        sys.exit(0)

    oppdater_html("index.html", resultater)
    oppdater_html("sioov/index.html", resultater)
    print(f"Ferdig! {len(resultater)} kamper.")

if __name__ == "__main__":
    main()
