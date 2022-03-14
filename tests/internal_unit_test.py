from brownie import FlashloanBorrowerDev
from brownie import FlashloanExposed, OwnableExposed
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


@pytest.fixture
def contract2(account):
    # deploy contract
    flashloanExposed = FlashloanExposed.deploy({'from': account})
    #fund contract with gas
    account.transfer(flashloanExposed, 0.01*10**18)
    print(f"FlashloanExposed address: {flashloanExposed}")
    return flashloanExposed


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


#add any tokens you want to test from brownie-config
@pytest.mark.parametrize("token_from", ('jWETH', 'jUSDC'))
def test_swap_from_AVAX(contract2, web3, token_from):
    token = token_from
    requested_amount = 1 * 10 ** config['addresses']['DECIMALS'][token]
    flashloanExposed = contract2
    destination_token = config['addresses']['TOKENS'][token]
    destination_token_interface = interface.IERC20(destination_token)
    balance1 = destination_token_interface.balanceOf(flashloanExposed, {"from": accounts[1]})
    joerouter = interface.IJoeRouter01(config['addresses']['CONTRACTS']['joerouter'])
    amountIn, amountOut = joerouter.getAmountsIn(requested_amount, [config['addresses']['TOKENS']['jAVAX'], destination_token])
    #fund contract with required AVAX
    accounts[1].transfer(flashloanExposed, amountIn)


    flashloanExposed._swap_from_AVAX(
        config['addresses']['TOKENS'][token],
        requested_amount,
        2 ** 256 - 1, #full allowance
        {'from': accounts[0]}
        )
    balance2 = destination_token_interface.balanceOf(flashloanExposed, {"from": accounts[1]})
    
    assert balance2 > balance1, "no change in balance made"
    assert balance2 == amountOut


@pytest.mark.parametrize("token_from", ('jWETH', 'jUSDC'))
def test_swap_to_AVAX(contract2, web3, token_from):
    #ARRANGE
    flashloanExposed = contract2
    account = accounts[0]
    avax_amount_to_swap = 55
    swapping_token = config['addresses']['TOKENS'][token_from]
    swap(avax_amount_to_swap, token_from, account, web3)

    #fund contract with token to swap
    from_token_interface = interface.IERC20(swapping_token)
    balance_account = from_token_interface.balanceOf(account, {"from": account})
    from_token_interface.transfer(flashloanExposed, balance_account, {"from": account})
    balance_token_contract_before = from_token_interface.balanceOf(flashloanExposed, {"from": account})
    balance_avax_contract_before = flashloanExposed.balance()

    assert balance_token_contract_before > 0, "token not transfered to contract"

    #ACT
    flashloanExposed._swap_to_AVAX(
        swapping_token,
        balance_account,
        {"from": account}
        )

    #ASSERT
    balance_token_contract_after = from_token_interface.balanceOf(flashloanExposed, {"from": account})
    balance_avax_contract_after = flashloanExposed.balance()
    assert balance_token_contract_after == 0, "token not swapped"
    assert balance_avax_contract_after > balance_avax_contract_before


#providing the same token for 'token_to' and 'token_from' will result in revert
@pytest.mark.parametrize("token_from,token_to", [('jWETH', 'jUSDC'), ('jMIM', 'jWBTC')])
def test_swap_token_to_token(contract2, web3, token_to, token_from):
    #ARRANGE
    #token_from - means token that we will be swapping in contract to token_to
    flashloanExposed = contract2
    account = accounts[0]
    avax_amount_to_swap = 55
    swap_from_token = config['addresses']['TOKENS'][token_from]
    swap_to_token = config['addresses']['TOKENS'][token_to]
    #so in arrange phase we actually swap TO token from
    swap(avax_amount_to_swap, token_from, account, web3)

    #fund contract with token to swap
    to_token_interface = interface.IERC20(swap_to_token)
    from_token_interface = interface.IERC20(swap_from_token)
    balance_account = from_token_interface.balanceOf(account, {"from": account})
    from_token_interface.transfer(flashloanExposed, balance_account, {"from": account})
    balance_token_from_contract_before = from_token_interface.balanceOf(flashloanExposed, {"from": account})
    balance_token_to_contract_before = to_token_interface.balanceOf(flashloanExposed, {"from": account})

    assert balance_token_from_contract_before > 0, "token not transfered to contract"
    assert balance_token_to_contract_before == 0, "contract had token before swap"

    #ACT
    flashloanExposed._swap_token_to_token(
        swap_from_token,
        swap_to_token,
        balance_token_from_contract_before,
        {"from": account}
        )

    #ASSERT
    balance_token_from_contract_after = from_token_interface.balanceOf(flashloanExposed, {"from": account})
    balance_token_to_contract_after = to_token_interface.balanceOf(flashloanExposed, {"from": account})
    assert balance_token_from_contract_after == 0, "token not swapped"
    assert balance_token_to_contract_after > balance_token_to_contract_before


def test_liquidate_borrow_failed(contract2):
    #ARRANGE
    flashloanExposed = contract2
    account = accounts[0]

    with reverts("liquidate borrow failed"):
        flashloanExposed._liquidate_borrow(
            accounts[1],
            config['addresses']['jADDRESS']['jAVAX'],
            config['addresses']['TOKENS']['jAVAX'],
            1 * 10 ** 18,
            config['addresses']['jADDRESS']['jAVAX'], 
            {'from': account}) 


def test_Ownable_transfer(account):
    new_owner = accounts[8]
    owner = OwnableExposed.deploy({'from': account})
    assert owner.owner() == account
    owner.transferOwnership(new_owner)

    assert owner.owner() == new_owner
