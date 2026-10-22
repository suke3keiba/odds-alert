from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("https://jra.jp/", timeout=60000)
    page.get_by_role("link", name="オッズ", exact=True).first.click()
    page.wait_for_load_state("load")
    print("url:", page.url)
    print("title:", page.title())
    texts = page.eval_on_selector_all(
        "a",
        "els => els.map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)",
    )
    print("links:", texts[:80])
    b.close()
