
"""
    Represents a node in the graph of instructions
"""
class Node:
    def __init__(self, next_action, dst = None):
        self.next_action = next_action
        # Keeps track of the dst location for AStar to know which gadgets to prefer over others
        if dst == None and next_action:
            self.dst = self.next_action.dst
        elif dst != None:
            self.dst = dst
        else:
            raise ValueError("If a node has no action, it at least needs a dst : " + str((next_action, dst)))
        self.aft = set()
        self.bef = set()

    """
        Adds a read/write dependency, where other must happend before self
    """
    def addBef(self, other):
        if isinstance(other, Node):
            self.bef.add(other)
            other.aft.add(self)
        else:
            self.bef.update(other)
            for o in other:
                o.aft.add(self)

    """
        Adds a read/write dependency, where other must happend before self
    """
    def addAft(self, other):
        other.addBef(self)


    """
        Similarly to the involvedRegs method of Action, returns a set of all registers involved with this value
    """
    def involvedRegs(self):
        if self.next_action == None:
            return {}
        return self.next_action.involvedRegs()

    """
        Returns a copy of this node, without any dependencies
    """
    def cleanCopy(self):
        return Node(self.next_action, self.dst)

    def __repr__(self):
        s = "<Node : "+ str(self.next_action)
        if self.next_action == None:
            s += "(dst is " + str(self.dst) + ")"
        s += ">"
        return s
