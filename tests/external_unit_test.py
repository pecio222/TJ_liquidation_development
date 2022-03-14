from brownie import FlashloanBorrowerDev
from brownie import FlashloanExposed
from eth_account import Account
from scripts.helpful_scripts import get_account, connect_to_ETH_provider, ask_graphql, get_underwater_accounts, choose_tokens_to_seize_and_repay, get_account_tokens
from scripts.helpful_test_scripts import forward_in_time, get_account_liquidity, swap, mint_and_borrow, mock_get_account_tokens #, get_account_data, forward_in_time
from brownie import interface, config, network, chain, accounts, reverts, exceptions, convert
from web3 import Web3
from pprint import pprint
import time
import pytest
import eth_abi

@pytest.fixture
def web3():
    web3 = connect_to_ETH_provider()
    return web3

@pytest.fixture
def account():
    return get_account(1)



@pytest.fixture
def contract1(account):
    # deploy contract
    flashloanborrowerdev = FlashloanBorrowerDev.deploy(
        config['addresses']['CONTRACTS']['joetroller'],
        config['addresses']['CONTRACTS']['joerouter'],
        {'from': account})
    #fund contract with gas
    account.transfer(flashloanborrowerdev, 0.01*10**18)
    print(f"flashloanborrowerdev address: {flashloanborrowerdev}")

    return flashloanborrowerdev


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


def test_flashloan_onlyowner(contract1):
    #ARRANGE
    flashloanBorrowerr = contract1

    chosen_tokens = {'address': '0xd23d1c87af3147608cd56f1c90d41ffa8469be97', 
                'repay_amount': 13507.24435048959, 
                'repay_token': 'jUSDC', 
                'max_seize_USD_value': 35720.60254979458, 
                'seize_token': 'jWBTC'}
    #ACT + ASSERT


    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.doFlashloan([config['addresses']['jADDRESS']['jAVAX'],
            config['addresses']['TOKENS']['jAVAX'],
            config['addresses']['TOKENS'][chosen_tokens['repay_token']], #tokenToRepay, 
            chosen_tokens['address'], #borrowerToLiquidate,
            config['addresses']['jADDRESS'][chosen_tokens['seize_token']], #JTokenCollateralToSeize,
            config['addresses']['TOKENS'][chosen_tokens['seize_token']], #underlyingCollateral,
            config['addresses']['jADDRESS'][chosen_tokens['repay_token']], #borrowedJTokenAddress,
            config['addresses']['PAIRS'][chosen_tokens['seize_token']] #joepair
            ],
            1 * 10 ** 18,
            0,
        
        {'from': accounts[8]})


def test_withdraw_AVAX_onlyowner(contract1, account):
    #ARRANGE
    flashloanBorrowerr = contract1
    amount_avax = 30 * 10 ** 18
    balance_avax_contract_before = flashloanBorrowerr.balance()
    account.transfer(flashloanBorrowerr, amount_avax)
    balance_avax_contract_after = flashloanBorrowerr.balance()
    assert balance_avax_contract_after > balance_avax_contract_before

    #ACT + ASSERT
    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.withdrawAVAX(balance_avax_contract_after, {'from': accounts[8]})
    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.withdrawAVAX(balance_avax_contract_after, {'from': accounts[3]})

    #ASSERT
    balance_avax_contract_after_withdrawal = flashloanBorrowerr.balance()
    assert balance_avax_contract_after_withdrawal == balance_avax_contract_after
    

def test_withdraw_AVAX(contract1, account):
    
    #ARRANGE
    flashloanBorrowerr = contract1
    amount_avax = 30 * 10 ** 18
    balance_avax_contract_before = flashloanBorrowerr.balance()
    account.transfer(flashloanBorrowerr, amount_avax)
    balance_avax_contract_after = flashloanBorrowerr.balance()
    assert balance_avax_contract_after > balance_avax_contract_before

    #ACT
    flashloanBorrowerr.withdrawAVAX(balance_avax_contract_after, {'from': account})


    #ASSERT
    assert flashloanBorrowerr.balance() == 0


@pytest.mark.parametrize("token", ('jWETH', 'jUSDC'))
def test_withdraw_ERC20(contract1, account, token, web3):
    #ARRANGE
    #fund contract with parametrized token
    flashloanBorrowerr = contract1
    avax_amount_to_swap = 55
    token_adr = config['addresses']['TOKENS'][token]
    swap(avax_amount_to_swap, token, account, web3)
    token_interface = interface.IERC20(token_adr)
    balance_account = token_interface.balanceOf(account, {"from": account})
    balance_token_contract_before = token_interface.balanceOf(flashloanBorrowerr, {"from": account})
    token_interface.transfer(flashloanBorrowerr, balance_account, {"from": account})

    balance_token_contract_after = token_interface.balanceOf(flashloanBorrowerr, {"from": account})
    assert balance_token_contract_after > balance_token_contract_before
    assert balance_account == balance_token_contract_after

    #ACT
    flashloanBorrowerr.withdrawToken(token_adr, balance_account, {"from": account})

    #ASSERT
    balance_token_contract_after_withdrawal = token_interface.balanceOf(flashloanBorrowerr, {"from": account})
    balance_account_after_withdrawal = token_interface.balanceOf(account, {"from": account})
    assert balance_token_contract_after_withdrawal == 0
    assert balance_account_after_withdrawal == balance_account


