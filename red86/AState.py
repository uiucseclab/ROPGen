"""
    Returns a state in the AStar algorithm
"""
class AState:
    def __init__(self, memState, graph, equivalence, assigns, prev_state, prev_action = None, action_addr = None):
        # Memory state of this AState
        self.__memState = memState
        # r**/e** equivalences of this AState
        self.__equivalence = equivalence
        # e**->r** assignments of this AState
        self.__assigns = assigns
        # Pointer to the previous AState
        self.__prev_state = prev_state
        # Action that returned this AState from prev_state
        self.__prev_action = prev_action
        # Address of the gadget for prev_action
        self.__action_addr = action_addr
        # Remaining graph of actions to complete
        self.__graph = graph

    def copy(self, with_prev_state = None):
        if with_prev_state == None:
            ps = self.__prev_state
        else:
            ps = with_prev_state
        ret = AState(memState = self.__memState.copy(), graph = self.__graph.copy(), equivalence = self.__equivalence.copy(), assigns = self.__assigns, prev_state = ps, prev_action = self.__prev_action, action_addr = self.__action.addr)
        return ret

    """
        Retuns whether self is a goal state, i.e. whether there is still actions to find in the graph or not
    """
    def is_goal(self):
        return self.__graph.isEmpty()

    def get_action_addr(self):
        return self.__action_addr

    def get_prev_state(self):
        return self.__prev_state

    def get_prev_action(self):
        return self.__prev_action

    def get_assigns(self):
        return self.__assigns

    def get_graph(self):
        return self.__graph

    def get_mem(self):
        return self.__memState

    """
        Computes the next AState for the given action.
        - action : Action that was performed to get new_mem
        - action_addr : address of the gadget for action
        - new_mem : New memory state for this new state
        - eq_to_root : root node in self.__graph to which next_state is expected to be equivalent.
        - eq : additional equivalences for next_state compared to this state
        Returns the next state if possible, or None if the given parameters are incoherent with self. For instance, if there is a contradiction between eq and self.__equivalence.
    """
    def next_state(self, action, action_addr, new_mem, eq_to_root = None, eq = {}):
        # Compute new assignments
        new_assigns = self.__assigns.copy()

        # Check validity of the eq parameter and compute new equivalences
        for r, e in self.__equivalence.items():
            if r in eq and eq[r] != e:
                return None
        new_eq = self.__equivalence.copy()
        new_eq.update(eq)

        # Compute new graph
        new_graph = None
        r = eq_to_root
        if r != None:
            # If next state is one of the graph's roots, remove that root from the graph
            if r in self.__graph.getRoots():
                m = self.__graph.getRoots()[r]
                new_graph = self.__graph.withoutRoot(r)
            else:
                return None
        else:
            # If no root specified as an argument, try to find it
            for r, m in self.__graph.getRoots().items():
                reass_m = m.reassigned(new_eq)
                if reass_m.equals(new_mem):
                    new_graph = self.__graph.withoutRoot(r)
                    break
            # If not equivalent to any roots, simply reuse the graph and invalidate all next_actions
            if new_graph == None:
                new_graph = self.__graph.copy()
                for r, m in new_graph.getRoots().items():
                    r.next_action = None

        # Update assignments to remove assignments that will never be used again in the future
        irs = new_graph.getInvolvedRegs()
        for r, e in eq.items():
            new_assigns[e] = r
        temp = new_assigns
        new_assigns = {}
        for e, r in temp.items():
            if r in irs:
                new_assigns[e] = r
            else:
                pass

        return AState(new_mem, new_graph, new_eq, new_assigns, self, action, action_addr)

    def __repr__(self):
        return "<State : "+str(self.__memState)+", eq : " + str(self.__equivalence) + ", assign : "+str(self.__assigns) + ">"


