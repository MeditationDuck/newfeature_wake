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
from wake.ir.enums import ContractKind

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
    _refering_edges: Dict[ir.ContractDefinition, Set[ir.ContractDefinition]]
    _refered_edges: Dict[ir.ContractDefinition, Set[ir.ContractDefinition]]

    
    def __init__(self):
        self._contracts = []
        self._refering_edges = {}
        self._refered_edges = {}

    def find_ContractDefinition(self, node: ir.SolidityAbc) -> ir.ContractDefinition | None: 
        while node is not None:
            if isinstance(node, ir.InheritanceSpecifier) and not self._inherit:
                return None                          
            if isinstance(node, ir.ContractDefinition):
                return node
            if isinstance(node, ir.SourceUnit):
                return None
            node = node.parent

    def create_edge(self, source: ir.ContractDefinition, target: ir.ContractDefinition):
        self._refering_edges[target].add(source)
        self._refered_edges[source].add(target)

    def create_edges(self, source: ir.ContractDefinition, targets: List[ir.ContractDefinition]):
        for target in targets:
            self.create_edge(source, target)

    def node_name(self, contract: ir.ContractDefinition) -> str:
        return f"{contract.parent.source_unit_name}_{contract.name}"

    def print(self) -> None: 
        import graphviz as gv
        for contract in self._contracts:

            self._refered_edges[contract] = set()
            self._refering_edges[contract] = set()

        for contract in self._contracts:
            children: List[ir.ContractDefinition] = []
            children.append(contract)
                
            classified_references = defaultdict(list)
            for reference in contract.references:
                if isinstance(reference, ir.Identifier):
                    classified_references['Identifier'].append(reference)
                elif isinstance(reference, ir.IdentifierPathPart):
                    classified_references['IdentifierPathPart'].append(reference)
                elif isinstance(reference, ir.MemberAccess):
                    classified_references['MemberAccess'].append(reference)

            identifiers: List[ir.Identifier] = classified_references['Identifier']
            identifier_path_parts: List[ir.IdentifierPathPart] = classified_references['IdentifierPathPart']
            member_accesses: List[ir.MemberAccess] = classified_references['MemberAccess']

            for id in identifiers:
                if isinstance(id, ir.ExpressionAbc) and id.statement is not None: # reference is ExpressionAbc and statement is not none
                    current_node: ir.ExpressionAbc = id
                    if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition): 
                        refer_contract: ir.ContractDefinition = current_node.statement.declaration.parent
                        self.create_edges(refer_contract, children)
                else:
                    current_node: ir.SolidityAbc = id
                    refer_contract = self.find_ContractDefinition(current_node)
                    if refer_contract is not None:
                        self.create_edges(refer_contract, children)


            for pp in identifier_path_parts:
                current_node: ir.SolidityAbc = pp.underlying_node # always it is not ExpressionAbc
                refer_contract = self.find_ContractDefinition(current_node)
                if refer_contract is not None:
                    self.create_edges(refer_contract, children)

            for ma in member_accesses:
                if isinstance(ma, ir.ExpressionAbc) and ma.statement is not None:
                    current_node: ir.ExpressionAbc = ma
                    if isinstance(current_node.statement.declaration.parent, ir.ContractDefinition):
                        refer_contract:  ir.ContractDefinition = current_node.statement.declaration.parent
                        self.create_edges(refer_contract, children)
                else:
                    current_node: ir.SolidityAbc = ma
                    refer_contract = self.find_ContractDefinition(current_node)
                    if refer_contract is not None:
                        self.create_edges(refer_contract, children)


    
