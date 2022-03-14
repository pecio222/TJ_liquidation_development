import telegram
#from brownie import config

def notify(message):
    # token = config['telegram']['token']
    # chat_id = config['telegram']['chat_ID']
    token = keys_file['telegram_token']
    chat_id = keys_file['telegram_chat_id']    
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)
