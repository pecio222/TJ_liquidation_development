// SPDX-License-Identifier: MIT

pragma solidity >=0.4.22 <0.6;

interface IJoeBar {
    function enter(uint256 _amount) external;
    function leave(uint256 _share) external;
    function balanceOf(address account) external view returns (uint256);
}