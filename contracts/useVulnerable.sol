// SPDX-License-Identifier: MIT
pragma solidity =0.8.20;

import "./ct1.sol";

contract AttackerContract {

    function attack(address vulnadd) external {
        VulnerableTokenStore target = VulnerableTokenStore(vulnadd);

        target.deposit(100);
    }

}