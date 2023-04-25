pragma solidity ^0.8.0;

contract PackableEnum {

    uint128 public a;
    uint256 private c;
    enum Direction { Sud, East, North, West }
    Direction directionChosen;
}