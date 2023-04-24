import pytest, os
from pathlib import Path
from sottovuoto.sottovuoto import Sottovuoto
from sottovuoto.exceptions import NoContractFound, NoVarsFound
import logging
logger = logging.getLogger("tests-sottovuoto")
logging.getLogger().setLevel(logging.DEBUG)

"""
False positives tests:
    * cheap_struct.sol
    * doc_cheap.sol
    * user_packed.sol
"""

"""
cheap_struct.sol

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

"""
def test_cheap_struct():
    contract_path = "tests/contracts/cheap_struct.sol"
    sv = Sottovuoto(contract_path)
    ((spareable_structs_slots, _), 
     (_, _)) = sv.analyze_packing()
    assert spareable_structs_slots == 0

"""
doc_cheap.sol

uint128 public a;
uint128 public c;
uint256 public b;

"""
def test_doc_cheap():
    contract_path = "tests/contracts/doc_cheap.sol"
    sv = Sottovuoto(contract_path)
    ((_, _), 
     (spareable_storage_slots, _)) = sv.analyze_packing()
    assert spareable_storage_slots == 0

"""
user_unpacked.sol

struct UserPacked {
    uint64  id;
    uint8   age;
    bytes23 name;
    bytes32 description;
    bytes20 location;
    bytes10 picture;
    bool    isMarried;
}

"""
def test_user_packed():
    contract_path = "tests/contracts/user_packed.sol"
    sv = Sottovuoto(contract_path)
    ((spareable_structs_slots, _), 
     (_, _)) = sv.analyze_packing()
    assert spareable_structs_slots == 0

"""
True positives tests
"""

"""
doc_expensive.sol

uint128 public a;
uint256 public b;
uint128 public c;

"""
def test_doc_expensive():
    contract_path = "tests/contracts/doc_expensive.sol"
    sv = Sottovuoto(contract_path)
    ((_, _), 
     (contract_is_tight_packed, new_slots_map)) = sv.analyze_packing()
    assert contract_is_tight_packed == 1
    assert len(new_slots_map) == 2

"""
expensive_struct.sol

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

"""
def test_expensive_struct():
    contract_path = "tests/contracts/expensive_struct.sol"
    sv = Sottovuoto(contract_path)
    ((spareable_structs_slots, vars), 
     (_, _)) = sv.analyze_packing()
    assert spareable_structs_slots == 3
    assert len(vars[0].opt_version) == 5

"""
user_unpacked.sol

struct UserUnpacked {
    bool    isMarried;
    bytes32 description;
    bytes23 name;
    bytes10 picture;
    bytes20 location;
    uint64  id;
    uint8   age;
}

"""
def test_user_unpacked():
    contract_path = "tests/contracts/user_unpacked.sol"
    sv = Sottovuoto(contract_path)
    ((spareable_structs_slots, vars), 
     (_, _)) = sv.analyze_packing()
    assert spareable_structs_slots == 2
    assert len(vars[0].opt_version) == 3