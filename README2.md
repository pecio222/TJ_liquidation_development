
Introduction
Tests


FlashloanBorrower.sol flowchart:

Less complicated and less detailed flowchart of FlashloanBorrowerDev.sol:

```mermaid
graph TD;
    A(doFlashloan)-->B(Flashloanlender);
    B-->C(onFlashloan);
    C-->|notNative|D(swap_from_AVAX);
    C-->|isNative|D1(swap_from_USDC);
    D1-->E
    D-->E(liquidate_borrow);
    E-->|success|F(balance of jtoken - reddem - balance of token)
    E-->|failed|F2(emit fail)
    F-->|isNative|G1(swap_to_USDC)
    F-->|isXJOE|G2(redeem, swap_to_AVAX)
    F-->|notNative|G(swap_to_AVAX)
    G2-->H(approve spending by Flashloanlender) 
    G1-->H(approve spending by Flashloanlender)
    G-->H(approve spending by Flashloanlender)
    
    H-->|isNative|I(AVAX TO WAVAX)
    H-->|notNative|J
    I-->J(Flashloanlender takes back money, we happy)
```



Full flowchart of FlashloanBorrowerDev.sol:

```mermaid
graph TD;
    0(Python decision to liquidate)-->A(call_doFlashloan)
    A-->B(Flashloanlender);
    B-->C{onFlashloan};
    C-->|isNative == 1 or 2 or 4|D(swap_from_AVAX - to token);
    C-->|isNative == 0 or 5 |D1(swap_from_USDC - to AVAX);
    C-->|isNative == 3 |D2(swap_from_USDC - to token);
    D2-->E
    D1-->E
    D-->E(liquidate_borrow);
    E-->|success|F(balance of jtoken - reddem - balance of token)
    E-->|failed|F2(revert)
    F-->|isNative == 0|G1(swap_to_AVAX)
    F-->|isNative == 1|G3(swap_to_AVAX)
    F-->|isNative == 3 or 4|G4(swap_from_AVAX)
    G4-->H
    G3-->G3A(swap_to_USDC)
    G3A-->H
    F-->|isNative == 2 or 5|G2(redeem, swap_to_AVAX)
    G2-->|isNative == 5|G2A(swap_from_AVAX)
    G2A-->H
    G2-->H(approve spending by Flashloanlender) 
    G1-->H(approve spending by Flashloanlender)
   
    H-->|isNative == 2 or 5|I(AVAX TO WAVAX)
    H-->|isNative == 0, 1, 3, 4|J
    I-->J(Flashloanlender takes back money, we happy)
```



Should be private for now - if you found it, please let me know - first time using github