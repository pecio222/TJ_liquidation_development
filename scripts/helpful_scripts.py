from brownie import accounts, config, network
import requests
import time
from web3 import Web3
#from discord_webhook import DiscordWebhook

LOCAL_BLOCKCHAIN_ENVIRONMENTS = [
    "development",
    "ganache",
    "hardhat",
    "local-ganache",
    "mainnet-fork",
    "avax-main-fork"
]


def get_account(index=None, id=None):
    if index:
        return accounts[index]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    if id:
        return accounts.load(id)
    if network.show_active() in config["networks"]:
        return accounts.add(config["wallets"]["from_key"])
    return None


def ask_graphql(query):

    request = requests.post('https://api.thegraph.com/subgraphs/name/traderjoe-xyz/lending'
                            '',
                            json={'query': query})
    if request.status_code == 200:
        return request.json()
    else:
        time.sleep(0.1)
        request = requests.post('https://api.thegraph.com/subgraphs/name/traderjoe-xyz/lending'
                                '',
                                json={'query': query})
        if request.status_code == 200:
            return request.json()


def connect_to_ETH_provider():
    # avalanche_url = 'https://api.avax.network/ext/bc/C/rpc' #mainnet
    avalanche_url = 'https://api.avax.network/ext/bc/C/rpc'  # testnet
    web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

    assert web3.isConnected() == True, "web3 not connected"

    return web3


def get_underwater_accounts():

    query_underwater_accounts = """
    {
    accounts(where: {health_gt: 0, health_lt: 1, totalBorrowValueInUSD_gt: 0}) {
        id
    }
    }
    """
    answer_accounts = ask_graphql(query_underwater_accounts)
    list_of_addresses = []
    for account in range(len(answer_accounts['data']['accounts'])):
        list_of_addresses.append(
            answer_accounts['data']['accounts'][account]['id'])
    return list_of_addresses


def choose_tokens_to_seize_and_repay(graph_account_data):
    token_amount = len(graph_account_data['accounts'][0]['tokens'])
    address = graph_account_data['accounts'][0]['id']
    token_names = []
    token_prices = []
    debt_amounts = []
    collateral_amounts = []
    debt_usd_values = []
    collateral_usd_values = []

    for token in range(token_amount):

        #print("token numer {}".format(token))
        collateral_amount = graph_account_data['accounts'][0]['tokens'][token]['supplyBalanceUnderlying']
        token_price = graph_account_data['accounts'][0]['tokens'][token]['market']['underlyingPriceUSD']
        debt_amount = graph_account_data['accounts'][0]['tokens'][token]['borrowBalanceUnderlying']
        token_name = graph_account_data['accounts'][0]['tokens'][token]['symbol']
        entered_market = graph_account_data['accounts'][0]['tokens'][token]['enteredMarket']
        
        token_names.append(token_name)
        token_prices.append(token_price)
        debt_amounts.append(debt_amount)
        collateral_amounts.append(collateral_amount)
        debt_usd_values.append(float(token_price) * float(debt_amount))
        #ignore collateral usd value, when searching for liquidation potential
        if entered_market == True:
            collateral_usd_values.append(float(token_price) * float(collateral_amount))
        else:
            collateral_usd_values.append(0)
        #print("{}: collamm {}, debtamm {}, tokenprice {}".format(
        #    token_name, collateral_amount, debt_amount, token_price))

    print(address)
    print(token_names)
    print(token_prices)
    print(debt_amounts)
    print(collateral_amounts)
    print(debt_usd_values)
    print(collateral_usd_values)

    print(  f"max borrow usd value: {max(debt_usd_values)} on index {debt_usd_values.index(max(debt_usd_values))}"
            f"of coin {token_names[debt_usd_values.index(max(debt_usd_values))]}")
    
    max_debt_repaid = float(max(debt_usd_values))
    max_collateral_seized_usd = float(max(collateral_usd_values))
    index_debt = debt_usd_values.index(max_debt_repaid)
    index_collateral = collateral_usd_values.index(max_collateral_seized_usd)

    if max_debt_repaid / 2 <= max_collateral_seized_usd:
        # print(
        #     f"repaying debt: {max_debt_repaid / 2} USD = {float(debt_amounts[index_debt]) / 2} of {token_names[index_debt]}")
        # print(
        #     f"seizing part of {max_collateral_seized_usd} USD = {collateral_amounts[index_collateral]} of {token_names[index_collateral]}")
        return {'address': address,
                'repay_amount': float(debt_amounts[index_debt]) / 2 * 0.95,
                'repay_token': token_names[index_debt],
                'max_seize_USD_value': max_collateral_seized_usd,
                'seize_token': token_names[index_collateral]
                }

    elif max_debt_repaid / 2 > max_collateral_seized_usd:
        #Possible if 5+ collaterals against borrow concentrated in 1 asset
        #TODO maths too strong
        # print(
        #     f"repaying debt: {max_collateral_seized_usd*0.95} USD = {float((2* max_collateral_seized_usd/max_debt_repaid) * debt_amounts[index_debt]) * 0.95 } of {token_names[index_debt]}")
        # print(
        #     f"seizing PART of {max_collateral_seized_usd} USD = {collateral_amounts[index_collateral]} of {token_names[index_collateral]}")
        return {'address': address,
                'repay_amount': (float(max_collateral_seized_usd/max_debt_repaid) * float(debt_amounts[index_debt]) * 0.95)/2,
                'repay_token': token_names[index_debt],
                'max_seize_USD_value': max_collateral_seized_usd,
                'seize_token': token_names[index_collateral]
                }
    else: print("something went wrong!")




    # mock return: 


