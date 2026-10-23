from playwright.sync_api import sync_playwright


def show(page, label, n):
    lines = [l.strip() for l in page.inner_text("body").splitlines() if l.strip()]
    start = 0
    for i, l in enumerate(lines):
        if "ここから本文です" in l:
            start = i
    print(label, lines[start:start + n])


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page()
    page.goto("https://jra.jp/", timeout=60000)
    page.get_by_role("link", name="オッズ", exact=True).first.click()
    page.wait_for_load_state("load")
    page.get_by_text("4回東京8日").first.click()
    page.wait_for_load_state("load")
    show(page, "race list:", 40)
    try:
        page.get_by_text("11R", exact=True).first.click(timeout=10000)
        page.wait_for_load_state("load")
        show(page, "odds page:", 120)
    except Exception as e:
        print("11R click failed:", str(e)[:200])
    b.close()
