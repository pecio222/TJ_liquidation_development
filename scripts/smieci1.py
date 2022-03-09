from brownie import interface, accounts, config
from scripts.helpful_scripts import connect_to_ETH_provider
from scripts.helpful_test_scripts import forward_in_time, get_account_liquidity, swap, mint_and_borrow #, get_account_data, forward_in_time
#from helpful_scripts import ask_graphql
from pprint import pprint
import requests
import time

def main():
    """mocking price oracles"""

    # price_oracle = '0xd7Ae651985a871C1BC254748c40Ecc733110BC2E'
    # price_interface = interface.PriceOracle(price_oracle)

    # cenaAVAX = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jWAVAX'] , {'from': accounts[0]})
    # cenajWETH = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jWETH'] , {'from': accounts[0]})
    # cenajWBTC = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jWBTC'] , {'from': accounts[0]})
    # cenajUSDC = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jUSDC'] , {'from': accounts[0]})
    # cenajUSDT = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jUSDT'] , {'from': accounts[0]})
    # cenajDAI = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jDAI'] , {'from': accounts[0]})
    # cenajLINK = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jLINK'] , {'from': accounts[0]})
    # cenajMIM = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jMIM'] , {'from': accounts[0]})
    # cenajXJOE = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jXJOE'] , {'from': accounts[0]})
    # cenajUSDCNATIVE = price_interface.getUnderlyingPrice(config['addresses']['jADDRESS']['jUSDCNATIVE'] , {'from': accounts[0]})

    # print(cenaAVAX*10**(-18))
    # print(cenajWETH*10**(-18))
    # print(cenajWBTC*10**(-18)*10**(-10))
    # print(cenajUSDC*10**(-18)*10**(-12))
    # print(cenajUSDT*10**(-18)*10**(-12))
    # print(cenajDAI*10**(-18))
    # print(cenajLINK*10**(-18))
    # print(cenajMIM*10**(-18))
    # print(cenajXJOE*10**(-18))
    # print(cenajUSDCNATIVE*10**(-18)*10**(-12))


    """getting example return dict from get_account_tokens"""
    # def ask_graphql(query):

    #     request = requests.post('https://api.thegraph.com/subgraphs/name/traderjoe-xyz/lending'
    #                             '',
    #                             json={'query': query})
    #     if request.status_code == 200:
    #         return request.json()
    #     else:
    #         time.sleep(0.1)
    #         request = requests.post('https://api.thegraph.com/subgraphs/name/traderjoe-xyz/lending'
    #                                 '',
    #                                 json={'query': query})
    #         if request.status_code == 200:
    #             return request.json()


    # def get_account_tokens(address):
    #     query_underwater_acc_balance_short = """
    #     {{
    #     accounts (where: {{id: "{adr}"}})
    #     {{
    #         id
    #         tokens{{market{{underlyingPriceUSD}},
    #     symbol,
    #     enteredMarket,
    #     jTokenBalance,
    #     storedBorrowBalance,
    #     supplyBalanceUnderlying,
    #     borrowBalanceUnderlying,
    #     }}
    #     }}
    #     }}
    #     """.format(adr=address)

    #     tokens_of_underwater_account = ask_graphql(
    #         query_underwater_acc_balance_short)['data']
    #     return tokens_of_underwater_account


    
    # tokeny = get_account_tokens("0x6bfaa30ed20a83777180e14fcb07bb329e0d9fcc")
    # pprint(tokeny)





    # collateral_amount = graph_account_data['accounts'][0]['tokens'][token]['supplyBalanceUnderlying']
    # token_price = graph_account_data['accounts'][0]['tokens'][token]['market']['underlyingPriceUSD']
    # debt_amount = graph_account_data['accounts'][0]['tokens'][token]['borrowBalanceUnderlying']
    # token_name = graph_account_data['accounts'][0]['tokens'][token]['symbol']


    def test_underwater_setup(web3, supply_borrow_tokens):
        
        #setup assets on account, that will be liquidated by swapping avax to any tokens 
        supply_token = supply_borrow_tokens[0]
        borrow_token = supply_borrow_tokens[1]
        
        account0 = accounts[0]
        destination_token = config['addresses']['TOKENS'][supply_token]
        destination_token_interface = interface.IERC20(destination_token)
        balance1 = destination_token_interface.balanceOf(account0, {"from": account0})
        swap(8, supply_token, account0, web3)
        balance2 = destination_token_interface.balanceOf(account0, {"from": account0})
        #assert that token swapped successfully
        assert balance1 < balance2
        
        #setup minting JToken
        borrow_token_adr = config['addresses']['TOKENS'][borrow_token]
        borrow_token_interface = interface.IERC20(borrow_token_adr)  
        balance_before_borrow = borrow_token_interface.balanceOf(account0, {"from": account0})
        mint_and_borrow(supply_token, balance2/10**config['addresses']['DECIMALS'][supply_token], borrow_token)
        balance3 = destination_token_interface.balanceOf(account0, {"from": account0})
        assert balance3/balance2 < 0.001, "tokens weren't deposited successfully"
        balance_after_borrow = borrow_token_interface.balanceOf(account0, {"from": account0})
        assert balance_after_borrow > balance_before_borrow, "tokens weren't borrowed successfully"

        #simulate going underwater - wait x days and accure interest
        forward_in_time(10)
        #do not accure interest to supplied token - guarantees, that account will be underwater to liquidate
        #sometimes it's possible, that interest of borrowed token is lower than interest on supplied token - never will be liquidated

        # update1 = config['addresses']['jADDRESS'][supply_token]
        # interface.JErc20Interface(update1).exchangeRateCurrent({'from': account0})
        update2 = config['addresses']['jADDRESS'][borrow_token]
        interface.JErc20Interface(update2).exchangeRateCurrent({'from': account0})

        liquidity = get_account_liquidity(account0)
        print(liquidity)



    def mock_get_account_tokens(supply_borrow_tokens):

        tokens_of_underwater_account = {}

        mock_account_tokens = []
        account_checking = accounts[9]
        account_to_check = accounts[0]
        tokens_to_check_list = supply_borrow_tokens #TODO
        for token in range(len(tokens_to_check_list)):
            symbol = tokens_to_check_list[token]

            #get constants
            jtoken_address = config['addresses']['jADDRESS'][symbol]
            decimals = int(config['addresses']['DECIMALS'][symbol])
            price_oracle = config['addresses']['CONTRACTS']['price_oracle']
            jerc20 = interface.JErc20Interface(jtoken_address)

            #get account snapshot for every jtoken in supply_borrow_tokens
            account_snapshot = jerc20.getAccountSnapshot(account_to_check, {'from': account_checking})
            supplyBalanceUnderlying = account_snapshot[1]*10**(-decimals)*account_snapshot[3]*10**(-18)
            borrowBalanceUnderlying = account_snapshot[2]*10**(-decimals)
            price_interface = interface.PriceOracle(price_oracle)
            
            underlyingPriceUSD = price_interface.getUnderlyingPrice(jtoken_address , {'from': account_checking})
            underlyingPriceUSD = underlyingPriceUSD * 10 ** (-18) * 10 ** (decimals - 18)


            #mocked return from lending subgraph - 1 piece from get_account_tokens() function
            
            accounts_tokens =    {'borrowBalanceUnderlying': borrowBalanceUnderlying,
                'enteredMarket': True,
                'jTokenBalance': '0', #not implemented
                'market': {'underlyingPriceUSD': underlyingPriceUSD},
                'storedBorrowBalance': '0', #not implemented
                'supplyBalanceUnderlying': supplyBalanceUnderlying,
                'symbol': symbol}

            mock_account_tokens.append(accounts_tokens)


        # mocked complete return from get_account_tokens() function
        # ready to pass to: graph_account_data['accounts'][0]['tokens'] from function choose_tokens_to_seize_and_repay()
        tokens_of_underwater_account['accounts'] = [
            {'id': str(account_to_check), 
            'tokens': mock_account_tokens
        }]

        return tokens_of_underwater_account


    web3 = connect_to_ETH_provider()
    supply_borrow_tokens = ['jUSDT', 'jDAI']
    test_underwater_setup(web3, supply_borrow_tokens)
    supply_borrow_tokens = ['jWBTC', 'jMIM']
    test_underwater_setup(web3, supply_borrow_tokens)


    supply_borrow_tokens = ['jWBTC', 'jMIM', 'jUSDC', 'jUSDT', 'jDAI']
    mock_account_tokens = mock_get_account_tokens(supply_borrow_tokens)
    pprint(mock_account_tokens)
    


