// SPDX-License-Identifier: MIT
pragma solidity =0.8.20;

import "./ct1.sol";
import "./imp.sol";

contract ReferContract {

    function call_foreign_function(address vulnadd) external {
        VulnerableTokenStore target = VulnerableTokenStore(vulnadd);

        // target.deposit(100);
        target.change(msg.sender);
    }
}

contract RefRef {
    uint256 public value;

    function check(address ad) external {
        CheckMemberAccsess(ad).mAccess(this);
    }
    
}

contract ReferingContract {

    function refering_vts(address vtsadd) external {
        ReferContract rc = ReferContract(vtsadd);
        max(uint256(11), uint256(12));
        rc.call_foreign_function(vtsadd);
    } 
}

contract ImpCheck {
    ReferingContract ab;

    constructor(ReferingContract dc){
        ab = dc;
    } 

    function refercheck(ReferContract cd) external{
        ReferContract ef = ReferContract(cd);
    }

    function Access(RefRef cd) external returns(uint256) {

        return cd.value();
    }
}

contract CheckMemberAccsess {

    function mAccess(RefRef cd) external payable returns(uint256){

        uint256 ad_cd = address(cd).balance;
        (bool sent, ) = address(cd).call{value: msg.value}("");


    }
}