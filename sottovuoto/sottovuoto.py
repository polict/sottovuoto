"""sottovuoto: a tight variable packing tool for solidity.

sottovuoto analyzes the struct and storage packing of a single
or list of contracts from the filesystem and provides an
optimized order which uses less storage slots.

Typical usage example:
    sottovuoto = Sottovuoto(file)
    sottovuoto.output(sottovuoto.analyze_packing(), "stdout")

"""

import logging
from slither.slither import Slither
from slither.core.declarations import (
    StructureContract
)
from slither.core.variables.state_variable import (
    StateVariable
)
from ortools.linear_solver import pywraplp
from sottovuoto.storage import (
    Storage,
    SLOT_SPACE_IN_BYTES
)
from sottovuoto.exceptions import (
    NoContractFound,
    NoVarsFound
)
from sottovuoto import utils

log = logging.getLogger("sottovuoto")

class Sottovuoto():
    """It contains all the references to the current analysis.

    Attributes:
        file: the file path it is going to analyze
        contract: a slither.core.Contract instance
        storage: a sottovuoto.Storage instance
        variables: the full list of state variables in the contract
    """

    def __init__(self, file):
        """Initialize the instance based on file.

        Args:
            file: a file path string
        """

        self.file = file
        self.contract = {}
        self.storage = Storage()
        self.variables = []

    def get_state_variables(self):
        """Collects all the state variables from self.file.

        Returns:
            A tuple with all the state variables and the number of structs found

        Raises:
            NoContractFound: no contracts were found
            NoVarsFound: no state variables were found
        """

        vars_in_contract = {}

        slither = Slither(self.file)
        if len(slither.contracts) < 1:
            raise NoContractFound(f"{self.file} does not contain any contract.")

        # @todo support more than 1 contract per file
        self.contract = slither.contracts[0]

        # Contract object:
        # https://github.com/crytic/slither/blob/0ec487460690482c72cacdea6705e2c51bb3981e/slither/core/declarations/contract.py
        log.debug(f"new contract found: {self.contract}")

        structs_count = 0
        vars_in_contract = []
        # add all the state variables
        for state_variable in self.contract.state_variables_ordered:
            state_variable.is_inherited = state_variable.contract != self.contract

            if utils.is_struct(state_variable):
                structs_count += 1

            log.debug(f"new state variable found in {self.contract.name}: "
                        f"{state_variable} "
                        f"(type: {state_variable.type}, "
                        f"dynamic? {state_variable.type.is_dynamic}, "
                        f"inherited? {state_variable.is_inherited})")

            # skip it if it's inherited
            # @todo support inherited vars
            if state_variable.is_inherited:
                continue

            # skip it if it's a dynamic type (dynamic array and mappings)
            # as they don't fill the slots sequentially
            if state_variable.type.is_dynamic:
                continue

            vars_in_contract.append(state_variable)

        if len(vars_in_contract) < 1:
            raise NoVarsFound(f"{self.contract} does not define any variable.")

        return vars_in_contract, structs_count

    def get_opt_slots_map(self, vars):
        """Tries to optimize the vars order to use less slots.

        Args:
            vars: the full list of vars to pack

        Returns:
            A tuple with the success flag and the optimized slots map, or None

        References:
            https://en.wikipedia.org/wiki/Bin_packing_problem
            https://developers.google.com/optimization/pack/bin_packing
            https://pypi.org/project/binpacking/
        """

        data = {}
        data['weights'] = []
        index_to_rich_var = []
        # set structs and arrays aside, we'll add them at the end
        tail_vars = []
        for var in vars:
            if utils.is_struct(var) or utils.is_array(var):
                tail_vars.append(var)
                continue
            data['weights'].append(var.type.storage_size[0])
            index_to_rich_var.append(var)

        data['items'] = list(range(len(data['weights'])))
        data['bins'] = data['items']
        data['bin_capacity'] = SLOT_SPACE_IN_BYTES

        # create the mip solver with the SCIP backend
        solver = pywraplp.Solver.CreateSolver('SCIP')
        assert solver

        # variables, needed for the constraints later
        # x[i, j] = 1 if item i is packed in bin j
        x = {}
        for i in data['items']:
            for j in data['bins']:
                x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

        # y[j] = 1 if bin j is used
        y = {}
        for j in data['bins']:
            y[j] = solver.IntVar(0, 1, 'y[%i]' % j)

        # constraints
        # each item must be in exactly one bin
        for i in data['items']:
            solver.Add(sum(x[i, j] for j in data['bins']) == 1)

        # the amount packed in each bin cannot exceed its capacity
        for j in data['bins']:
            solver.Add(
                sum(x[(i, j)] * data['weights'][i] for i in data['items']) <= y[j] *
                data['bin_capacity'])

        # minimize the number of bins used
        solver.Minimize(solver.Sum([y[j] for j in data['bins']]))

        status = solver.Solve()

        opt_slots_map = {}
        if status == pywraplp.Solver.OPTIMAL:
            num_bins = 0
            for j in data['bins']:
                if y[j].solution_value() == 1:
                    bin_items = []
                    bin_weight = 0
                    for i in data['items']:
                        if x[i, j].solution_value() > 0:
                            # append the var's rich object
                            bin_items.append(index_to_rich_var[i])
                            bin_weight += data['weights'][i]
                    if bin_items:
                        num_bins += 1
                        log.debug(f"Slot #{j}")
                        log.debug(f"  Items packed: {[str(var) for var in bin_items]}")
                        log.debug(f"  Total weight: {bin_weight}")
                        opt_slots_map[j] = bin_items

            # add the structs and arrays at the end
            current_slot = len(opt_slots_map)
            for struct_or_array in tail_vars:
                current_slot += 1
                opt_slots_map[current_slot] = [struct_or_array]

            log.debug(f"Number of slots used: {num_bins}")
            log.debug(f"Time = {solver.WallTime()} milliseconds")
            return True, opt_slots_map

        return False, None

    def are_tight_packed(self, vars):
        """Verifies whether the vars are tightly packed.

        Args:
            vars: the full list of vars to pack

        Returns:
            A tuple with number of slots spared and the optimized slots map
        """

        self.storage = Storage()
        # get the current slot space occupied
        current_slots_map = self.storage.get_slots_map(vars)
        log.debug(f"currently they use {len(current_slots_map)} slots:")
        log.debug(f"{current_slots_map}")

        # @todo we could add here a check if len(current_slots_map) = min_slots_possible

        # get the optimized slots map
        solved, opt_slots_map = self.get_opt_slots_map(vars)
        if not solved:
            log.error("the solver couldn't find an optimal solution :(")
            return True, {}

        log.debug(f"the optimized slots map uses {len(opt_slots_map)} slots:")
        log.debug(f"{opt_slots_map}")

        # return it, if it occupies less slots
        if len(opt_slots_map) < len(current_slots_map):
            log.debug(f"{len(current_slots_map) - len(opt_slots_map)}"
                      " slots can be spared")
            return len(current_slots_map) - len(opt_slots_map), opt_slots_map

        # they occupy the same amount of slots
        return 0, None

    def break_down_struct(self, struct):
        """Breaks down a struct into its members.

        Args:
            struct: the struct to break down

        Returns:
            A list of all the struct's members
        """

        vars = []
        if isinstance(struct, StateVariable):
            # struct is a StateVariable < UserDefinedType < StructureVariable
            # so we need to go up two types
            for var in struct.type.type.elems_ordered:
                vars.append(var)
        if isinstance(struct, StructureContract):
            for var in struct.elems_ordered:
                vars.append(var)
        return vars

    def are_structs_packed(self):
        """A wrapper around self.are_tight_packed for structs.

        Returns:
            A tuple with number of slots spared and the optimized variables
        """

        spared_slots = 0
        # we are only interested in structs
        opt_structs = []
        for var in [var for var in self.contract.structures_declared]:
            vars_in_struct = self.break_down_struct(var)
            (struct_is_tight_packed, new_members_order) = self.are_tight_packed(vars_in_struct)
            if struct_is_tight_packed != 0:
                log.debug(f"{str(var)} is not tight packed, "
                          f"optimized order: " 
                          f"{[str(member) for member in enumerate(new_members_order)]}")
                var.opt_version = new_members_order
                opt_structs.append(var)
                spared_slots += struct_is_tight_packed

        return spared_slots, opt_structs

    def analyze_packing(self):
        """Entrypoint for the analysis.

        Returns:
            A tuple of two tuples:
                A flag indicating whether all the structs are packed and the new vars list
                A flag indicating whether the whole storage is packed and the new slots map
        """

        try:
            vars_in_contract, structs_count = self.get_state_variables()
        except (NoContractFound, NoVarsFound) as exception:
            log.info(exception)
            return (0, None), (0, None)

        if structs_count > 0:
            log.debug("=================== STRUCTS ANALYSIS =========================")

        # let's analyze the structs first
        (structs_are_tight_packed, opt_structs) = \
            self.are_structs_packed()

        # then we analyze the whole contract,
        # but skip really simple ones
        if len(vars_in_contract) < 3:
            log.debug(f"too few variables: {self.contract.name}'s storage analysis was skipped.")
            return ((structs_are_tight_packed, opt_structs),
                (0, None))

        log.debug("==================== CONTRACT ANALYSIS ======================")
        (contract_is_tight_packed, maybe_opt_slots_map) = \
            self.are_tight_packed(vars_in_contract)

        return ((structs_are_tight_packed, opt_structs),
                (contract_is_tight_packed, maybe_opt_slots_map))

    def output(self, analysis_output, output_choice):
        """Outputs the results of the analysis.

        Args:
            analysis_output: the return value from self.analyze_packing
            output_choice: the output destination
        """

        assert output_choice == "stdout"

        (structs_are_tight_packed_or_count, opt_structs), \
        (contract_is_tight_packed_or_count, new_slots_map) = analysis_output
        if structs_are_tight_packed_or_count != 0:
            log.info(f"{self.file} -> {self.contract.name}'s structs are not tight packed.")
            log.info(f"{structs_are_tight_packed_or_count} slot(s) could be spared "
                     "by defining them in this order:")
            for var in [var for var in opt_structs if hasattr(var, 'opt_version')]:
                log.info(f"{self.contract.name} -> {var}:")
                for slot in var.opt_version:
                    for member in var.opt_version[slot]:
                        log.info(f"{member.type} {str(member)}")

        if contract_is_tight_packed_or_count != 0:
            log.info(f"{self.file} -> {self.contract.name}'s storage is not tight packed.")
            log.info(f"{contract_is_tight_packed_or_count} slot(s) could be spared "
                     "by declaring the state variables in this order:")
            for slot in new_slots_map:
                log.debug(f"slot #{slot}: {new_slots_map[slot]}")
                for var in new_slots_map[slot]:
                    var.visibility = " " if var.visibility == "internal" else f" {var.visibility} "
                    log.info(f"{var.type}{var.visibility}{var}")

        log.debug("==============================================================")
