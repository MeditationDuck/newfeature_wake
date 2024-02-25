from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import List, Set, Tuple

import networkx as nx
import rich_click as click
from rich import print

import wake.ir as ir
import wake.ir.types as types
from wake.cli import SolidityName
from wake.printers import Printer, printer

import re


class ContractCrossReferencePrinter(Printer):
    # _names: Set[str]
    _out: Path
    _direction: str
    _links: bool
    _force: bool
    _single_file: bool
    _children: bool
    _parents: bool
    _interfaces: bool
    _contracts: List[ir.ContractDefinition]
    # _references: Dict[str, ]
    # _function_calls: List[ir.FunctionCall]

    # _import_directives: List[ir.ImportDirective]
    # _visit_identifier_path: List[ir.IdentifierPath]

    def __init__(self):
        self._contracts = []


    def print(self) -> None:

        for node in self._contracts:
            print("-------------------")
            print(node.name)
            identifiers: List[ir.Identifier] = [id for id in node.references if isinstance(id, ir.Identifier)]

            for id in identifiers:
                if isinstance(id, ir.ExpressionAbc) and id.statement is not None: # reference is ExpressionAbc and statement is not none
                    current_node: ir.ExpressionAbc = id
                        # print(current_node.statement.declaration.parent)
                    if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition):
                        print(current_node.statement.declaration.parent.name)
                    # else:
                        # print("the function is not in the contract ... skip")
                else:
                    current_node: ir.SolidityAbc = id
                    while current_node is not None:
                        if isinstance(current_node, ir.ContractDefinition):
                            contract_def:ir.ContractDefinition = current_node
                            print(contract_def.name)
                            break
                        current_node = current_node.parent


            identifier_paths : List[ir.IdentifierPathPart] = [id for id in node.references if isinstance(id, ir.IdentifierPathPart)]
            for pp in identifier_paths:
                current_node: ir.SolidityAbc = pp.underlying_node # always it is not ExpressionAbc
                while current_node is not None:
                    if isinstance(current_node, ir.ContractDefinition):
                        contract_def:ir.ContractDefinition = current_node
                        print(contract_def.name)
                        break
                    current_node = current_node.parent            



        
        import graphviz as gv

        # if not self._force and self._out.exists():
        #     self.logger.warning(f"File {self._out} already exists, skipping")
        #     return
        

        g = gv.Digraph("Contract cross reference")
        g.attr(rankdir=self._direction)
        g.attr("node", shape="box")

        edges: Set[Tuple[str, str]] = set()

        for contract in self._contracts:
            g.node(f"{contract.parent.source_unit_name}_{contract.name}", contract.name)

        for node in self._contracts:
            node_id = f"{node.parent.source_unit_name}_{node.name}"
            identifiers: List[ir.Identifier] = [id for id in node.references if isinstance(id, ir.Identifier)]
            for id in identifiers:
                if isinstance(id, ir.ExpressionAbc) and id.statement is not None: # reference is ExpressionAbc and statement is not none
                    current_node: ir.ExpressionAbc = id
                    if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition): # and parent is 
                        refer_contract:  ir.ContractDefinition = current_node.statement.declaration.parent
                        edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                        if edge_id not in edges:
                            edges.add(edge_id)
                else:
                    current_node: ir.SolidityAbc = id
                    while current_node is not None:
                        if isinstance(current_node, ir.ContractDefinition):
                            refer_contract:ir.ContractDefinition = current_node
                            edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                            if edge_id not in edges:
                                edges.add(edge_id)
                            break
                        if isinstance(current_node, ir.SourceUnit): # reference is not in the contract
                            break
                        current_node = current_node.parent


            identifier_paths : List[ir.IdentifierPathPart] = [id for id in node.references if isinstance(id, ir.IdentifierPathPart)]
            for pp in identifier_paths:
                current_node: ir.SolidityAbc = pp.underlying_node # always it is not ExpressionAbc
                while current_node is not None:
                    if isinstance(current_node, ir.ContractDefinition):
                        refer_contract:ir.ContractDefinition = current_node
                        edge_id = (f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                        if edge_id not in edges:
                            edges.add(edge_id)
                        # g.edge(f"{refer_contract.source_unit.source_unit_name}_{refer_contract.name}", node_id)
                        # print(contract_def.name)
                        break
                    current_node = current_node.parent


        for from_, to in edges:
            g.edge(from_, to)
                    
        p = self._out / "contract-cross-reference-graph.dot"
        if not self._force and p.exists():
            self.logger.warning(f"File {p} already exists, skipping")
            return
        g.save(p)

        

    def visit_contract_definition(self, node:ir.ContractDefinition):
        self._contracts.append(node)
    
    @click.option(
        "--force",
        "-f",
        is_flag=True,
        default=False,
        help="Overwrite existing files",
    )
    @click.option(
        "-o",
        "--out",
        is_flag=False,
        default=".wake/contract-cross-reference-graphs",
        type=click.Path(file_okay=False, dir_okay=True, writable=True),
        help="Output directory",
    )
    @click.option(
        "--direction",
        type=click.Choice(["LR", "TB", "BT", "RL"]),
        default="TB",
        help="Graph direction",
    )

    @printer.command(name="contract-cross-reference")
    def cli(
        self,
        out: str,
        # names: Tuple[str, ...],
        # out: str,
        # direction: str,
        # links: bool,
        # force: bool,
        direction: str,
        # children: bool,
        
        force: bool,
        # parents: bool,
        # interfaces: bool,
        # single_file: bool,visit_identifier_path
    ) -> None:
        """
        print contract reference relationship.
        """
        self._direction = direction
        self._force = force
        self._out = Path(out).resolve()
        self._out.mkdir(parents=True, exist_ok=True)
        # self._names = set(names)

