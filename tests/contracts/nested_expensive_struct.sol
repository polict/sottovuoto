pragma solidity ^0.8.0;

contract NestedStructs {

    struct ExpensiveStruct {
        uint64 a; //uses 8 bytes
        bytes32 e; //uses 32 bytes writes in new slot
        uint64 b; //uses 8 bytes writes in new slot
        bytes32 f; //uses 32 bytes writes in new slot
        uint32 c; //uses 4 bytes writes in new slot
        bytes32 g; //uses 32 bytes writes in new slot
        uint8 d; //uses 1 byte writes in new slot
        bytes32 h; //uses 32 bytes writes in new slot
    }

    struct ChildStruct {
        uint128 child_a;
        uint256 child_b;
        uint128 child_c;
    }

    struct NestedExpensive {
        ExpensiveStruct nested_a;
        uint128 nested_b;
        ChildStruct nested_c;
        uint256 nested_d;
        uint128 nested_e;
    }

    uint128 public a;
    NestedExpensive private example;
    uint128 public b;

    function addNestedStruct() public {
        ExpensiveStruct memory someStruct = ExpensiveStruct(1,"a",2,"b",3,"c",4,"d");
        ChildStruct memory childStruct = ChildStruct(1, 2, 3);
        NestedExpensive memory nestedStruct = NestedExpensive(someStruct, 2, childStruct, 4, 5);
        example = nestedStruct;
    }
}