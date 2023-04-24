// from https://medium.com/layerx/how-to-reduce-gas-cost-in-solidity-f2e5321e0395#1701

pragma solidity ^0.8.0;

contract UserUnpackedStruct {

  // 112465 gas
  struct UserUnpacked {
    bool    isMarried;
    bytes32 description;
    bytes23 name;
    bytes10 picture;
    bytes20 location;
    uint64  id;
    uint8   age;
  }
  UserUnpacked public userUnpacked;

  function unpackedStruct(
    uint64 id, bytes23 name, bytes32 description, bytes10 
    picture, bool isMarried, bytes20 location, uint8 age) public 
  {
    userUnpacked = UserUnpacked(
      isMarried, description, name, picture, location, id, age);
  }

}