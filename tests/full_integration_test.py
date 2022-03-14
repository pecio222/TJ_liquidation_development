from brownie import FlashloanBorrowerDev
from eth_account import Account
from scripts.helpful_scripts import decide_native, get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens
from scripts.helpful_test_scripts import forward_in_time, get_account_liquidity, swap, mint_and_borrow, mock_get_account_tokens #, get_account_data, forward_in_time
from brownie import interface, config, network, chain, accounts, reverts, exceptions
from web3 import Web3
from pprint import pprint
import time
import pytest






#set Web3 provider
@pytest.fixture(scope="module", autouse=True)
def web3():
    web3 = connect_to_ETH_provider()
    return web3


# deploy contract
@pytest.fixture
def contract():

    # deploy contract
    flashloanborrowerdev = FlashloanBorrowerDev.deploy(
        config['addresses']['CONTRACTS']['joetroller'],
        config['addresses']['CONTRACTS']['joerouter'],
        {'from': accounts[1]})
    #fund contract with gas
    accounts[1].transfer(flashloanborrowerdev, 2*10**18)
    print(f"flashloanborrowerdev address: {flashloanborrowerdev}")

    return flashloanborrowerdev


#####BELOW FIXTURE COVERS ALL 'isNative' CASES, BUT IS LONGER, SO PLAN ACCORDINGLY#####
@pytest.fixture(scope="function", autouse=False, params=[
    ['jWETH', 'jUSDC'], #isNative = 0
    ['jUSDT', 'jUSDT'], #isNative = 0
    ['jWBTC', 'jAVAX'], #isNative = 1
    ['jXJOE', 'jAVAX'], #isNative = 2
    ['jAVAX', 'jMIM'], #isNative = 3
    ['jAVAX', 'jAVAX'], #isNative = 4
    ['jXJOE', 'jUSDC'] #isNative = 5
    ]) 
#####BELOW FIXTURE DOES NOT COVER ALL 'isNative' CASES, BUT IS FASTER, SO PLAN ACCORDINGLY#####
#@pytest.fixture(scope="module", autouse=False, params=[('jWETH', 'jUSDC')])
def supply_borrow_tokens(request):
    # supply_token = 'jWETH'
    # borrow_token = 'jUSDC'
    supply_token = request.param[0]
    borrow_token = request.param[1]
    return [supply_token, borrow_token]

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass



#swap free avax to requested token
#supply max amount of requested token, borrow max possible amount
#wait 100 days, acccure interest. You will be underwater, if borrowed interest >> supplied interest
@pytest.fixture(scope="function", autouse=True)
def test_underwater_setup(web3, supply_borrow_tokens):
    
    #setup assets on account, that will be liquidated by swapping avax to any tokens 
    supply_token = supply_borrow_tokens[0]
    borrow_token = supply_borrow_tokens[1]
    
    amount_to_swap_supply = 8
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



def test_flashloan_liquidation_full(contract, web3, supply_borrow_tokens, test_underwater_setup):

    tokens_of_underwater_account = mock_get_account_tokens(supply_borrow_tokens)

    chosen_tokens = choose_tokens_to_seize_and_repay(
            tokens_of_underwater_account)
    print(chosen_tokens['address'])
    print(chosen_tokens['repay_amount'])
    print(chosen_tokens['repay_token'])
    print(chosen_tokens['max_seize_USD_value'])
    print(chosen_tokens['seize_token'])


    isNative, flashloanlender, flashloaned_token = decide_native(chosen_tokens)


    print(f"is native {isNative}")
    print(f"flashloanlender {flashloanlender}")
    print(f"flashloaned_token {flashloaned_token}")

    flashloanborrowerdev = contract

    repayAmount = int(0.99* chosen_tokens['repay_amount'] 
                                * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']])

    print(f"repaying amount: {repayAmount}")

    #check balances before transaction
    borrowed_token = config['addresses']['TOKENS'][chosen_tokens['repay_token']]
    borrowed_token_interface = interface.IERC20(borrowed_token)
    flashloanborrower_balance_token_before = borrowed_token_interface.balanceOf(contract, {'from': accounts[1]})
    flashloanborrower_avax_balance_before = contract.balance()
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
            {'from': accounts[1]})
        # print("raising false error to debug")
        # raise exceptions.VirtualMachineError

    except Exception as e:
    #debugging tool outside of tests
        
        blok = web3.eth.get_block(block_identifier=web3.eth.default_block, full_transactions=False)
        trans1_adr = web3.toHex(blok['transactions'][0])
        flashloan = chain.get_transaction(trans1_adr)
        print("info:")
        print(flashloan.info())
        print("error:")
        print(flashloan.error())
        print("traceback:")
        print(flashloan.traceback())
        # print("trace")
        # print(flashloan.trace)
        print("call trace")
        print(flashloan.call_trace())
        print(F"FLASHLOAN {trans1_adr} FAILED with exception {e}")
        raise exceptions.VirtualMachineError

    flashloanborrower_balance_token_after = borrowed_token_interface.balanceOf(contract, {'from': accounts[1]})
    flashloanborrower_avax_balance_after = contract.balance()

    print("info:")
    print(flashloan.info())
    print("error:")
    print(flashloan.error())
    print("traceback:")
    print(flashloan.traceback())
    assert flashloanborrower_avax_balance_after > flashloanborrower_avax_balance_before, "transaction unprofitable"
    print(f"borrowed_token {borrowed_token}")
    print(f"flashloanborrower_balance_token_after {flashloanborrower_balance_token_after}")

    print(f"flashloanborrower_balance_token_before {flashloanborrower_balance_token_before}")
    #does not work for native
    #assert flashloanborrower_balance_token_after == 0, "leftovers from borrowed token are here"

    
    assert flashloanborrower_balance_token_before == 0, "borrowed token was here before liquidation"
