// SPDX-License-Identifier: MIT
pragma solidity =0.8.20;


interface IERC {
    // Foo c;
    function foo(address ad) external;
}


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

contract Foo {
    IERC a;

    Foo k;


    AbstractContract b;

    function control_our_contract(address ad) external{
        k = Foo(ad);
    }
}

contract ERC is IERC {
    uint ab;
    function foo(address ad) external override {
        ab = 0;

        ab += ab;

    }
}

contract ercc is ERC {
  constructor() {

  }
}

contract eccc is ERC {
     constructor() {
    
  }

}

contract abcd is ERC, eccc {
     constructor() {
    
  }
}