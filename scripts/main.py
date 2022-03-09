from brownie import FlashloanBorrowerDev
from eth_account import Account
from scripts.helpful_scripts import get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens
from brownie import interface, config, network, chain, accounts
from web3 import Web3
from pprint import pprint
import time


def main():
    web3 = connect_to_ETH_provider()
    account = get_account()

    if config['addresses']['CONTRACTS']['flashloanborrower'] == 'TODO':
        # deploy contract to interact if not yet deployed
        flashloanborrowerdev = FlashloanBorrowerDev.deploy(
            config['addresses']['CONTRACTS']['joetroller'],
            config['addresses']['CONTRACTS']['joerouter'],
            {'from': account})
    else:
        flashloanborrowerdev = config['addresses']['CONTRACTS']['flashloanborrower']
    print(f"flashloanborrowerdev address: {flashloanborrowerdev}")

    #while True:
    underwater_accounts = get_underwater_accounts()
    pprint(underwater_accounts)
    
    for account in underwater_accounts:
        tokens_of_underwater_account = get_account_tokens(account)
        chosen_tokens = choose_tokens_to_seize_and_repay(
            tokens_of_underwater_account)
        print(chosen_tokens)
    time.sleep(5)



if __name__ == "__main__":

    main()
