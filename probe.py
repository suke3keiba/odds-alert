from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    r = page.goto("https://www.jra.jp/", timeout=60000)
    print("status:", r.status if r else None)
    print("title:", page.title())
    texts = page.eval_on_selector_all(
        "a", "els => els.map(e => e.innerText.trim()).filter(t => t)"
    )
    print("odds links:", [t for t in texts if "オッズ" in t])
    b.close()
