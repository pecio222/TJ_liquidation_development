from brownie import FlashloanBorrowerDev
from eth_account import Account
from scripts.helpful_scripts import get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens
from scripts.helpful_test_scripts import forward_in_time, get_account_liquidity, swap, mint_and_borrow, mock_get_account_tokens #, get_account_data, forward_in_time
from brownie import interface, config, network, chain, accounts, reverts, exceptions
from web3 import Web3
from pprint import pprint
import time
import pytest


#network.connect("avax-main-fork11077410")

# @pytest.fixture(scope="module", autouse=True)
# def shared_setup(module_isolation):
#     pass


@pytest.fixture(scope="module", autouse=True)
def web3():
    web3 = connect_to_ETH_provider()
    return web3

@pytest.fixture(scope="module", autouse=True)
def supply_borrow_tokens():
    supply_token = 'jWETH'
    borrow_token = 'jMIM'
    return [supply_token, borrow_token]


@pytest.fixture(scope="module", autouse=True)
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
    forward_in_time(100)
#  26334262250430172324
#  474016720507743101832
    update1 = config['addresses']['jADDRESS'][supply_token]
    interface.JErc20Interface(update1).exchangeRateCurrent({'from': account0})
    update2 = config['addresses']['jADDRESS'][borrow_token]
    interface.JErc20Interface(update2).exchangeRateCurrent({'from': account0})

    liquidity = get_account_liquidity(account0)
    print(liquidity)

    #assert, that account is underwater after x days
    #sometimes it's possible, that interest on borrowed token is lower than interest on supplied token - never will be liquidated
    assert liquidity[2] > 0, "account is not underwater"

@pytest.fixture(autouse=True)
def contract():
    #account = get_account()
    # deploy contract
    flashloanborrowerdev = FlashloanBorrowerDev.deploy(
        config['addresses']['CONTRACTS']['joetroller'],
        config['addresses']['CONTRACTS']['joerouter'],
        {'from': accounts[1]})
    #fund contract with gas
    accounts[1].transfer(flashloanborrowerdev, 2*10**18)
    print(f"flashloanborrowerdev address: {flashloanborrowerdev}")

    return flashloanborrowerdev


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


# def test_flashloan_liquidation(contract, web3, supply_borrow_tokens):

#     liquidity = get_account_liquidity(accounts[0])

#     #TODO mock repay amount - works only for stablecoins now
#     chosen_tokens = {'address': accounts[0], 
#                 'repay_amount': 100, 
#                 'repay_token': supply_borrow_tokens[1], 
#                 'max_seize_USD_value': 35720.60254979458, 
#                 'seize_token': supply_borrow_tokens[0]}

#     print(chosen_tokens['address'])
#     print(chosen_tokens['repay_amount'])
#     print(chosen_tokens['repay_token'])
#     print(chosen_tokens['max_seize_USD_value'])
#     print(chosen_tokens['seize_token'])

#     flashloanborrowerdev = contract

#     #modify decimals for PriceOracle function inside contract
#     decimals_repay = 0
#     if config['addresses']['DECIMALS'][chosen_tokens['repay_token']] != 18:
#         decimals_repay = 18 - config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
#         #TODO other borrow than avax

#     flashBorrowAmount = int(chosen_tokens['repay_amount'] 
#                                 * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
#                                 / 10 ** decimals_repay)


#     #check balances before transaction
#     borrowed_token = config['addresses']['TOKENS'][chosen_tokens['repay_token']]
#     borrowed_token_interface = interface.IERC20(borrowed_token)
#     flashloanborrower_balance_token_before = borrowed_token_interface.balanceOf(contract, {'from': accounts[1]})
#     flashloanborrower_avax_balance_before = contract.balance()
#     try:
#         flashloan = flashloanborrowerdev.doFlashloan(
#             [config['addresses']['jADDRESS']['jWAVAX'], #flashloanLender, 
#             config['addresses']['TOKENS']['jWAVAX'], #borrowToken, 
#             config['addresses']['TOKENS'][chosen_tokens['repay_token']], #tokenToRepay, 
#             chosen_tokens['address'], #borrowerToLiquidate,
#             config['addresses']['jADDRESS'][chosen_tokens['seize_token']], #JTokenCollateralToSeize,
#             config['addresses']['TOKENS'][chosen_tokens['seize_token']], #underlyingCollateral,
#             config['addresses']['jADDRESS'][chosen_tokens['repay_token']], #borrowedJTokenAddress,
#             config['addresses']['PAIRS'][chosen_tokens['seize_token']] #joepair
#             ],
#             #borrowAmount, #TODO jak obliczyć ilość avax do pożyczenia?? chyba już nieważne,
#             flashBorrowAmount, #chosen_tokens['repay_amount'] * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
#             {'from': accounts[1]})
    
#     except Exception as e:
#     #debugging tool outside of tests
        
#         blok = web3.eth.get_block(block_identifier=web3.eth.default_block, full_transactions=False)
#         trans1_adr = web3.toHex(blok['transactions'][0])
#         flashloan = chain.get_transaction(trans1_adr)
#         print("info")
#         print(flashloan.info())
#         # print("trace")
#         # print(flashloan.trace)
#         print("call trace")
#         print(flashloan.call_trace(True))
#         print(F"FLASHLOAN {trans1_adr} FAILED with exception {e}")
#         raise exceptions.VirtualMachineError

#     flashloanborrower_balance_token_after = borrowed_token_interface.balanceOf(contract, {'from': accounts[1]})
#     flashloanborrower_avax_balance_after = contract.balance()


