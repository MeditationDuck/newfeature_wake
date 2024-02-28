from typing import List, Set, Tuple, Dict


_Cedges: Set[str, Set[str]] = set()
nodes: Set[str] = set()

nodes.add("abab")
nodes.add("cdcd")

_Cedges[nodes[0]].add(nodes[1])