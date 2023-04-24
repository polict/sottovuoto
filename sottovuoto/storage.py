"""sottovuoto.Storage is a solidity storage implementation

Storage provides the ability to create and edit solidity slots
to calculate the amount of space taken up.

Typical usage example:
    self.storage = Storage()
    self.storage.get_slots_map(vars)

"""

import logging
from slither.core.solidity_types import (
    ArrayType
)
from sottovuoto import utils

SLOT_SPACE_IN_BYTES = 32

log = logging.getLogger("sottovuoto")

class Storage():
    """It contains all the references to the current analysis.

    Attributes:
        slots: the current slots map
        current_slot_id: an inline ref to the current slot id
        bytes_left_in_slot: an inline ref to the number of bytes left in the current slot
    """

    def __init__(self):
        """Initialize the instance, which is empty at the beginning."""

        self.slots = {}
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

            if utils.is_struct(var):
                log.debug(f"{var.type} is a struct")
                self.add_struct_or_array_to_storage(var)
            elif isinstance(var.type, ArrayType):
                log.debug(f"{var} is an array")
                self.add_struct_or_array_to_storage(var)
            else:
                self.add_var_to_storage(var)

        return self.slots

    def start_new_slot(self):
        """Starts a new storage slot"""

        self.current_slot_id += 1
        self.slots[str(self.current_slot_id)] = []
        self.bytes_left_in_slot = SLOT_SPACE_IN_BYTES

    def add_struct_or_array_to_storage(self, var):
        """Adds a struct variable to the storage.

        Args:
            var: the elementary-type variable
        """

        self.start_new_slot()
        # init the new slot if necessary
        if str(self.current_slot_id) not in self.slots:
            self.slots[str(self.current_slot_id)] = []

        self.slots[str(self.current_slot_id)].append(
            {"name": str(var),
            "type": str(var.type),
        # we hardcode 32 because it is just a placeholder,
        # all the structs and arrays will be moved to the end
            "size": 32})
        self.start_new_slot()

    def add_var_to_storage(self, var):
        """Adds a variable to the storage.

        Args:
            var: the variable to add
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