#     assert flashloanborrower_avax_balance_after > flashloanborrower_avax_balance_before, "transaction unprofitable"
#     assert flashloanborrower_balance_token_after == flashloanborrower_balance_token_before == 0, "leftovers from borrowed token are here"

def test_flashloan_liquidation_better(contract, web3, supply_borrow_tokens):



    #TODO mock repay amount - works only for stablecoins now
    tokens_of_underwater_account = mock_get_account_tokens(supply_borrow_tokens)


    chosen_tokens = choose_tokens_to_seize_and_repay(
            tokens_of_underwater_account)
    print(chosen_tokens['address'])
    print(chosen_tokens['repay_amount'])
    print(chosen_tokens['repay_token'])
    print(chosen_tokens['max_seize_USD_value'])
    print(chosen_tokens['seize_token'])

    flashloanborrowerdev = contract

    #modify decimals for PriceOracle function inside contract
    decimals_repay = 0
    if config['addresses']['DECIMALS'][chosen_tokens['repay_token']] != 18:
        decimals_repay = 18 - config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
        #TODO other borrow than avax

    flashBorrowAmount = int(0.9* chosen_tokens['repay_amount'] 
                                * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
                                / 10 ** decimals_repay)


    #check balances before transaction
    borrowed_token = config['addresses']['TOKENS'][chosen_tokens['repay_token']]
    borrowed_token_interface = interface.IERC20(borrowed_token)
    flashloanborrower_balance_token_before = borrowed_token_interface.balanceOf(contract, {'from': accounts[1]})
    flashloanborrower_avax_balance_before = contract.balance()
    try:
        flashloan = flashloanborrowerdev.doFlashloan(
            [config['addresses']['jADDRESS']['jWAVAX'], #flashloanLender, 
            config['addresses']['TOKENS']['jWAVAX'], #borrowToken, 
            config['addresses']['TOKENS'][chosen_tokens['repay_token']], #tokenToRepay, 
            chosen_tokens['address'], #borrowerToLiquidate,
            config['addresses']['jADDRESS'][chosen_tokens['seize_token']], #JTokenCollateralToSeize,
            config['addresses']['TOKENS'][chosen_tokens['seize_token']], #underlyingCollateral,
            config['addresses']['jADDRESS'][chosen_tokens['repay_token']], #borrowedJTokenAddress,
            config['addresses']['PAIRS'][chosen_tokens['seize_token']] #joepair
            ],
            #borrowAmount, #TODO jak obliczyć ilość avax do pożyczenia?? chyba już nieważne,
            flashBorrowAmount, #chosen_tokens['repay_amount'] * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
            {'from': accounts[1]})
    
    except Exception as e:
    #debugging tool outside of tests
        
        blok = web3.eth.get_block(block_identifier=web3.eth.default_block, full_transactions=False)
        trans1_adr = web3.toHex(blok['transactions'][0])
        flashloan = chain.get_transaction(trans1_adr)
        print("info")
        print(flashloan.info())
        # print("trace")
        # print(flashloan.trace)
        print("call trace")
        print(flashloan.call_trace(True))
        print(F"FLASHLOAN {trans1_adr} FAILED with exception {e}")
        raise exceptions.VirtualMachineError

    flashloanborrower_balance_token_after = borrowed_token_interface.balanceOf(contract, {'from': accounts[1]})
    flashloanborrower_avax_balance_after = contract.balance()


    assert flashloanborrower_avax_balance_after > flashloanborrower_avax_balance_before, "transaction unprofitable"
    assert flashloanborrower_balance_token_after == flashloanborrower_balance_token_before == 0, "leftovers from borrowed token are here"


def test_flashloan_liquidation_onlyOwner(contract, web3, capsys):

    chosen_tokens = {'address': accounts[0], 
                'repay_amount': 524 / 2, 
                'repay_token': 'jDAI', 
                'max_seize_USD_value': 35720.60254979458, 
                'seize_token': 'jWBTC'}

    print(chosen_tokens['address'])
    print(chosen_tokens['repay_amount'])
    print(chosen_tokens['repay_token'])
    print(chosen_tokens['max_seize_USD_value'])
    print(chosen_tokens['seize_token'])

    flashloanborrowerdev = contract

    #modify decimals for PriceOracle function
    decimals_repay = 0
    if config['addresses']['DECIMALS'][chosen_tokens['repay_token']] != 18:
        decimals_repay = 18 - config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
        #TODO other borrow than avax

    flashBorrowAmount = int(chosen_tokens['repay_amount'] 
                                * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
                                / 10 ** decimals_repay)
    
    with reverts("Ownable: caller is not the owner"):
            flashloan = flashloanborrowerdev.doFlashloan(
            [config['addresses']['jADDRESS']['jWAVAX'], #flashloanLender, 
            config['addresses']['TOKENS']['jWAVAX'], #borrowToken, 
            config['addresses']['TOKENS'][chosen_tokens['repay_token']], #tokenToRepay, 
            chosen_tokens['address'], #borrowerToLiquidate,
            config['addresses']['jADDRESS'][chosen_tokens['seize_token']], #JTokenCollateralToSeize,
            config['addresses']['TOKENS'][chosen_tokens['seize_token']], #underlyingCollateral,
            config['addresses']['jADDRESS'][chosen_tokens['repay_token']], #borrowedJTokenAddress,
            config['addresses']['PAIRS'][chosen_tokens['seize_token']] #joepair
            ],
            #borrowAmount, #TODO jak obliczyć ilość avax do pożyczenia?? chyba już nieważne,
            flashBorrowAmount, #chosen_tokens['repay_amount'] * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
            {'from': accounts[2]})






