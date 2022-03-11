// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "./ERC3156FlashLenderInterface.sol";
import "./ERC3156FlashBorrowerInterface.sol";
import "./Ownable.sol";

interface Comptroller {
    function isMarketListed(address cTokenAddress) external view returns (bool);
}

interface ERC20 {
    function approve(address spender, uint256 amount) external;
    function allowance(address owner, address spender) external view returns (uint256);
    function deposit() external payable;
    function transfer(address to, uint value) external returns (bool);
    function withdraw(uint) external;
    function balanceOf(address account) external view returns (uint256);
}



interface PriceOracle {
    /**
     * @notice Get the underlying price of a jToken asset
     * @param jToken The jToken to get the underlying price of
     * @return The underlying asset price mantissa (scaled by 1e18).
     *  Zero means the price is unavailable.
     */
    function getUnderlyingPrice(address jToken) external view returns (uint256);
}

interface JTokenInterface{
}

interface IWAVAX {
    function deposit() external payable;
    function withdraw(uint wad) external;
    event  Approval(address indexed src, address indexed guy, uint wad);
    event  Transfer(address indexed src, address indexed dst, uint wad);
    event  Deposit(address indexed dst, uint wad);
    event  Withdrawal(address indexed src, uint wad);
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) external returns (bool);

}

interface JErc20Interface {
    function liquidateBorrow(
        address borrower,
        uint256 repayAmount,
        JTokenInterface jTokenCollateral
    ) external returns (uint256);
    function approve(address spender, uint256 amount) external;
    function allowance(address owner, address spender) external view returns (uint256);
    function redeem(uint256 redeemTokens) external returns (uint256);
    function balanceOf(address owner) external view returns (uint256);

}

interface IJoeRouter01 {

    function swapAVAXForExactTokens(
        uint256 amountOut,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external payable returns (uint256[] memory amounts);

    function swapExactTokensForAVAX(
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path,
        address to,
        uint256 deadline
    ) external returns (uint256[] memory amounts);


    function getAmountsIn(uint256 amountOut, address[] calldata path)
        external
        view
        returns (uint256[] memory amounts);

    function getAmountOut(
        uint256 amountIn,
        uint256 reserveIn,
        uint256 reserveOut
    ) external pure returns (uint256 amountOut);
}

interface IJoePair{

    function getReserves()
        external
        view
        returns (
            uint112 reserve0,
            uint112 reserve1,
            uint32 blockTimestampLast
        );

}



contract FlashloanBorrowerDev is ERC3156FlashBorrowerInterface, Ownable {


    /**
     * @notice Event emitted when contract gets onFlashloan response
     */
    event fees_flash(uint256 amount_flashloaned, uint256 fee_flashloan);

    /**
     * @notice Event emitted when !!debugging only
     */
    event balance_after(uint256 amount_balance);

    /**
     * @notice Event emitted when contract is funded with AVAX
     */
    event Received(address, uint);

    /**
     * @notice Event emitted when swap from swap function happens
     */
    event swapped(address from, address to, uint256 amountFrom, uint256 amountTo);


    event beforeliquidation(
            address borrowerToLiquidate,
            address JTokenCollateralToSeize,
            address tokenToRepay,
            uint256 borrowedAmountToRepay,
            address borrowedJTokenAddress);


    /**
     * @notice Event emitted when liquidation from liquidate_borrow function happens
     */
    event liquidated(uint borrow);

    event liquidation_failed(uint borrow);

    /**
     * @notice C.R.E.A.M. comptroller address
     */
    address public comptroller;
    address public joerouter;
    address public wavax;
    address public priceOracle;

    
    constructor(address _comptroller, address _joerouter) {
        comptroller = _comptroller;
        joerouter = _joerouter;
        wavax = 0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7;
        priceOracle = 0xd7Ae651985a871C1BC254748c40Ecc733110BC2E;

    }
        

    receive() external payable {
        emit Received(msg.sender, msg.value);
    }
    function div(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a / b;
        }
    }

