import requests
import time
import datetime
import os
import threading
import logging

import schedule

from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright, Playwright, Page

BOT_TOKEN = '6884814030:AAGlpMsTZUNzrLrDxa9K7eL1e1dVYufiwq8'
CHAT_ID = 725151616

TWO_PERC_PRICE = '2'
THREE_PERC_PRICE = '3'
TEN_PERC_PRICE = '10'

FIVE_INTR_PICE = 5
FTN_INTR_PRICE = 15

CHG_IO = '5'

class TelegramBot:

    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.percentage = None
        self.filters = None


        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # Логування у консоль
                logging.FileHandler('my_log_file.log')  # Логування у файл
            ]
        )

    def _handle_consent_your_personal_data_popup(self, page: Page):
        # Обробка спливаючого вікна якщо воно появилося, знайти і натиснути кнопку "Consent"
        try:
            logging.info("Waiting for 'Consent popup to appear'")
            page.wait_for_selector(selector='button[aria-label="Consent"]', timeout=5000)
            consent_button = page.locator('button[aria-label="Consent"]')
            consent_button.click()
            logging.info("Consent button clicked")
        except Exception:
            logging.warning("Consent popup was not appeared")


    def _get_coins_data_screenshot(self, page: Page):
        current_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')
        # перезиписує змінну скріншот нейм, початково вона None
        self.screenshot_name = f"{self.percentage}%_{self.filters}__{current_time}.png"
        screenshots_path = os.path.join('screenshots', self.screenshot_name)
        logging.info(f"Saving screenshot - {self.screenshot_name}")
        page.screenshot(path=screenshots_path)


    def _append_coins_data_to_file(self, coins_to_add):
        logging.info("Writing coin data to the file")
        with open('coindata.txt', 'a') as file:
            file.write(coins_to_add + '\n')


    def _set_page_and_go_to_coinglass(self, playwright: Playwright) -> Page:
        browser = playwright.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        page = context.new_page()
        page.set_viewport_size({'width': 1080, 'height': 1080})

        logging.info("Going to 'Coinglass'")
        page.goto("https://www.coinglass.com/en")
        self._handle_consent_your_personal_data_popup(page)
        logging.info("Going to 'Filter'")
        page.get_by_role("button", name="Filters").click(force=True)
        
        return page


    def _get_data_from_table(self, page: Page) -> str:
        page.wait_for_selector('tbody.ant-table-tbody')
        logging.info("Waiting for data to display 2 sec")
        page.wait_for_timeout(2000)
        logging.info(f"Fetching coins from site table")
        coins_from_table = page.evaluate('''() => {
                const tbodys = document.querySelectorAll('tbody.ant-table-tbody');
                const rows = tbodys[0].querySelectorAll('tr');
                return Array.from(rows).map(row => row.getAttribute('data-row-key'));
        }''')

        if all(element is None for element in coins_from_table):
            logging.info(f"No Data to display on website")
            return ''
        else:

            current_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d_%H-%M-%S')
            logging.info(f"Preparing data for Telegram bot")
            proceded_coins = [str(f'{coin} - https://www.coinglass.com/tv/ru/Binance_{coin}USDT') for coin in coins_from_table if coin is not None]
            coins_for_message = f"Coins with changed {self.filters} over {self.percentage}%\n" + "\n".join(proceded_coins) + f'\n{current_time}'

            return coins_for_message


    def _send_telegram_message(self, message: str):
        logging.warning(f"Processing message into send_telegram_bot: {message}")
        if not message:
            logging.error("No Data to sent to Telegram bot")
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        headers = {
            "Content-Type": "application/json"
        }

        logging.info(f"Sending message to the chat with")
        response = requests.post(url, json=payload, headers=headers)
        logging.info(f"Response is -- {response}")
        return response.json()


    def _send_telegram_photo(self):

        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        logging.warning("Checking photo name if new exists")

        if not self.screenshot_name:
            logging.error(f"Screenshot name is -- {self.screenshot_name}")
            return

        files = {'photo': open(f'screenshots/{self.screenshot_name}', 'rb')}
        logging.info("Sending Photo to the chat")
        response = requests.post(url, files=files, data={'chat_id': self.chat_id})
        logging.info(f"Response is -- {response}")
        return response.json()


