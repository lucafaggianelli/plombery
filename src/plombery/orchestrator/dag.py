from typing import Any, Collection, Dict, Set

# Constants
UNVISITED = 0
VISITING = 1
VISITED = 2


def is_graph_acyclic(
    task_ids: Collection[str], upstream_of: Dict[str, Set[str]]
) -> bool:
    """
    Checks for cycles in a task graph using Depth First Search (DFS).

    `upstream_of` maps a task id to the ids of the tasks that must complete
    before it, and doesn't have to cover every id in `task_ids`: a task with
    no dependencies simply doesn't need an entry.
    """

    states: Dict[str, int] = {task_id: UNVISITED for task_id in task_ids}

    # Build the Downstream Map (Adjacency List): we need to know where to go
    # FROM a task, but `upstream_of` stores where we came FROM. Reverse it.
    downstream_map: Dict[str, Set[str]] = {task_id: set() for task_id in task_ids}

    for task_id in task_ids:
        for upstream_id in upstream_of.get(task_id, set()):
            if upstream_id in downstream_map:
                downstream_map[upstream_id].add(task_id)
            # NOTE: Any dependency check (like ensuring upstream_id exists)
            # should happen BEFORE this function, in the Pipeline validator.

    # DFS traversal, following downstream edges
    def dfs(task_id: str):

        if states[task_id] == VISITING:
            # Found a node in the current path! CYCLE DETECTED!
            # We return False instead of raising an exception for clean function completion.
            return False

        if states[task_id] == VISITED:
            return True  # Already fully processed and known to be safe

        states[task_id] = VISITING

        # Recursively check all downstream tasks using the generated map
        for next_task_id in downstream_map[task_id]:
            if not dfs(next_task_id):
                return False  # Propagate cycle detection immediately

        # Finished exploring this node and all its descendants.
        states[task_id] = VISITED
        return True  # Node and its branch are acyclic

    # Start DFS from every task, so disconnected components are all covered
    for task_id in task_ids:
        if states[task_id] == UNVISITED:
            if not dfs(task_id):
                return False  # Cycle detected

    # If the function completes, the graph is acyclic.
    return True


def is_mappable_list(data: Any) -> bool:
    """Checks if the output is a list suitable for fan-out mapping."""
    return isinstance(data, (list, set, tuple))
