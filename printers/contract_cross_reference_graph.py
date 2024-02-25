from __future__ import annotations

from collections import deque, defaultdict
from pathlib import Path
from typing import List, Set, Tuple

import networkx as nx
import rich_click as click
from rich import print

import wake.ir as ir
import wake.ir.types as types
from wake.cli import SolidityName
from wake.printers import Printer, printer

class ContractCrossReferenceGraphPrinter(Printer):
    _out: Path
    _direction: str
    _links: bool
    _force: bool
    _inherit: bool
    # _single_file: bool

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
        import graphviz as gv

        if not self._force and self._out.exists():
            self.logger.warning(f"File {self._out} already exists, skipping")
            return

        g = gv.Digraph("Contract cross reference")
        g.attr(rankdir=self._direction)
        g.attr("node", shape="box")

        edges: Set[Tuple[str, str]] = set()

        for contract in self._contracts:
            node_attrs = {}
            if self._links:
                node_attrs["URL"] = self.generate_link(contract)
            g.node(f"{contract.parent.source_unit_name}_{contract.name}", contract.name, **node_attrs)

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


        for from_, to in edges:
            g.edge(from_, to)
        g.save(self._out)

    def visit_contract_definition(self, node:ir.ContractDefinition):
        self._contracts.append(node)
    
    @printer.command(name="contract-cross-reference-graph")
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
        default=".wake/contract-cross-reference-graph.dot",
        type=click.Path(file_okay=True, dir_okay=False, writable=True),
        help="Output file",
    )
    @click.option(
        "--direction",
        type=click.Choice(["LR", "TB", "BT", "RL"]),
        default="TB",
        help="Graph direction",
    )
    @click.option(
        "--links/--no-links",
        default=True,
        help="Generate links to source code",
    )
    @click.option(
        "--inherit",
        is_flag=True,
        default=False,
        help="Include inheritance in cross-reference graph.",
    )
    # @click.option(
    #     "--single-file/--multiple-files",
    #     default=True,
    #     help="Generate single with all discovered contracts or multiple files per contract",
    # )
    # @click.option(
    #     "--referer/--no-referer",
    #     default=True,
    #     help="Generate contract referer",
    # )
    # @click.option(
    #     "--refering/--no-refering",
    #     default=True,
    #     help="Generate contract refering",
    # )


    
    def cli(
        self,
        force: bool,
        out: str,
        direction: str,
        links: bool,
        inherit: bool,
        # single_file: bool,
        # referer: bool,
        # refering: bool,

    ) -> None:
        """
        Generate contract cross reference graph.
        """
        self._force = force
        self._out = Path(out).resolve()
        self._out.parent.mkdir(parents=True, exist_ok=True)
        self._direction = direction
        self._links = links
        self._inherit = inherit
        # self._single_file = single_file


