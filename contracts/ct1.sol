// // SPDX-License-Identifier: MIT
// pragma solidity =0.8.20;
// import "./foreign_call.sol";
// import "./erc20.sol";

// // Simplified ERC-20 interface
// // interface IERC20 {
// //     function transfer(address recipient, uint256 amount) external returns (bool);
// //     function balanceOf(address account) external view returns (uint256);
// //     function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

// // }

// contract VulnerableTokenStore 
// {
//     mapping(address => uint256) public balances;
//     ERC20 public token;

//     constructor(ERC20 _token) {
//         token = _token;
//     }

//     // Allow users to deposit tokens into the contract
//     function deposit(uint256 _amount) public {

//         require(token.transferFrom(msg.sender, address(this), _amount), "Transfer failed");
//         balances[msg.sender] += _amount;
//     }

//     // Withdraw tokens from the contract
//     function withdraw(uint256 _amount) public {
//         require(balances[msg.sender] >= _amount, "Insufficient balance");
//         balances[msg.sender] -= _amount;
//         // Vulnerable to reentrancy attacks
//         require(token.transfer(msg.sender, _amount), "Transfer failed");
//     }

//     function change(address ad) external{
//         balances[ad] = 0;
//     }

//     function returning(address ad) external {
//         ReferContract a = ReferContract(ad);
//         a.call_foreign_function(msg.sender);
//     }

// }
