import tracemalloc
tracemalloc.start()

import asyncio
from playwright.async_api import async_playwright

async def fetch_data() -> list:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=100)
        context = await browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        page = await context.new_page()
        await page.goto("https://www.coinglass.com/en")

        filtr = page.get_by_role("button", name="Filters")
        await filtr.click(force=True)
        await page.get_by_role("button", name="Price Change").click()
        await page.get_by_role("button", name="Price Change (5m)").click()

        await page.get_by_role("textbox", name="-100%").fill("1")

        await page.get_by_role("button", name="Apply Filter").click()
        await page.get_by_role("button", name="Close").click()

        await page.wait_for_selector('tbody.ant-table-tbody')

        # Витягування значень атрибуту data-row-key з кожного tr
        row_data = await page.evaluate('''() => {
            const tbodys = document.querySelectorAll('tbody.ant-table-tbody');
            const rows = tbodys[0].querySelectorAll('tr');
            return Array.from(rows).map(row => row.getAttribute('data-row-key'));
        }''')

        await browser.close()
        # Форматування даних
        data = [str(element) if element is not None else 'No data' for element in row_data]
        message = "\n".join(data)
        return message

data = asyncio.run(fetch_data())
print(data)