import asyncio
from playwright.async_api import Playwright, async_playwright, expect
from config import Config

async def auto_topup_playwright(user_id: str, zone_id: str, diamond_package_playwright_index: int, card_details: dict):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True) # Set to False for visual debugging
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to Codashop...")
        await page.goto("https://www.codashop.com/my-mm/mobile-legends")

        # Input User ID and Zone ID
        print(f"Entering User ID: {user_id} and Zone ID: {zone_id}")
        await page.fill(Config.PLAYWRIGHT_SELECTORS["user_id_input"], user_id)
        await page.fill(Config.PLAYWRIGHT_SELECTORS["zone_id_input"], zone_id)

        # Select Diamond Package
        print(f"Selecting diamond package at index: {diamond_package_playwright_index}")
        diamond_selector = f"div[role=\"radio\"]:nth-child({diamond_package_playwright_index})"
        await page.click(diamond_selector)

        # Select Card Payment
        print("Selecting Card Payment...")
        await page.click(Config.PLAYWRIGHT_SELECTORS["card_payment_radio"])

        # Click \'Buy Now\' button
        print("Clicking \'Buy Now\'...")
        await page.click(Config.PLAYWRIGHT_SELECTORS["buy_now_button"])

        # Wait for navigation to the payment page
        print("Waiting for payment page...")
        # This URL pattern might need to be more specific or use a different wait condition
        await page.wait_for_url("**/checkout", timeout=60000) 

        # Fill in card details
        print("Filling card details...")
        await page.fill(Config.PLAYWRIGHT_SELECTORS["card_number_input"], card_details["number"])
        await page.fill(Config.PLAYWRIGHT_SELECTORS["card_expiry_input"], card_details["expiry"])
        await page.fill(Config.PLAYWRIGHT_SELECTORS["card_cvv_input"], card_details["cvv"])

        # Click payment button
        print("Submitting payment...")
        await page.click(Config.PLAYWRIGHT_SELECTORS["pay_now_button"])

        # Wait for transaction result (success/failure)
        await page.wait_for_selector(Config.PLAYWRIGHT_SELECTORS["transaction_status"], timeout=60000)
        status = await page.locator(Config.PLAYWRIGHT_SELECTORS["transaction_status"]).text_content()
        print(f"Transaction Status: {status}")

        await browser.close()
        return status

# Other helper functions can be added here
