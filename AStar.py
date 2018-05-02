import sys
sys.path.insert(0, './red86')
from random import shuffle

from Value import *
from Location import *

from MemState import *
from AState import *
from Action import *

from Extracter import *

from Graph import *
from Node import *

try:
    import Queue as Q  # ver. < 3.0
except ImportError:
    import queue as Q

class AStar:
    """
        - graph : graph representation of the instructions to find
        - gadgets : available gadgets in the form of an Extracted object
    """
    def __init__(self, graph, gadgets):
        self.graph = graph
        self.gadgets = gadgets

    """
        Runs the AStar algorithm.
    """
    def run(self):
        frontier = Q.PriorityQueue()
        state = AState(MemState(), self.graph, equivalence = {}, assigns = {}, prev_state = None)
        frontier.put((1, state))

        max_graph = self.graph.count() + 1
        loop_counter = 0
        fail_count = 0
        while frontier:
            loop_counter += 1
            if (loop_counter % 500 == 0):
                print("Iteration " + str(loop_counter))

            try:
                (_, state) = frontier.get(block = False)
            except Q.Empty:
                break

            # Testing whether solution was found
            if state.is_goal():
                sequence = []
                goal_state = state
                while state:
                    addr = state.get_action_addr()
                    if addr:
                        addr = hex(addr)
                    sequence.append(state.get_prev_action())
                    state = state.get_prev_state()
                sequence.reverse()
                for s in sequence:
                    if s:
                        print(s)
                return goal_state

            # for each possible root of the graph
            for r, target_mem in state.get_graph().getRoots().items():
                # target_action should always exist.
                # Used to sometimes not when I allowed multiple gadgets per target_actions
                if r.next_action != None:
                    target_action = r.next_action.reassigned(state.get_assigns())
                else:
                    target_action = None

                # try all available gadgets
                items = self.gadgets.data.items()
                shuffle(items)
                for gadget_o, g_addrs in items:
                    g_addr = g_addrs[0]
                    gadget = gadget_o.reassigned(state.get_assigns())
                    next_mem = gadget.apply(state.get_mem())

                    eq = None
                    if target_action:
                        # Testing equivalence between gadget and target action
                        eq = gadget.equivalence(target_action)
                        if eq != None:
                            # Generating next memory state
                            assign = {}
                            for rx, exx in eq.items():
                                assign[exx] = rx
                            next_mem = next_mem.reassigned(assign)

                            # If next memory state is valid, add next AStar stat to the frontier
                            if (next_mem != state.get_mem() or isinstance(gadget, IntAction)) and (next_mem.equivalence(target_mem) != None):
                                next_state = state.next_state(gadget, g_addr, next_mem, r, eq)
                                if next_state != None:
                                    frontier.put((-100000 * (max_graph - next_state.get_graph().count()) -1000 + len(eq), next_state))

                    # If gadget was not added, try to compare the two memory states instead of the action
                    if eq == None and target_action != None and target_action.__class__ != IntAction :
                        eq = next_mem.equivalence(target_mem)
                        if eq != None:
                            next_state = state.next_state(gadget, g_addr, next_mem, r, eq)
                            # If they are equivalent, add it with a smaller priority
                            if next_state != None:
                                frontier.put((-100000 * (max_graph - next_state.get_graph().count()) -100 + len(eq), next_state))

                     # Attempt to have multiple gadgets per target instruction, not working though.
#                    if eq == None:
#                        fail_count += 1
#                        if target_action:
#                            eq = target_action.dst.equivalence(gadget.dst)
#                            if eq != None:
#                                print("destinations are the same : " + str(target_action.dst) + ", " + str(gadget.dst) + " with eq = "  + str(eq))
#                                next_state = state.next_state(gadget, g_addr, next_mem, eq = eq)
#                                if next_state != None:
#                                    print("adding to frontier : " + str(next_state))
#                                    frontier.put((-100000 * (max_graph - next_state.get_graph().count()) -100 + len(eq), next_state))
#                        else:
#                            dst = r.dst
#                            if dst == gadget.dst:
#                                print("nothing matches, just adding since same dst " + str(dst))
#                                next_state = state.next_state(gadget, g_addr, next_mem)
#                                if next_state != None:
#                                    print("adding to frontier : " + str(next_state))
#                                    frontier.put((0, next_state))


            if fail_count > 100000:
                print("likely no solution")
                return None


