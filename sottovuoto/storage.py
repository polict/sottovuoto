"""sottovuoto.Storage is a solidity storage implementation

Storage provides the ability to create and edit solidity slots
to calculate the amount of space taken up.

Typical usage example:
    self.storage = Storage()
    self.storage.get_slots_map(vars)

"""

import logging
from slither.core.solidity_types import (
    ArrayType,
    ElementaryType,
    UserDefinedType
)

SLOT_SPACE_IN_BYTES = 32

log = logging.getLogger("sottovuoto")

class Storage():
    """It contains all the references to the current analysis.

    Attributes:
        slots: the current slots map
        should_start_new_slot: a flag for handling structs and arrays
        current_slot_id: an inline ref to the current slot id
        bytes_left_in_slot: an inline ref to the number of bytes left in the current slot
    """

    def __init__(self):
        """Initialize the instance, which is empty at the beginning."""

        self.slots = {}
        self.should_start_new_slot = False
        self.current_slot_id = 0
        self.bytes_left_in_slot = SLOT_SPACE_IN_BYTES

    def get_slots_map(self, vars):
        """Fills the slots with the provided variables.

        Args:
            vars: the full ordered list of storage variables

        Returns:
            A slots map with the storage layout
        """

        for var in vars:
            log.debug(f"{var} is a {var.type} and it is "
                      f"{var.type.storage_size[0]} bytes large")

            if self.should_start_new_slot:
                self.current_slot_id += 1
                self.slots[str(self.current_slot_id)] = []
                self.bytes_left_in_slot = SLOT_SPACE_IN_BYTES
                self.should_start_new_slot = False

            if isinstance(var.type, UserDefinedType):
                log.debug(f"{var.type} is a user defined type, "
                          "we are going to skip it")

            if isinstance(var.type, ArrayType):
                log.debug(f"{var} is an array, we are going to skip it")

            if isinstance(var.type, ElementaryType):
                log.debug(f"{var.type} is a elementary type")
                self.add_elementary_to_storage(var)

        return self.slots

    def add_elementary_to_storage(self, var):
        """Adds an elementary-type variable to the storage.

        Args:
            var: the elementary-type variable
        """

        var_size = var.type.storage_size[0]

        # check if the var doesn't fit the current slot
        if var_size > self.bytes_left_in_slot:
            self.current_slot_id += 1
            self.bytes_left_in_slot = SLOT_SPACE_IN_BYTES - var_size
        # we have enough space in the current slot
        else:
            self.bytes_left_in_slot -= var_size

        # init the new slot if necessary
        if str(self.current_slot_id) not in self.slots:
            self.slots[str(self.current_slot_id)] = []

        self.slots[str(self.current_slot_id)].append(
            {"name": str(var),
            "type": str(var.type),
            "size": var_size})