def get_account_tokens(address):
    query_underwater_acc_balance_short = """
    {{
    accounts (where: {{id: "{adr}"}})
    {{
        id
        tokens{{market{{underlyingPriceUSD}},
    symbol,
    enteredMarket,
    jTokenBalance,
    storedBorrowBalance,
    supplyBalanceUnderlying,
    borrowBalanceUnderlying,
    }}
    }}
    }}
    """.format(adr=address)

    tokens_of_underwater_account = ask_graphql(
        query_underwater_acc_balance_short)['data']
    return tokens_of_underwater_account


def decide_native(chosen_tokens):
    if chosen_tokens['repay_token'] == chosen_tokens['seize_token'] == 'jAVAX':
        isNative = 4
        flashloanlender = config['addresses']['jADDRESS']['jUSDC']
        flashloaned_token = config['addresses']['TOKENS']['jUSDC']
    elif chosen_tokens['seize_token'] == 'jXJOE' and chosen_tokens['repay_token'] == 'jAVAX':
        isNative = 2
        flashloanlender = config['addresses']['jADDRESS']['jUSDC']
        flashloaned_token = config['addresses']['TOKENS']['jUSDC']
    elif chosen_tokens['seize_token'] == 'jXJOE' and chosen_tokens['repay_token'] != 'jAVAX':
        isNative = 5
        flashloanlender = config['addresses']['jADDRESS']['jAVAX']
        flashloaned_token = config['addresses']['TOKENS']['jAVAX']
    elif chosen_tokens['repay_token'] == 'jAVAX':
        isNative = 1
        flashloanlender = config['addresses']['jADDRESS']['jUSDC']
        flashloaned_token = config['addresses']['TOKENS']['jUSDC']
    elif chosen_tokens['seize_token'] == 'jAVAX':
        isNative = 3
        flashloanlender = config['addresses']['jADDRESS']['jUSDC']
        flashloaned_token = config['addresses']['TOKENS']['jUSDC']
    else:
        isNative = 0
        flashloanlender = config['addresses']['jADDRESS']['jAVAX']
        flashloaned_token = config['addresses']['TOKENS']['jAVAX']

    print(f"is native {isNative}")
    print(f"flashloanlender {flashloanlender}")
    print(f"flashloaned_token {flashloaned_token}")
    return isNative, flashloanlender, flashloaned_token


# def discord_bot_webhook(message):
#   try:
#     #test channel
#     webhook = DiscordWebhook(url='https://discord.com/api/webhooks/914155708835049472/zCujeIgG9RF88yTRJxCZFV4ccrj1M5VZlaW7Rfw2djyHoxOQpTDlx7x8g_W7uofCMPl6', content=message)

#     # main chanell
#     # webhook = DiscordWebhook(url='https://discord.com/api/webhooks/913885231369568286/lavwyhLBnMT4Gz5maz41bm5MV2IiQycL0lwJ32RJ4sv5x4uFocpcFSyVgT1aWfxyW_n_', content=message)
#     a = webhook.execute(remove_embeds=True)
#   except Exception as e:
#     print(f'webhook bot died because of {e}\nduring sending msg {message}')