if __name__ == "__main__":
    main()



# def mock_get_account_tokens(web3):
#     account = accounts[0]
#     jWETHadress = config["networks"][network.show_active()]["jweth"]
#     jdaiaddress = config["networks"][network.show_active()]["jdai"]

#     jweth_jtoken = interface.JTokenInterface(jWETHadress)
#     jweth_jerc20 = interface.JErc20Interface(jWETHadress)
#     jdai_jtoken = interface.JTokenInterface(jdaiaddress)
#     jdai_jerc20 = interface.JErc20Interface(jdaiaddress)
    
    
#     account_snapshot_weth = jweth_jerc20.getAccountSnapshot(account, {'from': account})
#     exchange_rate_weth = jweth_jerc20.exchangeRateCurrent({'from': account}).return_value
#     coll_factor_weth = 0.75
#     deposited_balance_weth = account_snapshot_weth[1]*10**(-18)*exchange_rate_weth*10**(-18)
#     borrow_balance_weth = account_snapshot_weth[2]*10**(-18)

#     account_snapshot_jdai = jdai_jerc20.getAccountSnapshot(account, {'from': account})
#     exchange_rate_jdai = jdai_jerc20.exchangeRateCurrent({'from': account}).return_value
#     coll_factor_dai = 0.8
#     deposited_balance_jdai = account_snapshot_jdai[1]*10**(-18)*exchange_rate_jdai*10**(-18)
#     borrow_balance_jdai = account_snapshot_jdai[2]*10**(-18)



#     max_borrowed_weth = deposited_balance_weth * 0.75
#     #health = float(deposited_balance_weth) * coll_factor_weth / float(borrow_balance_weth)
#     joetroller_address = config["networks"][network.show_active()]["joetroller"]
#     joetrollerinterface = interface.JoetrollerInterface(joetroller_address)
#     liquidity = joetrollerinterface.getAccountLiquidity(account)

#     # print(exchange_rate*10**(-18))
#     print(account_snapshot_weth)
#     print(
#         f"token balance[jweth]: {account_snapshot_weth[1]*10**(-8)}\n"
#         f"deposited balance[weth]: {deposited_balance_weth}\n"
#         f"borrow balance[weth]: {borrow_balance_weth}\n"
#         # f"max borrow: {max_borrowed_weth}\n"
#         f"token balance[jdai]: {account_snapshot_jdai[1]*10**(-8)}\n"
#         f"deposited balance[jdai]: {deposited_balance_jdai}\n"
#         f"borrow balance[jdai]: {borrow_balance_jdai}\n"
#         f"error {liquidity[0]} \nliquidity {liquidity[1]*10**(-18)} \nshortfall {liquidity[2]*10**(-18)}"
#         )
