from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("https://jra.jp/", timeout=60000)
    page.get_by_role("link", name="オッズ", exact=True).first.click()
    page.wait_for_load_state("load")
    body = page.inner_text("body")
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    start = 0
    for i, l in enumerate(lines):
        if "オッズ" in l and "開催" in l:
            start = i
    print("body:", lines[start:start + 40])
    b.close()
