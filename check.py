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


def open_race(page, race):
    page.goto("https://jra.jp/", timeout=60000)
    page.get_by_role("link", name="オッズ", exact=True).first.click()
    page.wait_for_load_state("load")
    page.get_by_text(cfg["kaisai"]).first.click()
    page.wait_for_load_state("load")
    page.get_by_text("単勝複勝", exact=True).nth(race - 1).click()
    page.wait_for_load_state("load")


def goto_race(page, race, on_race_page):
    if on_race_page:
        try:
            page.get_by_text("レース選択へ戻る").first.click(timeout=10000)
            page.wait_for_load_state("load")
            page.get_by_text("単勝複勝", exact=True).nth(race - 1).click(timeout=10000)
            page.wait_for_load_state("load")
            return
        except Exception:
            pass
    open_race(page, race)


def read_odds(page):
    odds = {}
    for row in page.locator("table tr").all_inner_texts():
        m = re.search(r"(\d{1,2})\t([^\t\n]+)\t([\d,]+\.\d)", row)
        if m:
            odds[m.group(1)] = (m.group(2), float(m.group(3).replace(",", "")))
    return odds


def find_drops(state, odds, now):
    state["history"].append((now, odds))
    state["history"] = [
        h for h in state["history"] if now - h[0] <= cfg["window_seconds"]
    ]
    old = state["history"][0][1]
    found = []
    for no, (name, cur) in odds.items():
        if no not in old:
            continue
        before = old[no][1]
        if cur >= before:
            continue
        drop = (before - cur) / before * 100
        if drop >= cfg["drop_percent"] and no not in state["alerted"]:
            state["alerted"].add(no)
            found.append((no, name, before, cur, drop))
    return found


if __name__ == "__main__":
    states = {r: {"history": [], "alerted": set()} for r in cfg["races"]}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        notify(f"監視開始: {cfg['kaisai']} {cfg['races']}R")
        on_race_page = False
        for i in range(cfg["loops"]):
            for race in cfg["races"]:
                try:
                    goto_race(page, race, on_race_page)
                    on_race_page = True
                    body = page.inner_text("body")
                    m = re.search(r"発走時刻：(\d+時\d+分)", body)
                    start = m.group(1) if m else "?"
                    odds = read_odds(page)
                    print(i + 1, "回目", f"{race}R", start, {k: v[1] for k, v in odds.items()})
                    if not odds:
                        continue
                    for no, name, before, cur, drop in find_drops(
                        states[race], odds, time.time()
                    ):
                        notify(
                            f"{cfg['kaisai']} {race}R({start}発走) {no}番 {name} "
                            f"単勝 {before}→{cur} ({drop:.0f}%下落)"
                        )
                except Exception as e:
                    print("エラー:", race, str(e)[:200])
                    on_race_page = False
            time.sleep(cfg["interval_seconds"])
        browser.close()
