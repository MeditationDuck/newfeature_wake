// SPDX-License-Identifier: MIT
pragma solidity =0.8.20;

// Simplified ERC-20 interface
interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

}

contract VulnerableTokenStore {
    mapping(address => uint256) public balances;
    IERC20 public token;

    constructor(IERC20 _token) {
        token = _token;
    }

    // Allow users to deposit tokens into the contract
    function deposit(uint256 _amount) public {
        require(token.transferFrom(msg.sender, address(this), _amount), "Transfer failed");
        balances[msg.sender] += _amount;
    }

    // Withdraw tokens from the contract
    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        balances[msg.sender] -= _amount;
        // Vulnerable to reentrancy attacks
        require(token.transfer(msg.sender, _amount), "Transfer failed");
    }
}
