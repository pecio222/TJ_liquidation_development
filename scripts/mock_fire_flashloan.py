from brownie import config, accounts, interface
from scripts.helpful_test_scripts import get_account_liquidity, forward_in_time

chosen_tokens = {'address': '0xd23d1c87af3147608cd56f1c90d41ffa8469be97', 
                'repay_amount': 13507.24435048959, 
                'repay_token': 'jUSDC', 
                'max_seize_USD_value': 35720.60254979458, 
                'seize_token': 'jWBTC'}

print(chosen_tokens['address'])
print(chosen_tokens['repay_amount'])
print(chosen_tokens['repay_token'])
print(chosen_tokens['max_seize_USD_value'])
print(chosen_tokens['seize_token'])

flashloanborrowerdev = 'adres'

# #modify decimals for PriceOracle function
# decimals_repay = 0
# if config['addresses']['DECIMALS'][chosen_tokens['repay_token']] != 18:
#     decimals_repay = 18 - config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
#     #TODO other borrow than avax

flashBorrowAmount = int(1.01 * chosen_tokens['repay_amount'] 
                            * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']])

if chosen_tokens['repay_token'] == 'jAVAX':
    isNative = 1
    flashloanlender = config['addresses']['jADDRESS']['jUSDC']
    borrow_token = config['addresses']['TOKENS']['jUSDC']
elif chosen_tokens['repay_token'] == 'jXJOE':
    isNative = 2
    flashloanlender = config['addresses']['jADDRESS']['jAVAX']
    borrow_token = config['addresses']['TOKENS']['jAVAX']

else:
    isNative = 0
    flashloanlender = config['addresses']['jADDRESS']['jAVAX']
    borrow_token = config['addresses']['TOKENS']['jAVAX']

print(f"is native = {isNative}")


flashloan = flashloanborrowerdev.doFlashloan(
    [flashloanlender, #flashloanLender, 
    borrow_token, #borrowToken, 
    config['addresses']['TOKENS'][chosen_tokens['repay_token']], #tokenToRepay, 
    chosen_tokens['address'], #borrowerToLiquidate,
    config['addresses']['jADDRESS'][chosen_tokens['seize_token']], #JTokenCollateralToSeize,
    config['addresses']['TOKENS'][chosen_tokens['seize_token']], #underlyingCollateral,
    config['addresses']['jADDRESS'][chosen_tokens['repay_token']], #borrowedJTokenAddress,
    config['addresses']['PAIRS'][chosen_tokens['seize_token']] #joepair
    ],
    #borrowAmount, #TODO jak obliczyć ilość avax do pożyczenia?? chyba już nieważne,
    flashBorrowAmount, #chosen_tokens['repay_amount'] * 10 ** config['addresses']['DECIMALS'][chosen_tokens['repay_token']]
    isNative,
    {'from': accounts[1]}
    )

def main():
    to_token = 'jWBTC'
    borrow_token = 'jDAI'


    account0 = accounts[0]
    liquidity = get_account_liquidity(account0)
    print(liquidity)
    forward_in_time(2)
    update = config['addresses']['jADDRESS'][borrow_token]
    update_token_interface = interface.JErc20Interface(update)
    update_token_interface.exchangeRateCurrent({'from': account0})
    liquidity = get_account_liquidity(account0)
    print(liquidity)