class BotPrice(TelegramBot):

    def __init__(self, percentage_price: str=THREE_PERC_PRICE, interval: int=FIVE_INTR_PICE):
        super().__init__()
        self.percentage = percentage_price
        self.interval = interval
        self.screenshot_name = None
        self.filters = 'Price'


    def _apply_filter_price(self, page: Page):
        logging.info("Selecting 'Price Change'")
        page.get_by_role("button", name="Price Change").click()
        page.get_by_role("button", name=f"Price Change ({self.interval}m)").click()
        page.get_by_role("textbox", name="-100%").fill(self.percentage)
        page.get_by_role("button", name="Apply Filter").click()
        logging.info("Selecting 'Close'")
        page.get_by_role("button", name="Close").click()
        logging.info(f"Filter for price over {self.percentage}% was succssesfuly applied")


    def fetch_coins_with_changed_price(self) -> str:
        with sync_playwright() as playwright:
            page = self._set_page_and_go_to_coinglass(playwright)
            self._apply_filter_price(page)
            coins_for_message = self._get_data_from_table(page)
            if coins_for_message:
                self._append_coins_data_to_file(coins_for_message)
                self._get_coins_data_screenshot(page)

            return coins_for_message


    def send_telegram_photo_price(self):
        # перезаписуємо назуву скріншота, щоб не надсилався попердній якщо такий був
        self.screenshot_name = None
        self.fetch_coins_with_changed_price()
        self._send_telegram_photo()


    def send_telegram_message_price(self):
        message = self.fetch_coins_with_changed_price()
        self._send_telegram_message(message)


    def run_scheduler(self):
        # schedule.every(1).minutes.do(lambda: executor.submit(send_telegram_message, BOT_TOKEN, CHAT_ID, TWO_PERC))
        logging.info(f"Executing task 'send telegram message' for price changed over {self.percentage}%")
        logging.info("I'm running on thread %s" % threading.current_thread())
        schedule.every(1).minutes.do(self.send_telegram_photo_price)

        while True:
            schedule.run_pending()
            time.sleep(1)


class BotIO(TelegramBot):

    def __init__(self, percentage_io=CHG_IO):
        super().__init__()
        self.percentage = percentage_io
        self.screenshot_name = None
        self.filters = 'IO'

    def _apply_filter_io(self, page: Page):
        logging.info("Selecting 'Open Interest'")
        page.get_by_role("button", name="Open Interest").click()
        page.get_by_role("button", name="OI Change (15m)").click()
        page.get_by_role("textbox", name="-100%").fill(self.percentage)
        page.get_by_role("button", name="OI Chg (15m,$)").click()
        page.get_by_role("textbox", name="$0").fill("$400000")
        page.get_by_role("button", name="Apply Filter").click()
        logging.info("Selecting 'Close'")
        page.get_by_role("button", name="Close").click()
        logging.info(f"Filter for IO over {self.percentage}% was succssesfuly applied")


    def fetch_coins_with_changed_io(self) -> str:
        with sync_playwright() as playwright:
            page = self._set_page_and_go_to_coinglass(playwright)
            self._apply_filter_io(page)
            coins_for_message = self._get_data_from_table(page)
            if coins_for_message:
                self._append_coins_data_to_file(coins_for_message)
                self._get_coins_data_screenshot(page)

            return coins_for_message

    def send_telegram_photo_io(self):
        # перезаписуємо назуву скріншота, щоб не надсилався попердній якщо такий був
        self.screenshot_name = None
        self.fetch_coins_with_changed_io()
        self._send_telegram_photo()


    def send_telegram_message_io(self):
        message = self.fetch_coins_with_changed_io()
        self._send_telegram_message(message)


    def run_scheduler(self):
        # schedule.every(1).minutes.do(lambda: executor.submit(send_telegram_message, BOT_TOKEN, CHAT_ID, TWO_PERC))
        logging.info(f"Executing task 'send telegram message' for IO over {self.percentage}%")
        logging.info("I'm running on thread %s" % threading.current_thread())
        schedule.every(1).minutes.do(self.send_telegram_message_io)

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    # executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    bot_price = BotPrice(percentage_price='1', interval=15)
    bot_price.run_scheduler()
    

    # with ThreadPoolExecutor(max_workers=2) as executor:
    #     try:
    #         executor.submit(bot_1.run_scheduler)
    #         # executor.submit(bot_2.run_scheduler)
    #     except KeyboardInterrupt:
    #         executor.shutdown()