@pytest.mark.parametrize("token", ('jWETH', 'jUSDC'))
def test_withdraw_ERC20_onlyowner(contract1, account, token, web3):
    #ARRANGE
    #fund contract with parametrized token
    flashloanBorrowerr = contract1
    avax_amount_to_swap = 55
    token_adr = config['addresses']['TOKENS'][token]
    swap(avax_amount_to_swap, token, account, web3)
    token_interface = interface.IERC20(token_adr)
    balance_account = token_interface.balanceOf(account, {"from": account})
    balance_token_contract_before = token_interface.balanceOf(flashloanBorrowerr, {"from": account})
    token_interface.transfer(flashloanBorrowerr, balance_account, {"from": account})

    balance_token_contract_after = token_interface.balanceOf(flashloanBorrowerr, {"from": account})
    assert balance_token_contract_after > balance_token_contract_before
    assert balance_account == balance_token_contract_after

    #ACT + ASSERT
    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.withdrawToken(token_adr, balance_account, {"from": accounts[3]})
    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.withdrawToken(token_adr, balance_account, {"from": accounts[8]})

    #ASSERT
    balance_token_contract_after_withdrawal = token_interface.balanceOf(flashloanBorrowerr, {"from": account})
    balance_account_after_withdrawal = token_interface.balanceOf(account, {"from": account})
    assert balance_token_contract_after_withdrawal == balance_account
    assert balance_account_after_withdrawal == 0

 
def test_recieve(contract1):
    #ARRANGE
    flashloanBorrowerr = contract1
    amount_avax = 30 * 10 ** 18
    balance_avax_contract_before = flashloanBorrowerr.balance()

    #ACT
    #fund contract with required AVAX
    accounts[0].transfer(flashloanBorrowerr, amount_avax)
    balance_avax_contract_after = flashloanBorrowerr.balance()

    #ASSERT
    assert balance_avax_contract_after > balance_avax_contract_before


@pytest.fixture
def data_encoded():
    #data = eth_abi.encode_abi([('address', 'address', 'address', 'address', 'address', 'address', 'address', 'address'), 'uint256', 'uint256', 'int256'], [
    data = eth_abi.encode_abi(['address[]', 'uint256', 'uint256', 'int256'], [   
        (config['addresses']['TOKENS']['jAVAX'], 
        config['addresses']['TOKENS']['jAVAX'],
        config['addresses']['jADDRESS']['jAVAX'],
        config['addresses']['jADDRESS']['jAVAX'],
        config['addresses']['jADDRESS']['jAVAX'],
        config['addresses']['jADDRESS']['jAVAX'],
        config['addresses']['jADDRESS']['jAVAX'],
        config['addresses']['jADDRESS']['jAVAX']),
        1 * 10 ** 18,
        1 * 10 ** 18,
        0])
    return data

def test_onFlashLoan_untrusted_sender(contract1, account, data_encoded):
    flashloanBorrowerr = contract1


    with reverts("untrusted message sender"):
        flashloanBorrowerr.onFlashLoan(
            flashloanBorrowerr,
            config['addresses']['TOKENS']['jAVAX'],
            1 * 10 ** 18,
            0.0003 * 1 * 10 ** 18,
            data_encoded,
            {"from": account}
            )

def test_onFlashLoan_untrusted_initiator(contract1, account, data_encoded):
    flashloanBorrowerr = contract1


    with reverts("FlashBorrower: Untrusted loan initiator"):
        flashloanBorrowerr.onFlashLoan(
            accounts[9], #untrusted initiator, should be flashloanBorrowerr
            config['addresses']['TOKENS']['jAVAX'],
            1 * 10 ** 18,
            0.0003 * 1 * 10 ** 18,
            data_encoded,
            {"from": config['addresses']['jADDRESS']['jAVAX']}
            )


def test_Ownable_renounce(contract1, account):
    flashloanBorrowerr = contract1
    
    balance_avax_contract = flashloanBorrowerr.balance()
    assert flashloanBorrowerr.owner() == account, "this account wasn't owner in the first place, try again"
    flashloanBorrowerr.renounceOwnership()
    with reverts("Ownable: caller is not the owner"):
            flashloanBorrowerr.withdrawAVAX(balance_avax_contract, {'from': account})
    
    assert flashloanBorrowerr.owner() != account, "contract didn't change owner"


def test_Ownable_transfer(contract1, account):
    new_owner = accounts[8]
    flashloanBorrowerr = contract1
    flashloanBorrowerr.transferOwnership(new_owner, {'from': account})
    balance_avax_contract = flashloanBorrowerr.balance()
    with reverts("Ownable: caller is not the owner"):
            flashloanBorrowerr.withdrawAVAX(balance_avax_contract, {'from': account})
    assert flashloanBorrowerr.owner() == new_owner


def test_Ownable_owner(contract1, account):
    flashloanBorrowerr = contract1
    owner = flashloanBorrowerr.owner()
    assert owner == account


def test_Ownable_transfer_onlyOwner(contract1, account):
    new_owner = accounts[8]
    flashloanBorrowerr = contract1
    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.transferOwnership(new_owner, {'from': accounts[8]})


def test_Ownable_renounce_onlyOwner(contract1, account):
    flashloanBorrowerr = contract1
    with reverts("Ownable: caller is not the owner"):
        flashloanBorrowerr.renounceOwnership({'from': accounts[8]})


def test_Ownable_transfer_to0(contract1, account):
    new_owner = "0x0000000000000000000000000000000000000000"
    flashloanBorrowerr = contract1
    with reverts("Ownable: new owner is the zero address"):
        flashloanBorrowerr.transferOwnership(new_owner, {'from': account})
    assert flashloanBorrowerr.owner() == account