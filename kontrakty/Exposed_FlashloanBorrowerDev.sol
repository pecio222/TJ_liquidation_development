
// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "./FlashloanBorrowerDev.sol";



contract Exposed_FlashloanBorrowerDev is FlashloanBorrowerDev {
    
    
    constructor(address _comptroller, address _joerouter) {
        comptroller = _comptroller;
        joerouter = _joerouter;
        wavax = 0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7;
        priceOracle = 0xd7Ae651985a871C1BC254748c40Ecc733110BC2E;

    }

    function _swap_from_AVAX(
        address JoeRouter,
        address wAVAXToken,
        address JTokenBorrowed,
        uint256 borrowedTokenAmountToRepay,
        uint256 flashBorrowAmount)  external returns (uint256)

        {
            swap_from_AVAX(JoeRouter, wAVAXToken, JTokenBorrowed, borrowedTokenAmountToRepay, flashBorrowAmount);
        }

    function doFlashloan (
        address[] memory joinedAddresses, 
        uint256 borrowedAmountToRepay) external override onlyOwner {

    }
    receive() external override payable {
        emit Received(msg.sender, msg.value);
    }
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) override external returns (bytes32) {
    }
}
