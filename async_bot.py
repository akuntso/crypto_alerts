import tracemalloc
tracemalloc.start()

import asyncio
import time
import datetime

from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes

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

        await page.get_by_role("textbox", name="-100%").fill("3")

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
        return data
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = 'Привіт! Використовуйте команду\n /fetch, щоб отримати дані.'
    await update.message.reply_text(text=text)

# Обробник команди /fetch
async def fetch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    current_time_seconds = time.time()
    # Перетворити у формат дати і часу
    current_time = datetime.datetime.fromtimestamp(current_time_seconds).strftime('%Y-%m-%d %H:%M:%S')

    data = await fetch_data()
    message = "\n".join(data)
    await update.message.reply_text(f'{message}\n{current_time}')

if __name__ == "__main__":
    token = '6884814030:AAGlpMsTZUNzrLrDxa9K7eL1e1dVYufiwq8'
    
    app = Application.builder().token(token).build()

    start_handler = CommandHandler('start', start)
    fetch_handler = CommandHandler('fetch', fetch)

    app.add_handler(start_handler)
    app.add_handler(fetch_handler)

    app.run_polling()