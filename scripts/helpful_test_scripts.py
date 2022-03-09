from eth_account import Account
#from brownie import JToken
from scripts.helpful_scripts import get_account, connect_to_ETH_provider
from brownie import interface, config, network, chain, accounts
import sys
from web3 import Web3
from pprint import pprint
import time





def swap(amount_avax, to_token, account, web3):
    #account = get_account()
    
    print(f"amount of avax to wavax: {amount_avax}")
    amount_avax = amount_avax * 10 ** 18
    #ADRESY ERC20
    WAVAXadress = config['addresses']['TOKENS']['jWAVAX']
    destination_token = config['addresses']['TOKENS'][to_token]
    joe_router_adr = config['addresses']['CONTRACTS']['joerouter']
    joe_factory = config['addresses']['CONTRACTS']['joefactory']

    #KONTRAKTY
    wavax = interface.IERC20(WAVAXadress)
    destination_token_interface = interface.IERC20(destination_token)
    joerouter = interface.IJoeRouter01(joe_router_adr)

    approve = wavax.approve(joe_router_adr, amount_avax, {"from": account})
    
    balance1 = destination_token_interface.balanceOf(account, {"from": account})
    print(f"{to_token} before swap: {balance1 * config['addresses']['DECIMALS'][to_token]}")
    path = [WAVAXadress, destination_token]
    #chain[-1]['timestamp']
    chain.sleep(0)
    print(chain.time())
    deadline = round(chain.time() + 10000)
    get_output_amount = joerouter.getAmountsOut(amount_avax, path)[1]
    print(get_output_amount)
    swap = joerouter.swapExactAVAXForTokens(get_output_amount, path, account, deadline, {"from": account, "value" : amount_avax})
    swap.wait(1)
    balance2 = destination_token_interface.balanceOf(account, {"from": account})
    print(f"{to_token} after swap: {balance2 * config['addresses']['DECIMALS'][to_token]}")
    balance = wavax.balanceOf(account, {"from": account})
    print(f"wavax after swap: {Web3.fromWei(balance, 'ether')}")


def forward_in_time(days):
    #chain.mine(50)
    sleep = days * 3600 * 24
    chain.sleep(0)
    print(f"current time: {chain.time()} sleeping {sleep}")
    chain.sleep(sleep)
    print(f"current time: {chain.time()}")


def get_account_liquidity(account):
    joetroller_address = config['addresses']['CONTRACTS']['joetroller']
    joetrollerinterface = interface.JoetrollerInterface(joetroller_address)
    liquidity = joetrollerinterface.getAccountLiquidity(account)
    return liquidity


def mint_and_borrow(mint_token, mint_amount, borrow):
    account = accounts[0]
    deposit_jtoken = config['addresses']['jADDRESS'][mint_token]
    deposit_token = config['addresses']['TOKENS'][mint_token]
    borrow_jtoken = config['addresses']['jADDRESS'][borrow]
    borrow_token = config['addresses']['TOKENS'][borrow]

    deposit_amount_dec = mint_amount * 10 ** config['addresses']['DECIMALS'][mint_token]
    

    
    deposit_interface = interface.IERC20(deposit_token)
    deposit_jtoken_interface = interface.JTokenInterface(deposit_jtoken)
    deposit_jerc20_interface = interface.JErc20Interface(deposit_jtoken)
    borrow_jtoken_interface = interface.JTokenInterface(borrow_jtoken)
    borrow_jerc20_interface = interface.JErc20Interface(borrow_jtoken)


    allowed = deposit_interface.allowance(account, deposit_jtoken, {'from': account})
    if allowed == 0:
        print('approving')
        approve_deposit = deposit_interface.approve(deposit_jtoken, 2**256-1, {'from': account})
    else:
        print(f"Allowance: {allowed}")
    
    #ENTER MARKETS
    print("Entering markets")
    joetroller_address = config['addresses']['CONTRACTS']['joetroller']
    joetroller_interface = interface.JoetrollerInterface(joetroller_address)
    enter_markets = joetroller_interface.enterMarkets([deposit_jtoken], {'from': account})
    print(f"return value enter markets: {enter_markets.return_value}")
    
    #DEPOSIT
    deposit_erc20_balance = deposit_interface.balanceOf(account, {'from': account})
    print(f"Balance of {mint_token} [token] before deposit: {deposit_erc20_balance}")
    deposit_jtoken_balance = deposit_jerc20_interface.balanceOf(account, {'from': account})
    print(f"Balance of {mint_token} [jtoken] before deposit: {deposit_jtoken_balance}")

    print(f"depositing: {deposit_amount_dec}")
    minting_tx = deposit_jerc20_interface.mint(deposit_amount_dec, {'from': account})
    
    print(f"mint transaction: {mint_token}")

    deposit_erc20_balance = deposit_interface.balanceOf(account, {'from': account})
    print(f"Balance of {mint_token} [token] after deposit: {deposit_erc20_balance}")
    deposit_jtoken_balance = deposit_jerc20_interface.balanceOf(account, {'from': account})
    print(f"Balance of {mint_token} [jtoken] after deposit: {deposit_jtoken_balance}")
    

    #BORROW
    borrow_amount = int(0.999*get_account_liquidity(account)[1]*10**(config['addresses']['DECIMALS'][borrow]-18))
    print(f"borrowing : {borrow_amount}")
    borrow = borrow_jerc20_interface.borrow(borrow_amount, {'from': account})
    print(f"borrow returns: {borrow.return_value}")
    print(f"borrow transaction: {borrow}")


def mock_get_account_tokens(supply_borrow_tokens):

    tokens_of_underwater_account = {}

    mock_account_tokens = []
    account_checking = accounts[9]
    account_to_check = accounts[0]
    tokens_to_check_list = supply_borrow_tokens


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