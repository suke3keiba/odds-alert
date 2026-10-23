import json, os, re, time, urllib.request
from playwright.sync_api import sync_playwright

cfg = json.load(open("config.json", encoding="utf-8"))
WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")


def notify(text):
    print("通知:", text)
    if not WEBHOOK:
        return
    data = json.dumps({"content": text}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "odds-alert"},
    )
    urllib.request.urlopen(req)


def open_race(page):
    page.goto("https://jra.jp/", timeout=60000)
    page.get_by_role("link", name="オッズ", exact=True).first.click()
    page.wait_for_load_state("load")
    page.get_by_text(cfg["kaisai"]).first.click()
    page.wait_for_load_state("load")
    page.get_by_text("単勝複勝", exact=True).nth(cfg["race"] - 1).click()
    page.wait_for_load_state("load")


def read_odds(page):
    odds = {}
    for row in page.locator("table tr").all_inner_texts():
        m = re.search(r"(\d{1,2})\t([^\t\n]+)\t([\d,]+\.\d)", row)
        if m:
            odds[m.group(1)] = (m.group(2), float(m.group(3).replace(",", "")))
    return odds


history = []
alerted = set()
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    open_race(page)
    notify(f"監視開始: {cfg['kaisai']} {cfg['race']}R")
    for i in range(cfg["loops"]):
        if i > 0:
            try:
                page.get_by_text("更新", exact=True).first.click(timeout=10000)
                page.wait_for_load_state("load")
            except Exception:
                open_race(page)
        now = time.time()
        odds = read_odds(page)
        print(i + 1, "回目", {k: v[1] for k, v in odds.items()})
        if odds:
            history.append((now, odds))
        history = [h for h in history if now - h[0] <= cfg["window_seconds"]]
        if history:
            old = history[0][1]
            for no, (name, cur) in odds.items():
                if no not in old:
                    continue
                before = old[no][1]
                if cur >= before:
                    continue
                drop = (before - cur) / before * 100
                if drop >= cfg["drop_percent"] and no not in alerted:
                    alerted.add(no)
                    notify(
                        f"{cfg['kaisai']} {cfg['race']}R {no}番 {name} "
                        f"単勝 {before}→{cur} ({drop:.0f}%下落)"
                    )
        time.sleep(cfg["interval_seconds"])
    browser.close()
