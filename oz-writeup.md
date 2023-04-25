# sottovuoto: a tight variable packing tool for solidity 📦

> State variables of contracts are stored in storage in a compact way such that multiple values sometimes use the same storage slot. Except for dynamically-sized arrays and mappings (see below), data is stored contiguously item after item starting with the first state variable, which is stored in slot 0. For each variable, a size in bytes is determined according to its type. Multiple, contiguous items that need less than 32 bytes are packed into a single storage slot if possible, according to the following rules:
>
> * The first item in a storage slot is stored lower-order aligned.
>
> * Value types use only as many bytes as are necessary to store them.
>
> * If a value type does not fit the remaining part of a storage slot, it is stored in the next storage slot.
>
> * Structs and array data always start a new slot and their items are packed tightly according to these rules.
>
> * Items following struct or array data always start a new storage slot.
>
> * For contracts that use inheritance, the ordering of state variables is determined by the C3-linearized order of contracts starting with the most base-ward contract. If allowed by the above rules, state variables from different contracts do share the same storage slot.
>
> The elements of structs and arrays are stored after each other, just as if they were given as individual values.

from [1]

## An example of wasteful packing
```solidity
contract Wasteful {
    uint128 a;          slot #0
    uint256 b;          slot #1
    uint128 c;          slot #2
}
```
Packed alternative:
```solidity
contract Wasteful {
    uint128 a;          slot #0, first half
    uint128 c;          slot #0, second half
    uint256 b;          slot #1
}
```

## Why is it important to pack the storage?
It will reduce the amount of gas required to store the variables in storage, as the same variables can be packed in fewer slots: it will cost less to interact with your contract. Moreover, using less slots will decrease the contract's footprint on the blockchain size, improving scalability.

## Difficulties encountered

### Semgrep is useless here
* It doesn't support post-match logic and doesn't have a solidity typing system.
* Solution: i used slither's API instead.

### Inherited contracts
* "State variables from different contracts do share the same storage slot" [1].
* Potential solution: flatten first, then analyze.

### Tight variable packing !== bin packing
* Variables are not only packed in bins, but there is additional logic involved for arrays and structs: "Structs and array data always start a new slot" and "Items following struct or array data always start a new storage slot" [1].
* I had two options: 
    1. google's bin packing lib supports constraints, but it is quite convoluted to use: https://developers.google.com/optimization/pack/bin_packing#define_the_constraints
    2. move all structs and arrays to the end of the variables list (the end of the filled storage) and do not try to pack them: I chose this option.

### An array item or struct member can't be in two slots
* Array and structs items are basically standalone variables that have a specific order to respect, so we can't easily fill-up slots by dividing: (array_length * item_size) / slot_size.
* Solution: again, ignore structs and arrays in whole-contract analysis. In structs analysis they are already broken down so nested structs are supported.

### The real number of slots in use is miscalculated
* Since i chose to ignore structs and arrays in slots calculations, the actual number of slots used I calculate is less than in reality. That said, since we only show the spared slots number, we should be fine as long as the difference between the current and optimized version is equal to the difference without the structs and arrays: 

slots_length(current order) - slots_length(optimized order) == slots_length(current order without structs and arrays) - slots_length(optimized order without structs and arrays)

### Struct and contract storage packing at the same time is messy
* Solution: first analyze structs, then analyze the whole storage.

### Tight packing testing without actually packing is not trivial 
* It might be possible via heuristics: if it uses the minimum amount of slots possible it is packed for sure, but this logic causes many false-negatives.

### Structs are not "user defined types"
* The slither source code is misleading: https://github.com/crytic/slither/blob/0ec487460690482c72cacdea6705e2c51bb3981e/slither/core/solidity_types/user_defined_type.py#L13
* The solidity documentation says UDT are only "type X is Y" declarations: https://blog.soliditylang.org/2021/09/27/user-defined-value-types/, which slither understandably calls `TypeAlias`: https://github.com/crytic/slither/blob/0ec487460690482c72cacdea6705e2c51bb3981e/slither/core/solidity_types/type_alias.py#L12

### Slither is still in development
* There are a couple of misleading/shadowy classes: https://github.com/crytic/slither/blob/master/slither/core/variables/structure_variable.py
* The documentation is limited to the simplest usage, I had to read its source code.

### The bin packing algorithm might not find an optimal order
* This is expected, i don't think there is a solution without optimizing types (see below).

### Call for test cases (CFT)
* I came up with tests and collected some from public sources [2]
* checkout `/tests/contracts` and let me know if I missed any interesting layout!

## Tradeoffs
* it requires the solidity source code
* it requires 1 contract per file (handles the first one)
* slot packing between inherited contracts is not supported yet
* it depends on slither's API, solc and ortools
* the analyzed contract's solc version must match solc-select's
* (expected) tight variable packing might make the code less readable and more difficult to mantain

## Potential improvements
* multithreaded: one core per contract/file
* support more than 1 contract per file
* in-place patches
* automatic whole-slot pack/unpack functions generation for additional gas savings [3]
* cached packed orders (uint128, uint256, uint128 in any order always packs to 128, 128, 256)
* gas savings calculation (foundry?)
* JSON output for easy integration
* automatic git issue opening and assignment
* include/exclude options
* automatic solc-select synchronization
* slot mapping differential fuzzing against solc
* suggest smaller types for common keywords (timestamps: uint256 -> uint32 works until ~2107)

## Prior work and alternatives
### Tighten: https://github.com/az0mb13/tighten
It does not support contract analysis, just elementary-type variables reordering.

### Slither detector (wip): https://github.com/crytic/slither/pull/1346/files
it is similar to my approach, but implemented as a detector. It has some tradeoffs:
* very silent: no logs
* incorrect current slots usage calculation (structs/arrays covering multiple slots cover just one): https://github.com/crytic/slither/blob/05c4328d4b487afd521d0727436b11c0c1a87635/slither/detectors/variables/optimize_variable_order.py#L188 because of an hardcoded 32 bytes length in https://github.com/crytic/slither/blob/0ec487460690482c72cacdea6705e2c51bb3981e/slither/core/solidity_types/type_information.py#L28
* it uses its own implementation of bin packing: https://github.com/crytic/slither/blob/05c4328d4b487afd521d0727436b11c0c1a87635/slither/detectors/variables/optimize_variable_order.py#L90
* requires slither's compilation runtime
* not really readable

## Lessons learned
* Implementing an idea might be harder than anticipated
* Having access and alternatives to mature tools is key
* Naming things - and respecting naming conventions - is still a problem
* Tools are as reliable as their test suites

## References
1. https://docs.soliditylang.org/en/v0.8.19/internals/layout_in_storage.html#layout-of-state-variables-in-storage
2. https://github.com/code-423n4/2022-01-yield-findings/issues/58
3. https://fravoll.github.io/solidity-patterns/tight_variable_packing.html
