# from plombery.pipeline.task import Task

# UNVISITED = 0
# VISITING = 1
# VISITED = 2


# def is_graph_acyclic(all_tasks: list[Task]):
#     # Mapping task_id to state
#     states = {task.id: UNVISITED for task in all_tasks}

#     def dfs(task: Task):
#         task_id = task.id

#         if states[task_id] == VISITING:
#             # Found a node in the current path! CYCLE DETECTED!
#             return False

#         if states[task_id] == VISITED:
#             # Already fully processed
#             return True

#         states[task_id] = VISITING

#         # Recursively check all downstream tasks
#         for downstream_task in task.downstream_tasks:
#             if not dfs(downstream_task):
#                 return False

#         # Finished exploring this node and all its descendants.
#         states[task_id] = VISITED
#         return True

#     # Start DFS from all nodes that have no upstream tasks (start nodes)
#     # This ensures all disconnected components of the graph are checked

#     # Collect all tasks to ensure we cover any tasks that might not be connected
#     for task in all_tasks:
#         if states[task.id] == UNVISITED:
#             if not dfs(task):
#                 return False

#     # If the function completes without raising an exception, the graph is acyclic.
#     return True

from plombery.pipeline.task import Task
from typing import List, Dict, Set

# Constants
UNVISITED = 0
VISITING = 1
VISITED = 2


def is_graph_acyclic(all_tasks: List[Task]) -> bool:
    """
    Checks for cycles in the pipeline's task structure using Depth First Search (DFS).
    The graph structure is implicitly defined by the Task objects' upstream_task_ids.
    """

    # 1. Map ID to Task Object and initialize state
    task_map: Dict[str, Task] = {task.id: task for task in all_tasks}
    states: Dict[str, int] = {task_id: UNVISITED for task_id in task_map.keys()}

    # 2. Build the Downstream Map (Adjacency List)
    # We need to know where to go FROM a task, but our dependency model only
    # stores where we came FROM (upstream_task_ids). We must reverse it.
    downstream_map: Dict[str, Set[str]] = {
        task_id: set() for task_id in task_map.keys()
    }

    for task_id, task in task_map.items():
        for upstream_id in task.upstream_task_ids:
            if upstream_id in downstream_map:
                downstream_map[upstream_id].add(task_id)
            # NOTE: Any dependency check (like ensuring upstream_id exists)
            # should happen BEFORE this function, in the Pipeline validator.

    # 3. DFS Traversal (following DOWNSTREAM edges)
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

    # 4. Start DFS from all tasks (ensuring all disconnected components are covered)
    for task_id in task_map.keys():
        if states[task_id] == UNVISITED:
            if not dfs(task_id):
                return False  # Cycle detected

    # If the function completes, the graph is acyclic.
    return True
