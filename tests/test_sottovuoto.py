import pytest, os
from pathlib import Path
from sottovuoto.sottovuoto import Sottovuoto
from sottovuoto.exceptions import NoContractFound, NoVarsFound
import logging
logger = logging.getLogger("tests-sottovuoto")
logging.getLogger().setLevel(logging.DEBUG)

"""
False positives tests
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

"""
struct_between_uint128.sol

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

uint128 a;
ExpensiveStruct example;
uint128 b;

"""
def test_user_struct_between_uint128():
    contract_path = "tests/contracts/struct_between_uint128.sol"
    sv = Sottovuoto(contract_path)
    ((spareable_structs_slots, vars), 
     (spareable_storage_slots, _)) = sv.analyze_packing()
    assert spareable_structs_slots == 3
    assert len(vars[0].opt_version) == 5
    assert spareable_storage_slots == 1

"""
nested_expensive_struct.sol

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
"""
def test_nested_expensive_struct():
    contract_path = "tests/contracts/nested_expensive_struct.sol"
    sv = Sottovuoto(contract_path)
    ((spareable_structs_slots, vars),
     (spareable_storage_slots, _)) = sv.analyze_packing()
    assert spareable_structs_slots == 3 + 1 + 1
    assert len(vars[2].opt_version) == 4
    assert spareable_storage_slots == 1

"""
packable_enum.sol

uint128 public a;
uint256 private c;
enum Direction { Sud, East, North, West }
Direction directionChosen;
"""
def test_packable_enum():
    contract_path = "tests/contracts/packable_enum.sol"
    sv = Sottovuoto(contract_path)
    ((_, _),
     (spareable_storage_slots, _)) = sv.analyze_packing()
    assert spareable_storage_slots == 1

"""
udtuint128_doc.sol

@todo support UDT once slither does

contract UDTDoc {

    type UDTuint128 is uint128;

    UDTuint128 a;
    uint256 private b;
    uint128 c;
}

def test_udtuint128_doc():
    contract_path = "tests/contracts/udtuint128_doc.sol"
    sv = Sottovuoto(contract_path)
    ((_, _),
     (spareable_storage_slots, new_slots_map)) = sv.analyze_packing()
    assert spareable_storage_slots == 1
"""

"""
nested_mapping.sol

struct abc {
    uint8 small1;
    uint8 small2;
    bytes32 bigboy;
    uint8 small3;
    mapping(address => mapping(uint => bool)) someNestedMapping;
    uint8 small4;
}
"""
def test_nested_mapping():
    contract_path = "tests/contracts/nested_mapping.sol"
    sv = Sottovuoto(contract_path)
    ((_, _),
     (spareable_storage_slots, _)) = sv.analyze_packing()
    assert spareable_storage_slots == 1