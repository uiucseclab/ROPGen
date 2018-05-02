from Node import *
from Location import *
from Action import *
from pwn import *

"""
    Represents a sequence of instructions in a graph of read/write dependencies
"""
class Graph:
    def __init__(self, nodes = set()):
        import MemState
        self.__nodes = set()
        self.__roots = {}
        self.__count = 0
        self.__involvedRegs = {}
        for n in nodes:
            # Add nodes
            if not (n in self.__nodes):
                self.__nodes.add((n))
                self.__count += 1
            else:
                raise ValueError("Duplicate node")

            # Add all nodes that have no 'before' dependencies to roots
            if (not n in self.__roots) and (not n.bef) :
                self.__roots[n] = None

            # Update involved registers
            ir = n.involvedRegs()
            for r in ir:
                if r in self.__involvedRegs:
                    self.__involvedRegs[r] += 1
                else:
                    self.__involvedRegs[r] = 1

        # Set the target state of each root
        for r in self.__roots:
            mem_state = MemState.MemState()
            self.__roots[r]= r.next_action.apply(mem_state)

    def count(self):
        return self.__count

    def getRoots(self):
        return self.__roots

    def getNodes(self):
        return self.__nodes

    def getInvolvedRegs(self):
        return self.__involvedRegs

    def isEmpty(self):
        return self.__count == 0

    def copy(self):
        g = Graph()
        g.__nodes = self.__nodes.copy()
        g.__roots = self.__roots.copy()
        g.__count = self.__count
        g.__involvedRegs = self.__involvedRegs.copy()
        return g

    """
        Returns a new grahp without the given root.
    """
    def withoutRoot(self, node):
        node_copies = {}
        # node mest be a root
        if node.bef:
            print("call withoutRoot with : " + str(node))
            print("node.bef : " + str(node.bef))
            self.print_dependencies()
            raise ValueError("")
        if not node in self.__nodes:
            raise ValueError("trying to remove a node that isn't in graph")
        if not node in self.__roots:
            raise ValueError("trying to remove a node that isn't a root")

        # Need to update node's dependencies to point to the new nodes.
        # node_copies keeps track of the old node associated to its copy
        for n in self.__nodes:
            if n != node:
                node_copies[n] = n.cleanCopy()

        # New set of roots
        new_roots = {}
        for r, s in self.__roots.items():
            if r != node:
                new_roots[node_copies[r]] = s.copy()
        new_count = self.__count

        # New set of nodes. Updating each new node's bef and aft sets
        new_nodes = set()
        for n, nc in node_copies.items():
            for b in n.bef:
                if b != node:
                    nc.addBef(node_copies[b])
            for a in n.aft:
                nc.addAft(node_copies[a])
            new_nodes.add(nc)
        n = None

        # Updating involvedRegs
        new_ir = self.__involvedRegs.copy()
        new_count -= 1
        for r in node.involvedRegs():
            if r in new_ir:
                new_ir[r] -= 1
                if new_ir[r] == 0:
                    del new_ir[r]

        # Updating target states of each root
        st = self.__roots[node]
        for n2 in node.aft:
            n2 = node_copies[n2]
            if len(n2.bef) == 0:
                new_roots[n2] = st
        for r, _ in new_roots.items():
            if r.next_action != None:
                new_roots[r] = r.next_action.apply(st)


        new_g = Graph()
        new_g.__nodes = new_nodes
        new_g.__roots = new_roots
        new_g.__count = new_count
        new_g.__involvedRegs = new_ir
        return new_g

    """
        Used for debugging purposes, prints all nodes of the graph with their read/write dependencies
    """
    def print_dependencies(self):
        for n in self.__nodes:
            print("node : " + str(n.next_action) + "\n  must be before : ")
            for n2 in n.aft:
                print("\t"+str(n2.next_action))
            print("  and must be after : ")
            for n2 in n.bef:
                print("\t"+str(n2.next_action))

    @staticmethod
    def parseInt(s):
        if len(s) > 2:
            return int(s[2:], 16)
        else:
            return int(s)

    """
        Given a string, parses it into an action.
        Returns a (Action, Read_dependencies, Write_dependencies, Is_barrier) tuple, where dependencies are sets of locations, and Is_barrier is a boolean indicating whether the instruction is a memory barrier, meaning that no instructions should be rearranged with respect to the parsed action.
    """
    @staticmethod
    def parseLine(s):
        s = s.strip()
        op = s.split(' ')[0]
        token = ""
        in_mem = False
        in_mem_phase = 0
        in_src = False
        base = None
        index = None
        scale = 1
        displacement = 0
        args = []
        dep_r = set()
        dep_w = set()
        if len(s) < 3 :
            return (None, None, None, None)

        for c in s[3:]:
            if c == ' ' or c == ']' or c == '\t':
                if in_mem and len(token) != 0:
                    if in_mem_phase == 0:
                        base = Location(reg = token.lower())
                        dep_r.add(base)
                        token = ""
                    elif in_mem_phase == 1:
                        try:
                            displacement = Graph.parseInt(token)
                            in_mem_phase = 3
                        except:
                            index = Location(reg = token.lower())
                            token = ""
                            dep_r.add(index)
                    elif in_mem_phase == 2:
                        scale = Graph.parseInt(token)
                    elif in_mem_phase == 3:
                        displacement = Graph.parseInt(token)
                if in_mem and c == ']':
                    loc = Location(base = base, index = index, scale = scale, displacement = displacement)
                    args.append(loc)
                    if in_src:
                        dep_r.add(loc)
                    else:
                        dep_w.add(loc)
                    in_mem = False
                    in_mem_phase = 0
                    displacement = 0
                    scale = 1
                    index = None
                    base = None
                token = ""
            elif c == '[' and not in_mem:
                in_mem = True
            elif c == ',' and not in_mem:
                if len(token) != 0:
                    try:
                        args.append(Value(Graph.parseInt(token)))
                    except:
                        loc = Location(reg = token.lower())
                        token = ""
                        args.append(loc)
                        if in_src:
                            dep_r.add(loc)
                        else:
                            dep_w.add(loc)
                in_src = True
            elif (c == '*' or c == '+') and in_mem:
                if not (c == '*' and in_mem_phase == 1) and not (c == '+' and (in_mem_phase == 0 or in_mem_phase == 2)):
                    raise ValueError("ERROR : Incorrect operator : " + str(c))
                in_mem_phase += 1
            else:
                token += c
        if len(token) != 0:
            try:
                args.append(Value(Graph.parseInt(token)))
            except:
                loc = Location(reg = token.lower())
                args.append(loc)
                if in_src:
                    dep_r.add(loc)
                else:
                    dep_w.add(loc)

        if len(args) > 2 or len(args) < 1:
            raise ValueError("ERROR : Wrong number of arguments : " + str(len(args)) + " for line >" + s + "<")

        args.append(None)

        action = Action.from_instr(op, args[0], args[1])
        return (action, dep_r, dep_w, isinstance(action, IntAction))


    """
        Returns a graph from a sequence of instructions saved in the file given by the provided filename
    """
    @staticmethod
    def from_file(filename):
        graph_nodes = set()
        from MemState import MemState
        mem_state = MemState()
        with open(filename) as f:
            nodes = []
            for line in f.readlines():
                if len(line) > 1 and line[0] == '#':
                    continue
                (action, dep_r, dep_w, is_barrier) = Graph.parseLine(line)
                if (action == None) :
                    print("Impossible to parse line \"" + line + "\". skipping it.")
                    continue
                next_mem = action.apply(mem_state)
                node = Node(action)
                mem_state = next_mem
                for (n, dr, dw) in nodes:
                    is_dep = is_barrier
                    if not is_dep:
                        for d in dep_r:
                            if d in dw:
                                is_dep = True
                                break
                        for d in dep_w:
                            if d in dr or d in dw:
                                is_dep = True
                                break
                    if is_dep:
                        node.addBef(n)

                nodes.append((node, dep_r, dep_w))
                graph_nodes.add(node)
        return Graph(graph_nodes)


    def __repr__(self):
        s = "Graph (" + str(self.__count) + " nodes):\n"
        ns = list(self.__roots)
        printed_ns = set()
        while ns:
            n = ns.pop()
            if not n in printed_ns:
                if not n.bef:
                    s += "r: "
                else:
                    s += "   "
                s += str(n) + "\n"
                printed_ns.add(n)
                for n2 in n.aft:
                    ns.append(n2)
        s += "Involved Registers: {"
        for r, i in self.__involvedRegs.items():
            s += "(" + str(r) + ", " + str(i) + "), "
        return s + "}"

    """
        Similarly to the method freshened in Action, modifies this graph to use fresh registers.
        Modifications are done in place.
    """
    def freshen(self):
        new_ir = {}
        last_reass = {}
        equivalence = {}

        ns = list(self.__roots)
        explored_ns = set()
        while ns:
            # updating ns
            n = ns.pop()
            if n in explored_ns:
                continue
            not_yet = False
            for b in n.bef:
                if not b in explored_ns:
                    not_yet = True
            if not_yet:
                continue
            explored_ns.add(n)
            for n2 in n.aft:
                ns.append(n2)

            # updating action
            if isinstance(n.next_action, IntAction):
                last_eq = {}
                for exx, rxx in last_reass.items():
                    last_eq[rxx] = exx
                    if rxx in new_ir:
                        new_ir[exx] = new_ir[rxx]
                        del new_ir[rxx]
                for nbef in n.bef:
                    nbef.next_action = nbef.next_action.reassigned(last_eq)
                    if nbef in self.__roots:
                        self.__roots[nbef] = self.__roots[nbef].reassigned(last_eq)
            n.next_action = n.next_action.freshened(last_reass, equivalence)

            # updating roots
            if n in self.__roots:
                self.__roots[n] = self.__roots[n].reassigned(last_reass)

            # updating involved regs
            n_ir = n.involvedRegs()
            for r in n_ir:
                if r in new_ir:
                    new_ir[r] += 1
                else:
                    new_ir[r] = 1
        self.__involvedRegs = new_ir
        return equivalence
