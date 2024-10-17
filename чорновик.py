class TelegramBot:

    def __init__(self):
        self.bot_token = 12358
        self.chat_id = 15588
        self.percentage = None
        self.screenshot_name = None
        
class BotIo(TelegramBot):
    def __init__(self, perc_io):
        super().__init__()
        self.percentage = perc_io
        self.screenshot_name = 'h'
        self.filter = 'IO'
        

    def get_screenshot_name(self):
        self.screenshot_name = 'screenshot name'
        

botio = BotIo(perc_io='5')

print(botio.percentage)
print(botio.screenshot_name)
botio.get_screenshot_name()
print(botio.screenshot_name)
