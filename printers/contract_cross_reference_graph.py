from __future__ import annotations

from collections import deque, defaultdict
from pathlib import Path
from typing import List, Set, Tuple, Dict

import networkx as nx
import rich_click as click
from rich import print

import wake.ir as ir
import wake.ir.types as types
from wake.cli import SolidityName
from wake.printers import Printer, printer

class ContractCrossReferenceGraphPrinter(Printer):
    _names: Set[str]
    _out: Path
    _direction: str
    _links: bool
    _force: bool
    _inherit: bool
    _single_file: bool
    _referrer: bool
    _referring: bool

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

        for name in self._names:
            print(name)
            
        import graphviz as gv

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


        if self._single_file and len(self._names) == 0:
            g = gv.Digraph("Contract cross reference")
            g.attr(rankdir=self._direction)
            g.attr("node", shape="box")
            for v in nodes:
                g.node(v[0], v[1], URL=v[2])
            for from_, to in edges:
                g.edge(from_, to)
            p = self._out / "contract-cross-reference-graph.dot"
            if not self._force and p.exists():
                self.logger.warning(f"File {p} already exists, skipping")
                return
            g.save(p)
        elif not self._single_file:
            for node in nodes:
                if node[1] not in self._names:
                    continue
                g = gv.Digraph("Contract cross reference")
                g.attr(rankdir=self._direction)
                g.attr("node", shape="box")
                added_nodes = set()

                style="filled"
                g.node(node[0], node[1], URL=node[2], style=style)
                added_nodes.add(node[0])

                for edge in edges:
                    source, target = edge[0], edge[1]
                    if (self._referrer and target == node[0]) or (self._referring and source == node[0]):
                        for node_id, ct_name, url in nodes:
                            if (node_id == source  or node_id == target) and node_id not in added_nodes:
                                g.node(node_id, ct_name, URL=url)
                                added_nodes.add(node_id)
                        if source in added_nodes and target in added_nodes:
                            g.edge(source, target)

                p = self._out / f"contract-cross-reference-graph-{node[1]}.dot"
                if not self._force and p.exists():
                    self.logger.warning(f"File {p} already exists, skipping")
                    continue
                g.save(p)
        else: # single file and there is names
            g = gv.Digraph("Contract cross reference")
            g.attr(rankdir=self._direction)
            g.attr("node", shape="box")
            added_nodes = set()
            for node in nodes:
                if node[1] not in self._names: # only for names distingish by the name of contract
                    continue
                
                if node[0] not in added_nodes: # generally distingish by the id 
                    style="filled"
                    g.node(node[0], node[1], URL=node[2], style=style)
                    added_nodes.add(node[0])

                for edge in edges:
                    source, target = edge[0], edge[1]
                    if (self._referrer and target == node[0]) or (self._referring and source == node[0]):
                        for node_id, ct_name, url in nodes:
                            if (node_id == source  or node_id == target) and node_id not in added_nodes:
                                style = "filled" if ct_name in self._names else ""
                                g.node(node_id, ct_name, URL=url, style=style)
                                added_nodes.add(node_id)
                        if source in added_nodes and target in added_nodes:
                            g.edge(source, target)
            p = self._out / "contract-cross-reference-graph.dot"
            if not self._force and p.exists():
                self.logger.warning(f"File {p} already exists, skipping")
                return
            g.save(p)
                

    def visit_contract_definition(self, node:ir.ContractDefinition):
        self._contracts.append(node)
    
    @printer.command(name="contract-cross-reference-graph")
    @click.option(
        "--name",
        "-n",
        "names",
        type=SolidityName("contract", case_sensitive=False),
        multiple=True,
        help="Contract names",
    )

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
    @click.option(
        "--single-file/--multiple-files",
        default=True,
        help="Generate single with all discovered contracts or multiple files per contract",
    )

    @click.option(
        "--referrer/--no-referrer",
        default=True,
        help="Generate contracts that refer to the contract.",
    )
    @click.option(
        "--referring/--no-referring",
        default=True,
        help="Generate contracts that are referenced by the contract.",
    )

    
    def cli(
        self,
        names: Tuple[str, ...],
        force: bool,
        out: str,
        direction: str,
        links: bool,
        inherit: bool,
        single_file: bool,
        referrer: bool,
        referring: bool,
    ) -> None:
        """
        Generate contract cross reference graph.
        """
        self._names = names
        self._force = force
        self._out = Path(out).resolve()
        self._out.mkdir(parents=True, exist_ok=True)
        self._direction = direction
        self._links = links
        self._inherit = inherit
        self._single_file = single_file
        self._referrer = referrer
        self._referring = referring


