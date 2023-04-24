"""sottovuoto.Utils contains common utilities"""

from slither.core.solidity_types import (
    UserDefinedType
)
from slither.core.declarations.structure import (
    Structure
)

def is_struct(var):
    """Check whether a variable is a struct.

    Args:
        var: the variable to check

    Returns:
        Boolean
    """

    return (isinstance(var.type, UserDefinedType) and \
            isinstance(var.type.type, Structure))
