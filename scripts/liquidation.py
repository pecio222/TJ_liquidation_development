from brownie import FlashloanBorrowerDev
from eth_account import Account
from scripts.helpful_scripts import decide_native, get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens
from scripts.helpful_test_scripts import forward_in_time, get_account_liquidity, swap, mint_and_borrow, mock_get_account_tokens #, get_account_data, forward_in_time
from brownie import interface, config, network, chain, accounts
from web3 import Web3
from pprint import pprint
import time
import pytest


def test_underwater_setup(web3, supply_borrow_tokens):
    
    #setup assets on account, that will be liquidated by swapping avax to any tokens 
    supply_token = supply_borrow_tokens[0]
    borrow_token = supply_borrow_tokens[1]
    
    amount_to_swap_supply = 20
    account0 = accounts[0]

    destination_token = config['addresses']['TOKENS'][supply_token]
    destination_token_interface = interface.IERC20(destination_token)
    balance1 = destination_token_interface.balanceOf(account0, {"from": account0})
    if supply_token != 'jAVAX':
        swap(amount_to_swap_supply, supply_token, account0, web3)
    elif supply_token == 'jAVAX':
        destination_token_interface = interface.IWAVAX(destination_token)
        destination_token_interface.deposit({"from": account0, 'value': amount_to_swap_supply * 10 ** 18})
        


    balance2 = destination_token_interface.balanceOf(account0, {"from": account0})
    assert balance1 < balance2, "tokens weren't swapped successfully"

    
    #setup minting JToken
    borrow_token_adr = config['addresses']['TOKENS'][borrow_token]
    borrow_token_interface = interface.IERC20(borrow_token_adr)  
    balance_before_borrow = borrow_token_interface.balanceOf(account0, {"from": account0})
    mint_and_borrow(supply_token, balance2, borrow_token)
    balance3 = destination_token_interface.balanceOf(account0, {"from": account0})
    if supply_token == borrow_token:
        assert balance3/balance2 < 0.801, "tokens weren't deposited successfully"
    else:   
        assert balance3/balance2 < 0.001, "tokens weren't deposited successfully"

    
    balance_after_borrow = borrow_token_interface.balanceOf(account0, {"from": account0})

    if supply_token == borrow_token:
        assert balance_after_borrow/balance_before_borrow < 0.801, "tokens weren't borrowed successfully"
    else:
        assert balance_after_borrow > balance_before_borrow, "tokens weren't borrowed successfully"

    #simulate going underwater - wait x days and accure interest
    forward_in_time(100)

    update1 = config['addresses']['jADDRESS'][supply_token]
    interface.JErc20Interface(update1).exchangeRateCurrent({'from': account0})
    update2 = config['addresses']['jADDRESS'][borrow_token]
    interface.JErc20Interface(update2).exchangeRateCurrent({'from': account0})

    liquidity = get_account_liquidity(account0)
    print(liquidity)

    #assert, that account is underwater after x days
    #sometimes it's possible, that interest on borrowed token is lower than interest on supplied token - never will be liquidated
    assert liquidity[2] > 0, "account is not underwater"



def main():
    # web3 = connect_to_ETH_provider()

    # supply_borrow_tokens = ['jDAI', 'jUSDC']
    # #test_underwater_setup(web3, supply_borrow_tokens)
    # #test_underwater_setup(web3, supply_borrow_tokens)
    # #forward_in_time(100)
    # tokens = ['jAVAX', 'jWETH', 'jWBTC', 'jUSDC', 'jUSDT', 'jDAI', 'jLINK', 'jMIM', 'jXJOE']
    # tokens_of_underwater_account=mock_get_account_tokens(tokens)

    # chosen_tokens = choose_tokens_to_seize_and_repay(
    #         tokens_of_underwater_account)
    # print(chosen_tokens['address'])
    # print(chosen_tokens['repay_amount'])
    # print(chosen_tokens['repay_token'])
    # print(chosen_tokens['max_seize_USD_value'])
    # print(chosen_tokens['seize_token'])
    trans1_adr = '0x770ddb78572c339228a82579b4d30fae71acb0f5098884800bb052f5e289b012'
    flashloan = chain.get_transaction(trans1_adr)
    # print("info:")
    # print(flashloan.info())
    # print("error:")
    # print(flashloan.error())
    # print("traceback:")
    # print(flashloan.traceback())
    # # print("trace")
    # # print(flashloan.trace)
    # print("call trace")
    # print(flashloan.call_trace())

    if 'LiquidateBorrow' in flashloan.events:
        event0 = flashloan.events['LiquidateBorrow'][0]
        print(flashloan.events['LiquidateBorrow'])

        liquidator = event0['liquidator']
        borrower = event0['borrower']
        repayAmount = event0['repayAmount']
        jTokenCollateral = event0['jTokenCollateral']
        seizeTokens = event0['seizeTokens']
        print(liquidator)
        print(borrower)
        print(repayAmount)
        print(jTokenCollateral)
        print(seizeTokens)
        
    else:
        print("failed probably")

    


