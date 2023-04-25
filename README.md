# sottovuoto: a tight variable packing tool for solidity 📦

## Etymology
"sottovuoto" (IPA: /sottovwɔto/) stands for "vacuum packed" in italian. 🍝

## Dependencies
* slither
* solc
* ortools (bin packing solver)
* pytest (optional, for development)

## Install
`cd sottovuoto && pip install .`

## Run
### Analyze a contract
`sottovuoto --contract example.sol`

### Analyze a folder of contracts
It will collect and analyze all .sol files found, recursively:

`sottovuoto --folder contracts/`

## Tests
### Run the unit tests
`pytest -s tests/`

### Call for tests (CFT)
The test suite is pretty limited at the moment: contribute with your edge cases!

## License
GPL-3