from __future__ import annotations

from typing import List, Set, Tuple
from pathlib import Path

import networkx as nx
import rich_click as click
import wake.ir as ir
import wake.ir.types as types
from rich import print
from wake.cli import SolidityName
from wake.printers import Printer, printer


class ContractCrossReferencePrinter(Printer):
    _names: Set[str]
    _out: Path
    _direction: str
    _links: bool
    _force: bool
    _single_file: bool
    _children: bool
    _parents: bool
    _interfaces: bool
    _contracts: List[ir.ContractDefinition]
    _function_calls: List[ir.FunctionCall]

    _import_directives: List[ir.ImportDirective]

    def __init__(self):
        self._contracts = []
        self._function_calls = []
        self._import_directives = []



    def print(self) -> None:
        print("")
        print("contracts list -----------------")
        for contract in self._contracts:
            # print("printing")
            print(contract.name)
        
        print("")
        print("")
        print("imports----------")
        for import_directive in self._import_directives:


            source_contracts: Tuple[ir.ContractDefinition,...] = import_directive.source_unit.contracts
            if len(source_contracts) > 0:
                print("SOURCE CONTRACTS")
                for source_contract in source_contracts:
                    print(source_contract.name)

            print("at least one of them import this file")

            print("file name: ", import_directive.imported_source_unit_name)
            # do same here print all contract name
            # Assuming 'imported_source_unit' has a similar structure to 'source_unit'
            imported_contracts: Tuple[ir.ContractDefinition,...] = import_directive.imported_source_unit.contracts
            if len(imported_contracts) > 0:
                print("IMPORTED CONTRACTS")
                for imported_contract in imported_contracts:
                    print(imported_contract.name)


        print("")
        print("function calls--------------")
        for fc in self._function_calls:
            print("--------")
            print(fc.kind)        
            print("This function is called: ",fc.expression.parent.source)
            
            # print(fc.expression.parent.source_unit.contracts)

            # print(fc.expression.parent.parent.source)
            # print(fc.expression.parent.parent.parent.source)
            print("In this function: ", fc.expression.statement.declaration.canonical_name)
            # print(fc.expression.statement.declaration.parent)

            sourceontractDefinition: ir.ContractDefinition = fc.expression.statement.declaration.parent
            print("In this contract: ", sourceontractDefinition.name)


            # print(fc.expression.statement.declaration.declaration_string)
            # print(fc.function_called)
            # print(fc.expression.source_unit.contracts)
            # print(fc.expression.parent.source_unit)
            
            # print(fc.expression.parent.source_unit.contracts)
            # parent_contracts: Tuple[ir.ContractDefinition,...] = fc.expression.parent.source_unit.contracts

            print("Type Identifier: ", fc.type_identifier)

            # parent_contracts: List[ir.ContractDefinition] =   fc.source_unit.contracts

            # if len(parent_contracts) > 0:
            #     print("PARENT")
            #     for parent_contract in parent_contracts:
            #         print(parent_contract.name)



        pass

    def visit_contract_definition(self, node:ir.ContractDefinition):
        self._contracts.append(node)

    def visit_function_call(self, node: ir.FunctionCall):
        self._function_calls.append(node)

    def visit_identifier(self, node: ir.Identifier):
        # print(node)
        pass

    def visit_function_definition(self, node: ir.FunctionDefinition):
        print("--Function Definition--------")
        print(node.name)
        # print(node.child_functions)
        # print(node.)
        pass

    def visit_import_directive(self, node: ir.ImportDirective):
        self._import_directives.append(node)


        

        # print("-----")
        # parent_contracts: Tuple[ir.ContractDefinition, ...] = node.parent.contracts

        # # print(parent_contracts[0].name)
        # for pa_contract in parent_contracts:
        #     print(pa_contract)
        # # print(node.imported_source_unit.contracts)
        # source: Tuple[ir.ContractDefinition, ...]= node.imported_source_unit.contracts[0]
        # # print(node.import_string_location)
        # for so_contract in source:  
        #     print(so_contract.name)
        pass

        

    @printer.command(name="contract-cross-reference")
    def cli(
        self,
        # names: Tuple[str, ...],
        # out: str,
        # direction: str,
        # links: bool,
        # force: bool,
        # children: bool,
        # parents: bool,
        # interfaces: bool,
        # single_file: bool,
    ) -> None:
        """
        print contract reference relationship.
        """
        # self._names = set(names)

