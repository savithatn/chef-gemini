import os
import shutil
import time
from playwright.sync_api import sync_playwright

def record_demo():
    if os.path.exists("demo_raw"):
        shutil.rmtree("demo_raw")
    os.makedirs("demo_raw", exist_ok=True)

    target_url = "https://chef-gemini-frontend-234806946617.us-east1.run.app"
    print(f"Starting 2-prompt demo recording for {target_url}...")

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

        # --- PROMPT 1 ---
        print(">>> Submitting PROMPT 1: Pantry Recipe Search...")
        chip1 = page.locator(".prompt-chip:has-text('Pantry Recipe Search')")
        if chip1.is_visible():
            chip1.click()
        else:
            page.fill("#input", "What recipes can I make with ingredients in my pantry?")
            page.click("button.send-btn")

        print("Waiting for PROMPT 1 response to finish returning...")
        page.wait_for_selector(".msg-wrapper.agent", timeout=30000)
        for _ in range(30):
            agent_bubbles = page.locator(".msg-wrapper.agent .bubble")
            if agent_bubbles.count() >= 1:
                txt = agent_bubbles.last.text_content() or ""
                if "Thinking" not in txt:
                    print("--> PROMPT 1 response returned successfully!")
                    break
            time.sleep(1)
        time.sleep(3) # Pause so viewer can read the response

        # --- PROMPT 2 ---
        print(">>> Submitting PROMPT 2: Recipe Photo Generator...")
        chip2 = page.locator(".prompt-chip:has-text('Recipe Photo Generator')")
        if chip2.is_visible():
            chip2.click()
        else:
            page.fill("#input", "Find a healthy dinner recipe and generate a photo of it")
            page.click("button.send-btn")

        print("Waiting for PROMPT 2 response to finish returning...")
        for _ in range(45):
            agent_bubbles = page.locator(".msg-wrapper.agent .bubble")
            if agent_bubbles.count() >= 2:
                txt = agent_bubbles.last.text_content() or ""
                if "Thinking" not in txt:
                    print("--> PROMPT 2 response (with photo/A2UI card) returned successfully!")
                    break
            time.sleep(1)
        time.sleep(5) # Pause to showcase generated photo card

        print("Closing browser context to save video file...")
        page.close()
        context.close()
        browser.close()
        print("Demo recording complete!")

if __name__ == "__main__":
    record_demo()
