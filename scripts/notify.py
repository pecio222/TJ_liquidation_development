
import json
import requests
from pprint import pprint
from datetime import datetime
import time
import telegram
from discord_webhook import DiscordWebhook
import logging
import logging.config
import yaml



def discord_bot_webhook(message):
  try:
    #test channel
    webhook = DiscordWebhook(url='https://discord.com/api/webhooks/914155708835049472/zCujeIgG9RF88yTRJxCZFV4ccrj1M5VZlaW7Rfw2djyHoxOQpTDlx7x8g_W7uofCMPl6', content=message)

    # main chanell
    # webhook = DiscordWebhook(url='https://discord.com/api/webhooks/913885231369568286/lavwyhLBnMT4Gz5maz41bm5MV2IiQycL0lwJ32RJ4sv5x4uFocpcFSyVgT1aWfxyW_n_', content=message)
    a = webhook.execute(remove_embeds=True)
  except Exception as e:
    print(f'webhook bot died because of {e}\nduring sending msg {message}')



def logger():
    with open('./logging.yaml', 'r') as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)
    logger = logging.getLogger('printer')


def notify_telegram(message):
    with open('telegram_bot/bot_keys.json', 'r') as keys_file:
        k = json.load(keys_file)
        token = k['telegram_token']
        chat_id = k['telegram_chat_id']    
        bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)



