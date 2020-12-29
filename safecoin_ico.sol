pragma solidity ^0.4.11;

contract safecoin_ico {
    uint public max_safecoins = 1000000;
    uint public usd_to_safecoins = 1000;
    uint public total_safecoins_bought = 0;
    
    // Mapping from the investor address to its equity in safecoins and USD
    mapping(address => uint) equity_safecoins;
    mapping(address => uint) equity_usd;
    
    modifier can_buy_safecoins(uint usd_invested) {
        require(usd_invested * usd_to_safecoins + total_safecoins_bought <= max_safecoins);
        _;
    }
    
    function equity_in_safecoins(address investor) external constant returns(uint) {
        return equity_safecoins[investor];
    }
    function equity_in_usd(address investor) external constant returns(uint) {
        return equity_usd[investor];
    }
    
    function buy_safecoins(address investor, uint usd_invested) external
    can_buy_safecoins(usd_invested) {
        uint safecoins_bought = usd_invested * usd_to_safecoins;
        equity_safecoins[investor] += safecoins_bought;
        equity_usd[investor] = equity_safecoins[investor]/1000;
        total_safecoins_bought += safecoins_bought;
    }
    
    function sell_safecoins(address investor, uint safecoins_to_sell) external {
        equity_safecoins[investor] -= safecoins_to_sell;
        equity_usd[investor] -= equity_safecoins[investor]/1000;
        total_safecoins_bought -= safecoins_to_sell;
    }
    
    
}











