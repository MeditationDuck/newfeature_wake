from __future__ import annotations

from collections import deque, defaultdict
from pathlib import Path
from typing import List, Set, Tuple

import networkx as nx
import rich_click as click
from rich import print
import rich.tree

import wake.ir as ir
import wake.ir.types as types
from wake.cli import SolidityName
from wake.printers import Printer, printer

import re


class ContractCrossReferencePrinter(Printer):
    # _names: Set[str]
    _inherit: bool
    _contracts: List[ir.ContractDefinition]

    def __init__(self):
        self._contracts = []

    def find_ContractDefinition(self, node: ir.SolidityAbc): 
        while node is not None:
            if isinstance(node, ir.InheritanceSpecifier) and not self._inherit:
                return None                          
            if isinstance(node, ir.ContractDefinition):
                return node
            if isinstance(node, ir.SourceUnit):
                return None
            node = node.parent


    def print(self) -> None:
        # for node in self._contracts:
        #     print("-------------------")
        #     print(node.name)
        #     identifiers: List[ir.Identifier] = [id for id in node.references if isinstance(id, ir.Identifier)]

        #     for id in identifiers:
        #         if isinstance(id, ir.ExpressionAbc) and id.statement is not None: # reference is ExpressionAbc and statement is not none
        #             current_node: ir.ExpressionAbc = id
        #                 # print(current_node.statement.declaration.parent)
        #             if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition):
        #                 print(" - ", current_node.statement.declaration.parent.name)
        #             # else:
        #                 # print("the function is not in the contract ... skip")
        #         else:
        #             current_node: ir.SolidityAbc = id
        #             while current_node is not None:
        #                 if isinstance(current_node, ir.ContractDefinition):
        #                     contract_def:ir.ContractDefinition = current_node
        #                     print(" - ", contract_def.name)
        #                     break
        #                 current_node = current_node.parent


        #     identifier_paths : List[ir.IdentifierPathPart] = [id for id in node.references if isinstance(id, ir.IdentifierPathPart)]
        #     for pp in identifier_paths:
        #         current_node: ir.SolidityAbc = pp.underlying_node # always it is not ExpressionAbc
        #         while current_node is not None:
        #             if isinstance(current_node, ir.ContractDefinition):
        #                 contract_def:ir.ContractDefinition = current_node
        #                 print(" - ", contract_def.name)
        #                 break
        #             current_node = current_node.parent            


# ---------------------------------------


        for name in self._names:
            print(name)
            
        from rich.tree import Tree

        edges: Set[Tuple[str, str]] = set()
        nodes: Set[Tuple[str, str, str]] = set()
        # contract_id, contract_name, URL(contract_source)

        for contract in self._contracts:
            node_tuple = (f"{contract.parent.source_unit_name}_{contract.name}", contract.name, self.generate_link(contract))
            nodes.add(node_tuple)


        for node in self._contracts:
            node_id = f"{node.parent.source_unit_name}_{node.name}"


            classified_references = defaultdict(list)

            for reference in node.references:
                if isinstance(reference, ir.Identifier):
                    classified_references['Identifier'].append(reference)
                elif isinstance(reference, ir.IdentifierPathPart):
                    classified_references['IdentifierPathPart'].append(reference)
                elif isinstance(reference, ir.MemberAccess):
                    classified_references['MemberAccess'].append(reference)

            identifiers: List[ir.Identifier] = classified_references['Identifier']
            identifier_path_parts: List[ir.IdentifierPathPart] = classified_references['IdentifierPathPart']
            member_accesses: List[ir.MemberAccess] = classified_references['MemberAccess']
            # print(len(member_accesses))

            for id in identifiers:
                if isinstance(id, ir.ExpressionAbc) and id.statement is not None: # reference is ExpressionAbc and statement is not none
                    current_node: ir.ExpressionAbc = id
                    if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition): 
                        refer_contract:  ir.ContractDefinition = current_node.statement.declaration.parent
                        edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                        if edge_id not in edges:
                            edges.add(edge_id)
                else:
                    current_node: ir.SolidityAbc = id
                    refer_contract = self.find_ContractDefinition(current_node)
                    if refer_contract is not None:
                        edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                        edges.add(edge_id)


            for pp in identifier_path_parts:
                current_node: ir.SolidityAbc = pp.underlying_node # always it is not ExpressionAbc
                refer_contract = self.find_ContractDefinition(current_node)
                if refer_contract is not None:
                    edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                    edges.add(edge_id)

            # for ma in member_accesses:
            #     if isinstance(ma, ir.ExpressionAbc) and ma.statement is not None:
            #         current_node: ir.ExpressionAbc = ma
            #         if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition):
            #             refer_contract:  ir.ContractDefinition = current_node.statement.declaration.parent
            #             edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
            #             if edge_id not in edges:
            #                 edges.add(edge_id)
            #     else:
            #         current_node: ir.SolidityAbc = ma
            #         refer_contract = self.find_ContractDefinition(current_node)
            #         if refer_contract is not None:
            #             edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
            #             edges.add(edge_id) 

        # table.add_column("Referenced By", justify="left")
                    

        print(" referring tree")
      
        for node in nodes:
            referring_tree = Tree(
                f"[link={node[2]}]{node[1]}[/link]"
            )
            for from_, to in edges:
                if node[0] == from_:
                    for to_node in nodes:
                        if to_node[0] == to:
                            referring_tree.add(f"[link={to_node[2]}]{to_node[1]}[/link]")
            
            print(referring_tree)

        print("")
        print(" referrer tree")
        for node in nodes:
            referrer_tree = Tree(
                f"[link={node[2]}]{node[1]}[/link]"
            )
            for from_, to in edges:
                if node[0] == to:
                    for to_node in nodes:
                        if to_node[0] == from_:
                            referrer_tree.add(f"[link={to_node[2]}]{to_node[1]}[/link]")
            
            print(referrer_tree)


     

        

    def visit_contract_definition(self, node:ir.ContractDefinition):
        self._contracts.append(node)
    
    @printer.command(name="contract-cross-reference")
    @click.option(
        "--name",
        "-n",
        "names",
        type=SolidityName("contract", case_sensitive=False),
        multiple=True,
        help="Contract names",
    )

    @click.option(
        "--inherit",
        is_flag=True,
        default=False,
        help="Include inheritance in cross-reference graph.",
    )
    def cli(
        self,
        names: Tuple[str, ...],
        inherit
    ) -> None:
        """
        print contract reference relationship.
        """
        self._names = set(names)
        self._inherit = inherit

