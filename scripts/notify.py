import telegram
#from brownie import config

def notify(message):
    keys_file = {"telegram_token": "2130519712:AAHrFM8PN0vPnBH7-7CJE_Dyja9RCsVj5aY",
    "telegram_chat_id": "1689014697"}
    # token = config['telegram']['token']
    # chat_id = config['telegram']['chat_ID']
    token = keys_file['telegram_token']
    chat_id = keys_file['telegram_chat_id']    
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id=chat_id, text=message)



def main():
    notify("aaa")


main()