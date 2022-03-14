from brownie import FlashloanBorrowerDev
from eth_account import Account
from scripts.helpful_scripts import decide_native#, discord_bot_webhook
from scripts.helpful_scripts import get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens

import logging
# from logging import config as conffff
from brownie import interface, config, network, chain, accounts
from web3 import Web3
from pprint import pprint
import time
import yaml




def main():
    web3 = connect_to_ETH_provider()
    account = get_account()
    #my logger config is in conflict with brownie config. Sad, no time left to implement.
    # with open('./logging.yaml', 'r') as stream:
    #     config_logger = yaml.load(stream, Loader=yaml.FullLoader)
    # # logging.conffff.dictConfig(config_logger)
    # logger = logging.getLogger('printer')
    if config['networks'][network.show_active()]['flashloanborrower'] == 'TODO':
        # deploy contract to interact if not yet deployed
        flashloanborrowerdev = FlashloanBorrowerDev.deploy(
            config['addresses']['CONTRACTS']['joetroller'],
            config['addresses']['CONTRACTS']['joerouter'],
            {'from': account})
    else:
        flashloanborrowerdev = config['networks'][network.show_active()]['flashloanborrower']
    print(f"flashloanborrowerdev address: {flashloanborrowerdev}")

    #while True:
    underwater_accounts = get_underwater_accounts()
    pprint(underwater_accounts)
    
    for accountsss in underwater_accounts:
        tokens_of_underwater_account = get_account_tokens(accountsss)
        chosen_tokens = choose_tokens_to_seize_and_repay(
                                    tokens_of_underwater_account)
        isNative, flashloanlender, flashloaned_token = decide_native(chosen_tokens)
        repayAmount = int(0.99* chosen_tokens['repay_amount'] 
                                * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']])
        print(f"repaying amount: {repayAmount}")
        borrowed_token = config['addresses']['TOKENS'][chosen_tokens['repay_token']]
        contract_avax_balance_before = flashloanborrowerdev.balance()
        try:
            flashloan = flashloanborrowerdev.doFlashloan(
                [flashloanlender,
                flashloaned_token,
                config['addresses']['TOKENS'][chosen_tokens['repay_token']], #tokenToRepay, 
                chosen_tokens['address'], #borrowerToLiquidate,
                config['addresses']['jADDRESS'][chosen_tokens['seize_token']], #JTokenCollateralToSeize,
                config['addresses']['TOKENS'][chosen_tokens['seize_token']], #underlyingCollateral,
                config['addresses']['jADDRESS'][chosen_tokens['repay_token']], #borrowedJTokenAddress,
                config['addresses']['PAIRS'][chosen_tokens['seize_token']] #joepair
                ],
                repayAmount,
                isNative,
                {'from': account})
            #print('flashloan info:')
            #print(flashloan.info())
            if 'LiquidateBorrow' in flashloan.events and 'my_success' in flashloan.events:
                contract_avax_balance_after = flashloanborrowerdev.balance()
                event0 = flashloan.events['LiquidateBorrow'][0]
                #print(flashloan.events['LiquidateBorrow'])

                liquidator = event0['liquidator']
                borrower = event0['borrower']
                repayAmount = event0['repayAmount']
                jTokenCollateral = event0['jTokenCollateral']
                seizeTokens = event0['seizeTokens']
                profit = contract_avax_balance_after - contract_avax_balance_before
                msg1 = f"liquidator: {liquidator}, borrower: {borrower}\n"
                msg2 = f"repayAmount: {repayAmount * 10 ** (-config['addresses']['DECIMALS'][chosen_tokens['repay_token']])} of token {chosen_tokens['repay_token']}\n"
                msg3 = f"seizeTokens: {seizeTokens * 10 ** (-config['addresses']['DECIMALS'][chosen_tokens['seize_token']])} of token {chosen_tokens['seize_token']}\n"
                msg4 = f"profit: {profit * 10 ** (-18)} AVAX"
                print(msg1)
                print(msg2)
                print(msg3)
                print(msg4)
                msg_notify = msg1 + msg2 + msg3 + msg4
                #notify(msg_notify)
                print("\nBIG SUCCESS EVERYONE HAPPY\n")


            else:
                print("I'm hanging around \nI'm waiting for you \nBut nothing ever happens And I wonder...")

        except Exception as e:
            print("Something bad happened. Pls don't burn my gas.")
            print(f"Exception {e}")




