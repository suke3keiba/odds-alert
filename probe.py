from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("https://jra.jp/", timeout=60000)
    page.get_by_role("link", name="オッズ", exact=True).first.click()
    page.wait_for_load_state("load")
    body = page.inner_text("body")
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    print("kaisai lines:", [l for l in lines if "回" in l and "日" in l][:30])
    clicks = page.eval_on_selector_all(
        "a[onclick]",
        "els => els.map(e => (e.getAttribute('onclick') || '').slice(0, 120))",
    )
    print("onclick count:", len(clicks))
    print("onclick samples:", clicks[:5])
    b.close()
