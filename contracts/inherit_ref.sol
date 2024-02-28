// SPDX-License-Identifier: MIT
pragma solidity =0.8.20;




abstract contract AbstractContract {
    function doSomething() public virtual returns(uint){
        Foo k;
    }
}

contract InheritFromAbstract is AbstractContract {
    function doSomething() public override returns(uint){
        return 0;
    }
}

interface IERC {
    // Foo c;
    function foo(address ad) external;
}


contract Foo {
    IERC a;

    Foo k;


    AbstractContract b;

    function control_our_contract(address ad) external{
        k = Foo(ad);
    }
    erc c;
}

contract ERC is IERC {
    uint ab;
    function foo(address ad) external override {
     

    }
}

contract erc is ERC {

}

contract ERCerc is ERC, erc {
}