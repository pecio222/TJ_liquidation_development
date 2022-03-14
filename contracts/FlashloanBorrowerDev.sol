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

interface IJoeBar {
    function enter(uint256 _amount) external;
    function leave(uint256 _share) external;
    function balanceOf(address account) external view returns (uint256);

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

    function swapExactTokensForTokens(
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

    function getAmountsOut(uint256 amountIn, address[] calldata path)
        external
        view
        returns (uint256[] memory amounts);


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
    event balance_after(string numer, uint256 amount_balance);

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
    event liquidated(uint256 borrow);

    /**
     * @notice Event emitted right before repaying flashloan - success!
     */
    event my_success(uint256 profit);


    /**
     * @notice addresses stored on blockchain

     
     */
    address public joetroller;
    address public joerouter;
    address public wavaxAddress;
    address public priceOracle;
    address public joeAddress;

    
    constructor(address _joetroller, address _joerouter) {
        joetroller = _joetroller;
        joerouter = _joerouter;
        wavaxAddress = 0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7;
        priceOracle = 0xd7Ae651985a871C1BC254748c40Ecc733110BC2E;
        joeAddress = 0x6e84a6216eA6dACC71eE8E6b0a5B7322EEbC0fDd;

    }
        

    /**
     * @notice enables receiving AVAX
    **/

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


    /**
     * @notice conveniently using liquidateBorrow on JErc20Interface. Reverts if unsuccessful
     * @param borrowerToLiquidate account being underwater
     * @param JTokenCollateralToSeize collateral, that will be seized - JToken
     * @param tokenToRepay address borrowed token, that will be repaid by liquidator
     * @param borrowedTokenAmountToRepay amount of borrowed token, that will be repaid by liquidator
     * @param borrowedJTokenAddress JToken 'overlying' over tokenToRepay
     * @return liquidateBorrow error message from JErc20Interface. 0 = liquidation successful
    **/

    function liquidate_borrow(
        address borrowerToLiquidate,
        address JTokenCollateralToSeize,
        address tokenToRepay,
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
            if (liquidateBorrow == 0)
                {
                    emit liquidated(liquidateBorrow);
                }
            require(liquidateBorrow == 0, "liquidation failed");
            return liquidateBorrow;

    }

    /**
     * @notice conveniently using swapAVAXForExactTokens from JoeRouter
     * @param toToken desired output token
     * @param requestedOut desired amount of output token
     * @param maxIn maximal amount of AVAX spent
    **/

    function swap_from_AVAX(
        address toToken,
        uint256 requestedOut,
        uint256 maxIn) 
        internal returns (uint256)
        {
            address[] memory path = new address[](2);
            path[0] = wavaxAddress;
            path[1] = toToken;
            IWAVAX(wavaxAddress).approve(joerouter, maxIn); 
            uint256[] memory amountsIn = IJoeRouter01(joerouter).getAmountsIn(
                requestedOut,
                path
            );

            uint256[] memory amounts = IJoeRouter01(joerouter).swapAVAXForExactTokens{value: amountsIn[0]}(
                amountsIn[1],
                path,
                address(this),
                block.timestamp + 1000
            );
            return amounts[0];
            
        }

    /**
     * @notice conveniently using swapExactTokensForAVAX from JoeRouter
     * @param tokenFrom input token
     * @param amountFrom input token amount
    **/

    function swap_to_AVAX(
        address tokenFrom,
        uint256 amountFrom) 
        internal returns (uint256)
        {
            address[] memory path = new address[](2);
            path[1] = wavaxAddress;
            path[0] = tokenFrom;
            ERC20(tokenFrom).approve(joerouter, amountFrom);

            uint256[] memory amountsOut = IJoeRouter01(joerouter).getAmountsOut(
                amountFrom,
                path
            );
            //emit balance_after('a', amountsOut[0]); //debugging only


            uint256[] memory amounts = IJoeRouter01(joerouter).swapExactTokensForAVAX(
                amountFrom,
                amountsOut[1],
                path,
                address(this),
                block.timestamp + 1000
            );
            return amounts[1];
        }


    /**
     * @notice conveniently using swapExactTokensForTokens from JoeRouter
     * @param fromToken input token
     * @param toToken desired output token
     * @param fromTokenAmount amount of input token
    **/

    function swap_token_to_token(
        address fromToken,
        address toToken,
        uint256 fromTokenAmount) 
        internal returns (uint256)
        {
            address[] memory path = new address[](3);
            path[2] = toToken;
            path[1] = wavaxAddress;
            path[0] = fromToken;
            ERC20(fromToken).approve(joerouter, fromTokenAmount);

            uint256[] memory amountsOut = IJoeRouter01(joerouter).getAmountsOut(
                fromTokenAmount,
                path
            );
            //emit balance_after('b', flashBorrowAmount[0]); //debugging tool


            uint256[] memory amounts = IJoeRouter01(joerouter).swapExactTokensForTokens(
                fromTokenAmount,
                amountsOut[2],
                path,
                address(this),
                block.timestamp + 1000
            );
            return amounts[1];
        }


    function withdrawToken(
        address _tokenContract, 
        uint256 _amount) 
        external onlyOwner
    {
        ERC20(_tokenContract).transfer(msg.sender, _amount);
    }

    function withdrawAVAX(
        uint256 _amount) 
        external onlyOwner
    {
        payable(msg.sender).transfer(_amount);
    }




    // /**
    //  * @notice Function to start flashloan and liquidate borrow
    //  * Params below are used to request flashloan
    //  * @param flashloanLender contract address of flashloan lender -jWAVAX etc
    //  * @param flashloanedToken token that is being flashloaned
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




    struct joinedAdres {
        address flashloanLender;
        address flashloanedToken;
        address tokenToRepay;
        address borrowerToLiquidate;
        address JTokenCollateralToSeize;
        address underlyingCollateral;
        address borrowedJTokenAddress;
        address joepair;
    }
    struct returnValues {
        uint256 amountFrom;
        uint256 amount_avax;
        uint256 liquidate_borrow;
        uint256 earnedJToken;
        uint256 earnedUnderlyingToken;
        uint256 amountToken;
    }

    /**
     * @notice Function to start flashloan and liquidate borrow
     * Params below are used to request flashloan
     * @param joinedAddresses struct of addresses - to bypass "stack too deep". Parameters explained above
     * @param borrowedAmountToRepay amount of token that is going to be repaid
     * @param isNative used to navigate between cases (
         0 - borrowed and supplied any token but XJOE&AVAX
         1 - borrowed AVAX, supplied any other token, but XJOE
         2 - borrowed AVAX, supplied XJOE
         3 - supplied AVAX, borrowed any other token, but XJOE
         4 - borrowed&supplied AVAX
         5 - supplied XJOE, borrowed any token but AVAX
         )
         Any of these cases requires other combination of flashloan/swaps on the way to function properly and avoid reentrancy protection.
     */

    function doFlashloan (
        joinedAdres memory joinedAddresses,
        uint256 borrowedAmountToRepay,
        int256 isNative
    ) external onlyOwner {

        //can't flashloan and repay the same token due to reentrancy protection, so:
        //calculating required amount of flashloaned token, that will be swapped to token, that is being repaid using JoeRouter
        uint256 pathLength;
        if (isNative == 3) {
            //flashloaning non-native, repaying non-native, so longer route is needed
            pathLength = 3;
        }
        else {
            //if any other token is to be repaid, there always exists pair - wavax/token:
            pathLength = 2;
        }

        address[] memory path = new address[](pathLength);

        if (isNative == 3) {
            //flashloaning non-native, repaying non-native
            path[0] = joinedAddresses.flashloanedToken;
            path[1] = wavaxAddress;
            path[2] = joinedAddresses.tokenToRepay;    
        }
        else {
            //if any other token is to be repaid:
            path[0] = joinedAddresses.flashloanedToken;
            path[1] = joinedAddresses.tokenToRepay;    
        }



        uint256[] memory flashBorrowAmount = IJoeRouter01(joerouter).getAmountsIn(
            borrowedAmountToRepay,
            path
        );
        //emit balance_after('c', flashBorrowAmount[0]); //debugging only


        //encoding data, sending to flashloanLender; will decode later and use 
        bytes memory data = abi.encode(
            joinedAddresses, 
            flashBorrowAmount[0], 
            borrowedAmountToRepay,
            isNative
            );
        ERC3156FlashLenderInterface(joinedAddresses.flashloanLender).flashLoan(this, address(this), flashBorrowAmount[0], data);
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
    ) override external returns (bytes32) 
    {
        
        require(Comptroller(joetroller).isMarketListed(msg.sender), "untrusted message sender");
        require(initiator == address(this), "FlashBorrower: Untrusted loan initiator");
        (joinedAdres memory joinedAddresses,
        uint256 flashBorrowAmount,
        uint256 borrowedAmountToRepay,
        int256 isNative
        ) = abi.decode(data, (joinedAdres, uint256, uint256, int256));

        //declare struct to avoid 'stack too deep' later
        returnValues memory retrnVals;
        //emit fees_flash(amount, fee); //debugging only

        //swap flashloaned AVAX to token that will be repaid
        if (isNative == 0 || isNative == 5)
        {
            IWAVAX(wavaxAddress).withdraw(flashBorrowAmount);
            retrnVals.amountFrom = swap_from_AVAX(
                joinedAddresses.tokenToRepay,
                borrowedAmountToRepay,
                flashBorrowAmount);
            emit swapped(token, joinedAddresses.tokenToRepay, retrnVals.amountFrom, borrowedAmountToRepay);
        }
        //swap flashloaned token to AVAX that will be repaid
        else if (isNative == 1 || isNative == 4 || isNative == 2)
        {
            //emit balance_after(flashBorrowAmount); //debugging only
            retrnVals.amount_avax = swap_to_AVAX(
                joinedAddresses.flashloanedToken,
                flashBorrowAmount);

            emit swapped(joinedAddresses.flashloanedToken, joinedAddresses.tokenToRepay, flashBorrowAmount, retrnVals.amount_avax);
            IWAVAX(wavaxAddress).deposit{value: retrnVals.amount_avax}();
            
        }
        //swap flashloaned token to token that will be repaid
        else //if (isNative == 3)
        {
            //emit balance_after(flashBorrowAmount); //debugging only
            retrnVals.amountToken = swap_token_to_token(
                joinedAddresses.flashloanedToken,
                joinedAddresses.tokenToRepay,
                flashBorrowAmount);

            emit swapped(joinedAddresses.flashloanedToken, joinedAddresses.tokenToRepay, flashBorrowAmount, retrnVals.amountToken);
           
        }
        
        emit beforeliquidation(
            joinedAddresses.borrowerToLiquidate,
            joinedAddresses.JTokenCollateralToSeize,
            joinedAddresses.tokenToRepay,
            borrowedAmountToRepay,
            joinedAddresses.borrowedJTokenAddress
            );

        //liquidate borrow
        liquidate_borrow(
            joinedAddresses.borrowerToLiquidate,
            joinedAddresses.JTokenCollateralToSeize,
            joinedAddresses.tokenToRepay,
            borrowedAmountToRepay,
            joinedAddresses.borrowedJTokenAddress
            );
        
        
        //check how much JToken was seized by repaying collateral
        retrnVals.earnedJToken = JErc20Interface(joinedAddresses.JTokenCollateralToSeize).balanceOf(address(this));

        //redeem underlying collateral 
        JErc20Interface(joinedAddresses.JTokenCollateralToSeize).redeem(retrnVals.earnedJToken);

        //check how much underlying token was redeemed
        retrnVals.earnedUnderlyingToken = ERC20(joinedAddresses.underlyingCollateral).balanceOf(address(this));
        
        //emit balance_after('d', retrnVals.earnedUnderlyingToken); //debugging only

        //swap redeemed non-native collateral to AVAX
        if (isNative == 0)
            {
            retrnVals.amount_avax = swap_to_AVAX(
                joinedAddresses.underlyingCollateral,
                retrnVals.earnedUnderlyingToken
            );
            emit swapped(joinedAddresses.underlyingCollateral, wavaxAddress, retrnVals.earnedUnderlyingToken, retrnVals.amount_avax);
            }
        //swap redeemed non-native collateral to AVAX, than swap to flashloaned token (amount + fee) to repay flashloan
        else if (isNative == 1)
            {
            retrnVals.amount_avax = swap_to_AVAX(
                joinedAddresses.underlyingCollateral,
                retrnVals.earnedUnderlyingToken
            );
            emit swapped(joinedAddresses.underlyingCollateral, wavaxAddress, retrnVals.earnedUnderlyingToken, retrnVals.amount_avax);

            retrnVals.amountFrom = swap_from_AVAX(
                joinedAddresses.flashloanedToken,
                amount + fee,
                retrnVals.amount_avax);
            emit swapped(wavaxAddress, joinedAddresses.flashloanedToken, retrnVals.amountFrom, amount + fee);
            }

        //swap redeemed AVAX to flashloaned token (amount + fee) to repay flashloan
        else if (isNative == 3 || isNative == 4){
            
            //emit balance_after('e', amount + fee); //debugging only
            //emit balance_after('f', retrnVals.earnedUnderlyingToken); //debugging only
            IWAVAX(wavaxAddress).withdraw(retrnVals.earnedUnderlyingToken);
            retrnVals.amountFrom = swap_from_AVAX(
                joinedAddresses.flashloanedToken,
                amount + fee,
                retrnVals.earnedUnderlyingToken);
            emit swapped(wavaxAddress, joinedAddresses.flashloanedToken, retrnVals.amountFrom, amount + fee);
            }
        
        //swap redeemed XJOE to AVAX, than to flashloaned token (amount + fee) to repay flashloan
        else if (isNative == 2){
            //leave all xjoe
            IJoeBar(joinedAddresses.underlyingCollateral).leave(retrnVals.earnedUnderlyingToken);

            //retrieve balance of joe
            retrnVals.earnedUnderlyingToken = ERC20(joeAddress).balanceOf(address(this));
            emit balance_after('balance of joe', retrnVals.earnedUnderlyingToken);

            //trade joe to flashloaned token
            
            retrnVals.amount_avax = swap_to_AVAX(
                joeAddress,
                retrnVals.earnedUnderlyingToken
            );
            emit swapped(joinedAddresses.underlyingCollateral, wavaxAddress, retrnVals.earnedUnderlyingToken, retrnVals.amount_avax);

            retrnVals.amountFrom = swap_from_AVAX(
                joinedAddresses.flashloanedToken,
                amount + fee,
                retrnVals.amount_avax);
            emit swapped(wavaxAddress, joinedAddresses.flashloanedToken, retrnVals.amountFrom, amount + fee);
            
        }
        //swap redeemed XJOE to flashloaned AVAX (amount + fee) to repay flashloan
        else //if (isNative == 5)
        {
            //leave all xjoe
            IJoeBar(joinedAddresses.underlyingCollateral).leave(retrnVals.earnedUnderlyingToken);

            //retrieve balance of joe
            retrnVals.earnedUnderlyingToken = ERC20(joeAddress).balanceOf(address(this));
            emit balance_after('balance of joe', retrnVals.earnedUnderlyingToken);
            //trade joe to flashloaned token
            
            retrnVals.amount_avax = swap_to_AVAX(
                joeAddress,
                retrnVals.earnedUnderlyingToken
            );
            emit swapped(joinedAddresses.underlyingCollateral, wavaxAddress, retrnVals.earnedUnderlyingToken, retrnVals.amount_avax);

        }
        

        //allows flashloan to be repaid
        JErc20Interface(token).approve(joinedAddresses.flashloanLender, amount + fee);
        if (isNative == 0 || isNative == 5)
        {
        //converts avax to wavax for flashloan to be repaid
        IWAVAX(wavaxAddress).deposit{value: amount + fee}();
        }
        //make sure, that flashloan can be repaid - easy debug if too low balance is a reason
        uint256 token_balance = IWAVAX(token).balanceOf(address(this));
        //require(token_balance >= amount + fee, "not enough to repay flashloan"); //debugging tool
        
        uint256 profit = token_balance - amount - fee;
        emit my_success(profit);

        return keccak256("ERC3156FlashBorrowerInterface.onFlashLoan");
    }
}
