// from https://github.com/fravoll/solidity-patterns/blob/master/TightVariablePacking/TightVariablePackingGasExample.sol
// under MIT

pragma solidity ^0.8.0;

contract CheapStructPackingExample {

    struct CheapStruct {
        uint8 a; //uses 1 byte writes in new slot
        uint8 b; //uses 1 byte writes in previous slot
        uint8 c; //uses 1 byte writes in previous slot
        uint8 d; //uses 1 byte writes in previous slot
        bytes1 e; //uses 1 byte writes in previous slot
        bytes1 f; //uses 1 byte writes in previous slot
        bytes1 g; //uses 1 byte writes in previous slot
        bytes1 h; //uses 1 byte writes in previous slot
    }

    CheapStruct example;

    function addCheapStruct() public {
        CheapStruct memory someStruct = CheapStruct(1,2,3,4,"a","b","c","d");
        example = someStruct;
    }
}