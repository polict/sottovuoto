contract NestedMapping {
    struct abc {       
        uint8 small1;
        uint8 small2;
        bytes32 bigboy;
        uint8 small3;
        mapping(address => mapping(uint => bool)) someNestedMapping;
        uint8 small4;
    }

    abc a;
}