    function liquidate_borrow(
        address borrowerToLiquidate,
        address JTokenCollateralToSeize,
        address tokenToRepay, //tu chyba powinno być tokenborrowed/underlying??
        uint256 borrowedTokenAmountToRepay,
        address borrowedJTokenAddress) 
        internal returns (uint256)
        {
            ERC20(tokenToRepay).approve(borrowedJTokenAddress, borrowedTokenAmountToRepay);
            uint256 liquidateBorrow = JErc20Interface(borrowedJTokenAddress).liquidateBorrow(
                borrowerToLiquidate,
                borrowedTokenAmountToRepay,
                JTokenInterface(JTokenCollateralToSeize)
            );
            require(liquidateBorrow == 0, "liquidation failed");
            if (liquidateBorrow == 0)
                {
                    emit liquidated(liquidateBorrow);
                }
            return liquidateBorrow;

    }
    function swap_from_AVAX(
        address JoeRouter,
        address wAVAXToken,
        address JTokenBorrowed,
        uint256 borrowedTokenAmountToRepay,
        uint256 flashBorrowAmount) 
        internal returns (uint256)
        {
            address[] memory path = new address[](2);
            path[0] = wAVAXToken;
            path[1] = JTokenBorrowed;
            IWAVAX(wAVAXToken).approve(JoeRouter, flashBorrowAmount);  //TODO sprawdzić czy się nie zjebało była zmiana z borrowedTokenAmountToRepay
            uint256[] memory amountsIn = IJoeRouter01(JoeRouter).getAmountsIn(
                borrowedTokenAmountToRepay,
                path
            );
            //TODO ogarnąć zamianę z wavax na avax??
            IWAVAX(wAVAXToken).withdraw(flashBorrowAmount);
            //amountsIn[0]
            uint256[] memory amounts = IJoeRouter01(JoeRouter).swapAVAXForExactTokens{value: amountsIn[0]}(
                amountsIn[1],
                path,
                address(this),
                block.timestamp + 1000
            );
            return amounts[0];
            
        }

    function swap_to_AVAX(
        address JoeRouter,
        address wAVAXToken,
        address underlyingCollateral,
        uint256 redeemed,
        address joePair) 
        internal returns (uint256)
        {
            address[] memory path = new address[](2);
            path[1] = wAVAXToken;
            path[0] = underlyingCollateral;
            ERC20(underlyingCollateral).approve(JoeRouter, redeemed);

            (uint112 reserve0, uint112 reserve1, ) = IJoePair(joePair).getReserves();

            uint256 amountOut = IJoeRouter01(JoeRouter).getAmountOut(
                redeemed,
                reserve0,
                reserve1
            );


            uint256[] memory amounts = IJoeRouter01(JoeRouter).swapExactTokensForAVAX(
                redeemed,
                amountOut,
                path,
                address(this),
                block.timestamp + 1000
            );
            return amounts[0];
        }

    // /**
    //  * @notice Function to start flashloan and liquidate borrow
    //  * Params below are used to request flashloan
    //  * @param flashloanLender contract address of flashloan lender -jWAVAX etc
    //  * @param borrowToken token that is being flashloaned
    //  * @param borrowAmount USD amount of token being flashloaned
    //  * Params below are passed in data, returned onFlashloan and used later to swap/liquidate
    //  * @param tokenToRepay token address that will be repaid before liquidating underlying collateral
    //  * @param borrowedAmountToRepay token amount that will be repaid before liquidating underlying collateral
    //  * @param borrowerToLiquidate address of collateral/borrow owner, who will be liquidated
    //  * @param JTokenCollateralToSeize token address of jtoken collateral to be seized
    //  * @param underlyingCollateral token address of JTokenCollateralToSeize underlying asset 
    //  * @param borrowedJTokenAddress token address of JToken providing borrow
    //  * @param joePair address of joe pair used to swap redeemed underlying collateral token for avax
    //  */


    function doFlashloan (
        address[] memory joinedAddresses, //address flashloanLender,
        //address borrowToken,
        //uint256 borrowAmount, //useless?
        //address tokenToRepay,
        uint256 borrowedAmountToRepay
        //address borrowerToLiquidate,
        //address JTokenCollateralToSeize,
        //address underlyingCollateral,
        //address borrowedJTokenAddress,
        //address joePair
    ) external onlyOwner {
        //
        uint256 tokenToRepayPrice = PriceOracle(priceOracle).getUnderlyingPrice(address(joinedAddresses[6]));
        uint256 flashloanedTokenPrice = PriceOracle(priceOracle).getUnderlyingPrice(address(joinedAddresses[0]));


        uint256 flashBorrowAmount = div(borrowedAmountToRepay * tokenToRepayPrice, flashloanedTokenPrice, 'Price oracle failed - no AVAX price available');

        bytes memory data = abi.encode(
            joinedAddresses, 
            flashBorrowAmount, 
            //tokenToRepay, 
            borrowedAmountToRepay
            //borrowerToLiquidate, 
            //JTokenCollateralToSeize,
            //underlyingCollateral, 
            //borrowedJTokenAddress,
            //joePair
            );
        ERC3156FlashLenderInterface(joinedAddresses[0]).flashLoan(this, address(this), flashBorrowAmount, data);
    }