# topsort contracts about inheritance
        if(True):
            sorted_contracts:List[ir.ContractDefinition] = []
            in_degree:Dict[ir.ContractDefinition, int] = {}
            for contract in self._contracts:
                in_degree[contract] = len(contract.base_contracts) 
                ## conferm the number of base_contracts is the number of base contracts.
                ## since type of base_contracts is List[ir.InheritanceSpecifier] thus to reach base contract, 
                ## we need to traverse SolidityAbc tree to parent.

            que: deque[ir.ContractDefinition] = deque()
            for contract in self._contracts:
                if in_degree[contract] == 0:
                    que.append(contract)

            while len(que) > 0:
                current_contract = que.popleft()
                sorted_contracts.append(current_contract)
                for child_contract in current_contract.child_contracts:
                    in_degree[child_contract] -= 1
                    if in_degree[child_contract] == 0:
                        que.append(child_contract)

            # if len(sorted_contracts) != len(self._contracts):
            #     raise Exception("Cyclic inheritance")
            
            for contract in sorted_contracts:
                for child_contract in contract.child_contracts:
                    if isinstance(child_contract, ir.ContractDefinition):
                        for refering_contract in self._refering_edges[contract]:
                            self._refering_edges[child_contract].add(refering_contract)
                            self._refered_edges[refering_contract].add(child_contract)

                        for refered_contract in self._refered_edges[contract]:
                            self._refered_edges[child_contract].add(refered_contract)
                            self._refering_edges[refered_contract].add(child_contract)


        if(True):
            ignore_contracts: Set[ir.ContractDefinition] = set()
            for contract in self._contracts:
                if contract.kind != ContractKind.CONTRACT or contract.abstract:
                    ignore_contracts.add(contract)
            
            for contract in ignore_contracts:   
                self._refering_edges.pop(contract)
                self._refered_edges.pop(contract)
                self._contracts.remove(contract)

            for contract in self._contracts:
                refering_contracts_copy = set(self._refering_edges[contract])
                for refering_contract in refering_contracts_copy:
                    if refering_contract in ignore_contracts:
                        self._refering_edges[contract].remove(refering_contract)

                refered_contracts_copy = set(self._refered_edges[contract])
                for refered_contract in refered_contracts_copy:
                    if refered_contract in ignore_contracts:
                        self._refered_edges[contract].remove(refered_contract)

        if self._single_file and len(self._names) == 0:
            g = gv.Digraph("Contract cross reference")
            g.attr(rankdir=self._direction)
            g.attr("node", shape="box")
            
            for contract in self._contracts:
                g.node(self.node_name(contract), contract.name, URL=self.generate_link(contract))

            for contract in self._contracts:
                for refering_edge in self._refering_edges[contract]:
                    g.edge(self.node_name(refering_edge), self.node_name(contract))

            p = self._out / "contract-cross-reference-graph.dot"
            if not self._force and p.exists():
                self.logger.warning(f"File {p} already exists, skipping")
                return
            g.save(p)

        elif not self._single_file : #  and len(self._names) != 0 
            for contract in self._contracts:
                added_contracts: Set[ir.ContractDefinition] = set()
                if contract.name not in self._names:
                    continue
                g = gv.Digraph("Contract cross reference")
                g.attr(rankdir=self._direction)
                g.attr("node", shape="box")

                style="filled"
                g.node(self.node_name(contract), contract.name, URL=self.generate_link(contract), style=style)
                if self._referrer: # referrer of given contract thus show contracts are refering to given contract
                    for refering_contract in self._refering_edges[contract]:
                        if refering_contract not in added_contracts:
                            g.node(self.node_name(refering_contract), refering_contract.name, URL=self.generate_link(refering_contract))
                            added_contracts.add(refering_contract)
                        g.edge(self.node_name(refering_contract), self.node_name(contract))
                if self._referring: # referring of given contract i.e. show contracts are refered by given contract
                    for refered_contract in self._refered_edges[contract]:
                        if refered_contract not in added_contracts:
                            g.node(self.node_name(refered_contract), refered_contract.name, URL=self.generate_link(refered_contract))
                            added_contracts.add(refered_contract)
                        if not self._referring or contract != refered_contract:  # for self reference, there will two same edge
                            g.edge(self.node_name(contract), self.node_name(refered_contract))
                p = self._out / f"contract-cross-reference-graph-{contract.name}.dot"
                if not self._force and p.exists():
                    self.logger.warning(f"File {p} already exists, skipping")
                    continue
                g.save(p)

        else: # single file and there is names
            g = gv.Digraph("Contract cross reference")
            g.attr(rankdir=self._direction)
            g.attr("node", shape="box")
            added_contracts: Set[ir.ContractDefinition] = set()
            added_edges = set()
            for contract in self._contracts:
                if contract.name in self._names: # only for names distingish by the name of contract
                    g.node(self.node_name(contract), contract.name, URL=self.generate_link(contract), style="filled")
                    added_contracts.add(contract)
            for contract in self._contracts:
                if contract.name in self._names: # only for names distingish by the name of contract
                   
                    if self._referrer:
                        for refering_contract in self._refering_edges[contract]:
                            if refering_contract not in added_contracts:
                                g.node(self.node_name(refering_contract), refering_contract.name, URL=self.generate_link(refering_contract))
                                added_contracts.add(refering_contract)
                            g.edge(self.node_name(refering_contract), self.node_name(contract))

                    if self._referring:
                        for refered_contract in self._refered_edges[contract]:
                            if refered_contract not in added_contracts:
                                g.node(self.node_name(refered_contract), refered_contract.name, URL=self.generate_link(refered_contract))
                                added_contracts.add(refered_contract)
                            if not self._referring or contract != refered_contract: # for self reference, there will two same edge
                                g.edge(self.node_name(contract), self.node_name(refered_contract))
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
