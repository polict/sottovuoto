// from https://github.com/fravoll/solidity-patterns/blob/master/TightVariablePacking/TightVariablePackingGasExample.sol
// under MIT

pragma solidity ^0.8.0;

contract ExpensiveStructPackingExample {

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

    ExpensiveStruct example;

    function addExpensiveStruct() public {
        ExpensiveStruct memory someStruct = ExpensiveStruct(1,"a",2,"b",3,"c",4,"d");
        example = someStruct;
    }
}