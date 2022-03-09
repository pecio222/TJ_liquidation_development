from brownie import FlashloanBorrowerDev
from eth_account import Account
from scripts.helpful_scripts import get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens
from brownie import interface, config, network, chain, accounts
from web3 import Web3
from pprint import pprint
import time
import pytest

from scripts.helpful_test_scripts import forward_in_time, get_account_liquidity, swap, mint_and_borrow #, get_account_data, forward_in_time

#network.connect("avax-main-fork11077410")








def test_underwater_setup(web3):
    
    #setup assets on account, that will be liquidated by swapping avax to any tokens 
    to_token = 'jWBTC'
    borrow_token = 'jDAI'
    
    account0 = accounts[0]
    destination_token = config['addresses']['TOKENS'][to_token]
    destination_token_interface = interface.IERC20(destination_token)
    balance1 = destination_token_interface.balanceOf(account0, {"from": account0})
    swap(8, to_token, account0, web3)
    balance2 = destination_token_interface.balanceOf(account0, {"from": account0})
    #assert that token swapped successfully
    assert balance1 < balance2
    
    #setup minting JToken
    borrow_token_adr = config['addresses']['TOKENS'][borrow_token]
    borrow_token_interface = interface.IERC20(borrow_token_adr)  
    balance_before_borrow = borrow_token_interface.balanceOf(account0, {"from": account0})
    mint_and_borrow(to_token, balance2/10**config['addresses']['DECIMALS'][to_token], borrow_token)
    balance3 = destination_token_interface.balanceOf(account0, {"from": account0})
    assert balance3/balance2 < 0.001, "tokens weren't deposited successfully"
    balance_after_borrow = borrow_token_interface.balanceOf(account0, {"from": account0})
    assert balance_after_borrow > balance_before_borrow, "tokens weren't borrowed successfully"

    #simulate going underwater - wait x days and accure interest
    forward_in_time(10)
    update1 = config['addresses']['jADDRESS'][to_token]
    interface.JErc20Interface(update1).exchangeRateCurrent({'from': account0})
    update2 = config['addresses']['jADDRESS'][borrow_token]
    interface.JErc20Interface(update2).exchangeRateCurrent({'from': account0})

    liquidity = get_account_liquidity(account0)
    print(liquidity)

    #assert, that account is underwater after x days
    assert liquidity[2] > 0, "account is not underwater"


def contract():
    #account = get_account()
    # deploy contract
    flashloanborrowerdev = FlashloanBorrowerDev.deploy(
        config['addresses']['CONTRACTS']['joetroller'],
        config['addresses']['CONTRACTS']['joerouter'],
        {'from': accounts[1]})
    accounts[1].transfer(flashloanborrowerdev, 1*10**18)
    print(f"flashloanborrowerdev address: {flashloanborrowerdev}")

    return flashloanborrowerdev


def test_flashloan_liquidation(contract, web3):


    #INTERFACES READY TO DEBUGGING
    to_token = 'jWBTC'
    borrow_token = 'jDAI'
    
    account0 = accounts[0]
    destination_token = config['addresses']['TOKENS'][to_token]
    destination_token_interface = interface.IERC20(destination_token)
    borrow_token_adr = config['addresses']['TOKENS'][borrow_token]
    borrow_token_interface = interface.IERC20(borrow_token_adr)  
    wavax_adr = config['addresses']['TOKENS']['jWAVAX']
    wavax_inter = interface.IWAVAX(wavax_adr)
    joe_router_adr = config['addresses']['CONTRACTS']['joerouter']
    joer_inter = interface.IJoeRouter01(joe_router_adr)
    joetroll_adr = config['addresses']['CONTRACTS']['joetroller']
    joer_inter = interface.JoetrollerInterface(joetroll_adr)




    chosen_tokens = {'address': accounts[0], 
                'repay_amount': 370 / 2, 
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



def main():
    # to_token = 'jWBTC'
    # borrow_token = 'jDAI'
    
    # destination_token = config['addresses']['TOKENS'][to_token]
    # destination_token_interface = interface.IERC20(destination_token)
    # borrow_token_adr = config['addresses']['TOKENS'][borrow_token]
    # borrow_token_interface = interface.IERC20(borrow_token_adr)  
    # wavax_adr = config['addresses']['TOKENS']['jWAVAX']
    # wavax_inter = interface.IWAVAX(wavax_adr)
    # joe_router_adr = config['addresses']['CONTRACTS']['joerouter']
    # joer_inter = interface.IJoeRouter01(joe_router_adr)
    # joetroll_adr = config['addresses']['CONTRACTS']['joetroller']
    # joer_inter = interface.JoetrollerInterface(joetroll_adr)
    web3 = connect_to_ETH_provider()
    test_underwater_setup(web3)

    contract_depl = contract()
    test_flashloan_liquidation(contract_depl, web3)