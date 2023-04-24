// from https://medium.com/layerx/how-to-reduce-gas-cost-in-solidity-f2e5321e0395#1701

pragma solidity ^0.8.0;

contract UserPackedStruct {

  // 82565 gas
  struct UserPacked {
    uint64  id;
    uint8   age;
    bytes23 name;
    bytes32 description;
    bytes20 location;
    bytes10 picture;
    bool    isMarried;
  }
  UserPacked public userPacked;
  function packedStruct(
    uint64 id, bytes23 name, bytes32 description, bytes10 
    picture, bool isMarried, bytes20 location, uint8 age) public 
  {
    userPacked = UserPacked(
      id, age, name, description, location, picture, isMarried);
  }

}