// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "../FlashloanBorrowerDev.sol";

contract FlashloanExposed is FlashloanBorrowerDev(0xdc13687554205E5b89Ac783db14bb5bba4A1eDaC, 0x60aE616a2155Ee3d9A68541Ba4544862310933d4) {

  
       
    function _swap_from_AVAX(
        address tokenToRepay,
        uint256 borrowedTokenAmountToRepay,
        uint256 flashBorrowAmount) 
        external returns (uint256)
    {
        return swap_from_AVAX(
            tokenToRepay,
            borrowedTokenAmountToRepay,
            flashBorrowAmount
        );

    }

    function _swap_to_AVAX(
        address tokenFrom,
        uint256 amountFrom) 
        external returns (uint256)
        {
        return swap_to_AVAX(
            tokenFrom,
            amountFrom);
        }

    function _swap_token_to_token(
        address fromToken,
        address toToken,
        uint256 fromTokenAmount) 
        external returns (uint256)
        {
            return swap_token_to_token(
            fromToken,
            toToken,
            fromTokenAmount);
        }


    function _liquidate_borrow(
        address borrowerToLiquidate,
        address JTokenCollateralToSeize,
        address tokenToRepay,
        uint256 borrowedTokenAmountToRepay,
        address borrowedJTokenAddress) 
        external returns (uint256)

        {
            return liquidate_borrow(
            borrowerToLiquidate,
            JTokenCollateralToSeize,
            tokenToRepay,
            borrowedTokenAmountToRepay,
            borrowedJTokenAddress);
        }


}

