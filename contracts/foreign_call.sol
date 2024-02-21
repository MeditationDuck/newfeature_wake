// SPDX-License-Identifier: MIT
pragma solidity =0.8.20;

import "./ct1.sol";

contract ReferContract {

    function call_foreign_function(address vulnadd) external {
        VulnerableTokenStore target = VulnerableTokenStore(vulnadd);

        // target.deposit(100);
        target.change(msg.sender);
    }
}

// contract ReferingContract {

//     function refering_vts(address vtsadd) external {
//         bytes memory data = abi.encodeWithSignature("deposit(uint256)", 100);

//         (bool success, bytes memory returnedData) = vtsadd.call(data);

//         require(success, "Call failed");
//     } 
// }