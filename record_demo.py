import os
import time
from playwright.sync_api import sync_playwright

def record_demo():
    os.makedirs("demo_raw", exist_ok=True)
    target_url = "https://chef-gemini-frontend-234806946617.us-east1.run.app"
    print(f"Launching Playwright to record demo of {target_url}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--window-size=1280,800"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir="demo_raw/",
            record_video_size={"width": 1280, "height": 800}
        )
        page = context.new_page()

        print("Navigating to Chef Gemini frontend...")
        page.goto(target_url, wait_until="networkidle")
        time.sleep(2)

        # 1. Click prompt chip 1: Pantry Recipe Search
        print("Clicking prompt chip 1...")
        chip1 = page.locator(".prompt-chip:has-text('Pantry Recipe Search')")
        if chip1.is_visible():
            chip1.click()
            time.sleep(6)
        else:
            print("Chip 1 not found, typing manually...")
            page.fill("#input", "What recipes can I make with ingredients in my pantry?")
            page.click("button.send-btn")
            time.sleep(6)

        # 2. Click prompt chip 2: Recipe Photo Generator
        print("Clicking prompt chip 2...")
        chip2 = page.locator(".prompt-chip:has-text('Recipe Photo Generator')")
        if chip2.is_visible():
            chip2.click()
            time.sleep(8)

        # 3. Type custom query for memory or dietary preferences
        print("Typing memory preference prompt...")
        page.fill("#input", "Remember that I love Mediterranean cuisine and fresh herbs.")
        time.sleep(1)
        page.click("button.send-btn")
        time.sleep(6)

        print("Finished interaction flow. Closing browser context...")
        page.close()
        context.close()
        browser.close()
        print("Raw webm demo video saved to demo_raw/")

if __name__ == "__main__":
    record_demo()
