"""
Implementation of a game tree-like functionality for using the simulator
The approach is to use deepcopy to take snapshots of the simulator
In terms of how this relates to user actions, the snapshot should be taken immediately before the action
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from itertools import count
from typing import Any, Callable, Optional
from sim import Simulator

@dataclass
class StateNode:
    id: int
    sim: Simulator
    children_nodes: list[StateNode] = field(default_factory=list)
    parent_node: Optional[StateNode] = None

    def add_child(self, node: StateNode):
        self.children_nodes.append(node)

class GameTreeActionType(Enum):
    DOWN_TREE = 1
    UP_TREE = 2
    ADD_NODE = 3
    RESET_NODE = 4

@dataclass
class GameTreeAction:
    action_type: GameTreeActionType
    callback: Callable[[Simulator], Simulator]

def _action_callback(callback):
    # Wrap action callback to return a copy of the current node's sim state (this avoids the simulator running the game tree's own copy)
    def wrapper(self: GameTree, *args, **kwargs):
        callback(self, *args, **kwargs)
        return self.get_current_sim_state()
    return wrapper

class GameTree:
    next_node_id = 0
    def __init__(self, root: Simulator) -> None:
        self.root = StateNode(id=-1, sim=deepcopy(root))
        self.cur_node: StateNode = self.root

    def get_current_sim_state(self) -> Simulator:
        return deepcopy(self.cur_node.sim)

    @_action_callback
    def switch_to_state(self, state_id) -> Simulator:
        switch_to_node = None
        for child in self.cur_node.children_nodes:
            if child.id == state_id:
                switch_to_node = child
        if switch_to_node is None:
            print("failed to go down tree")
        else:
            self.cur_node = switch_to_node
        return self.cur_node.sim

    @_action_callback
    def up_tree(self) -> Simulator:
        if self.cur_node.parent_node is not None:
            self.cur_node = self.cur_node.parent_node
        else:
            print("failed to go up tree")
        return self.cur_node.sim
    
    @_action_callback
    def add_node(self, sim: Simulator):
        assert sim.sim_step > self.cur_node.sim.sim_step, f"Cannot add a node at an earlier or same sim step (got {sim.sim_step} expected > {self.cur_node.sim.sim_step})"

        new_node = StateNode(id=GameTree.next_node_id, sim=deepcopy(sim), parent_node=self.cur_node)
        GameTree.next_node_id += 1
        self.cur_node.add_child(new_node)
        self.cur_node = new_node
        return new_node.sim
    
    def get_available_actions(self) -> list[GameTreeAction]:
        available = []
        if self.cur_node.parent_node is not None:
            available.append(GameTreeAction(GameTreeActionType.UP_TREE, callback=lambda sim: self.up_tree()))
        for child in self.cur_node.children_nodes:
            available.append(GameTreeAction(GameTreeActionType.DOWN_TREE, callback=lambda sim, nid=child.id: self.switch_to_state(nid)))
        
        available.append(GameTreeAction(GameTreeActionType.ADD_NODE, callback=lambda sim: self.add_node(sim)))

        available.append(GameTreeAction(GameTreeActionType.RESET_NODE, callback=lambda sim: self.get_current_sim_state()))

        return available