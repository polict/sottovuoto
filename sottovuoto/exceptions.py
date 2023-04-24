"""sottovuoto.Exceptions contains common exceptions

It covers two scenarios: 
    NoContractsFound: no contracts were found in the input file
    NoVarsFound: no variables were found in the contract(s)

"""

class NoContractFound(Exception):
    """No contracts were found in the input file."""

class NoVarsFound(Exception):
    """No variables were found in the contract(s)."""
