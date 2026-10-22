import json, os, time, urllib.request

cfg = json.load(open("config.json", encoding="utf-8"))
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
calls = 0


def get_odds():
    # 練習用のダミーデータ。あとで本物の取得に差し替えます
    global calls
    calls += 1
    odds = {"1": 5.0, "2": 12.0, "3": 30.0}
    if calls >= 3:
        odds["2"] = 9.0
    return odds


def notify(text):
    print(text)
    if not WEBHOOK:
        return
    data = json.dumps({"content": text}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "odds-alert"},
    )
    urllib.request.urlopen(req)


history = []
alerted = set()
for i in range(cfg["loops"]):
    now = time.time()
    odds = get_odds()
    history.append((now, odds))
    history = [h for h in history if now - h[0] <= cfg["window_seconds"]]
    old = history[0][1]
    for no, cur in odds.items():
        before = old.get(no)
        if not before or cur >= before:
            continue
        drop = (before - cur) / before * 100
        if drop >= cfg["drop_percent"] and no not in alerted:
            alerted.add(no)
            notify(f"{no}番 単勝 {before}→{cur} ({drop:.0f}%下落)")
    time.sleep(cfg["interval_seconds"])