    /**
     * @notice Function called by contract that provides flashloan
     * @param initiator contract address that initiated flashloan
     * @param token token that is being flashloaned
     * @param amount amount of token being flashloaned
     * @param fee fee for flashloaning
     * @param data gives back data that was passed in flashLoan function 
     * @return ??
     */
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) override external returns (bytes32) {
        
        require(Comptroller(comptroller).isMarketListed(msg.sender), "untrusted message sender");
        require(initiator == address(this), "FlashBorrower: Untrusted loan initiator");
        (address[] memory joinedAddresses, //borrowToken
        uint256 flashBorrowAmount,
        //address tokenToRepay,
        uint256 borrowedAmountToRepay
        //address borrowerToLiquidate,
        //address JTokenCollateralToSeize,
        //address underlyingCollateral,
        //address borrowedJTokenAddress,
        //address joePair
        ) = abi.decode(data, (address[], uint256, uint256));

        emit fees_flash(amount, fee);
        require(joinedAddresses[1] == token, "encoded data (borrowToken) does not match");
        require(flashBorrowAmount == amount, "encoded data (flashBorrowAmount) does not match");
        

        
        {
        uint amountFrom = swap_from_AVAX(
            joerouter,
            token,
            joinedAddresses[2], //tokenToRepay
            borrowedAmountToRepay,
            flashBorrowAmount);
        emit swapped(token, joinedAddresses[2], amountFrom, borrowedAmountToRepay);
        
        
        emit beforeliquidation(
            joinedAddresses[3], //borrowerToLiquidate,
            joinedAddresses[4], //JTokenCollateralToSeize,
            joinedAddresses[2], //tokenToRepay,
            borrowedAmountToRepay,
            joinedAddresses[6] //borrowedJTokenAddress
            );
        uint liquidation = liquidate_borrow(
            joinedAddresses[3], //borrowerToLiquidate,
            joinedAddresses[4], //JTokenCollateralToSeize,
            joinedAddresses[2], //tokenToRepay,
            borrowedAmountToRepay,
            joinedAddresses[6] //borrowedJTokenAddress
            );
        
        
        if (liquidation == 0)
        {
            emit liquidated(liquidation);
            //JTokenCollateralToSeize = joinedAddresses[4], 
            uint256 earnedJToken = JErc20Interface(joinedAddresses[4]).balanceOf(address(this));
            uint256 redeemed = JErc20Interface(joinedAddresses[4]).redeem(earnedJToken);
            uint256 earnedSizedToken = ERC20(joinedAddresses[5]).balanceOf(address(this));
            uint256 amount_avax = swap_to_AVAX(
                joerouter,
                wavax,
                joinedAddresses[5], //underlyingCollateral,
                earnedSizedToken,
                joinedAddresses[7] //joePair
            );

            // );
            emit swapped(joinedAddresses[5], //underlyingCollateral, 
            wavax, redeemed, amount_avax);
        }
        }


        // uint256 balance = IWAVAX(token).balanceOf(address(this));
        // //ERC20(token).withdraw(amount + fee);
        // emit balance_after(balance);

        /* allows flashloan to be repaid */
        JErc20Interface(token).approve(msg.sender, amount + fee);
        /* converts sent avax to wavax for flashloan to be repaid */
        IWAVAX(wavax).deposit{value: amount + fee}();
        uint256 token_balance = IWAVAX(token).balanceOf(address(this));
        require(token_balance >= amount + fee, "not enough to repay flashloan");
        uint256 profit = token_balance - amount - fee;
        emit balance_after(profit);
        //require(ERC20(token).transfer(msg.sender, balance), "Transfer fund back failed");
        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }



}
