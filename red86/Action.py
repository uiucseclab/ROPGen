from Location import *
from Value import *

"""
    Internal representation of an instruction. Generic class, should never be instanciated directly.
"""
class Action:
    def __init__(self, dst, src):
        if ((not (isinstance(dst, Location) or isinstance(dst, Value))) or (not (isinstance(src, Location) or isinstance(src, Value)))):
            raise ValueError("Both src and dst must be either Location or Value")
        self.dst = dst
        self.src = src

    """
        Returns an instance of Action subclass corresponding to the op string
    """
    @staticmethod
    def from_instr(op, dst, src):
        op = op.lower()
        if op == "mov":
            return MoveAction(dst, src)
        if op == "add":
            return AddAction(dst, src)
        if op == "sub":
            return SubAction(dst, src)
        if op == "xor":
            return XorAction(dst, src)
        if op == "lea":
            return LeaAction(dst, src)
        if op == "int":
            return IntAction(dst, src)
        if op == "inc":
            return IncAction(dst, src)
        if op == "dec":
            return DecAction(dst, src)
        if op == "xchg":
            return XchgAction(dst, src)
        if op == "and":
            return AndAction(dst, src)
        if op == "or":
            return OrAction(dst, src)
        if op == "neg":
            return NegAction(dst, src)
        else:
            raise ValueError("Could not find instruction " + op)

    """
        Returns a set of all registers involved in the action
    """
    def involvedRegs(self):
        rs = self.dst.involvedRegs()
        rs.update(self.src.involvedRegs())
        return rs

    """
        Returns a dictionnary mapping all r* to e** assignments required for self and other to be equal, or None if no equivalence exists.
    """
    def equivalence(self, other):
        if self == other :
            return {}
        if self.__class__ == other.__class__:
            eq = self.src.equivalence(other.src)
            if eq != None:
                eq2 = self.dst.equivalence(other.dst)
                if eq2 != None:
                    for a, b in eq2.items():
                        if a in eq and eq[a] != b:
                            return None
                    eq.update(eq2)
                else:
                    return None
            return eq
        return None

    """
        Returns a freshened version of self.
        - reassignment : contains a e** to r** mapping of the latest reassignments of e** registers
        - equivalence : contains a r** to e** mapping of all equivalences between the original and the freshened action
    """
    def freshened(self, reassignment, equivalence):
        new_src = self.src.reassigned(reassignment)
        if self.doesOverwriteDst() and self.dst.isReg():
            fresh = Location.freshReg()
            reassignment[self.dst] = fresh
            equivalence[fresh] = self.dst
        new_dst = self.dst.reassigned(reassignment)
        return self.__class__(new_dst, new_src)

    """
        Returns a version of self with all registers reassigned according to the assignment parameter
    """
    def reassigned(self, assignment):
        new_src = self.src.reassigned(assignment)
        new_dst = self.dst.reassigned(assignment)
        return self.__class__(new_dst, new_src)

    """
        returns whether the destination register or memory location is getting overwritten by the action, as opposed to its value getting updated relatively to its previous value.
    """
    def doesoverwritedst(self): # whether it overwrites dst or just updates it
        return false

    """
        returns the state resulting from applying the action to the provided state
    """
    def apply(self, state):
        raise valueerror("error: apply method not implemented for action superclass")

    def __eq__(self, other):
        return other != None and self.src == other.src and self.dst == other.dst and self.__class__ == other.__class__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.dst) + hash(self.src) + hash(self.__class__)


"""
    Represents a mov action
"""
class MoveAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location. was " + str(dst) + " of type "+str(dst.__class__))

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.src))
        return next_state

    def doesOverwriteDst(self):
        return True

    def __repr__(self):
        return "mov "+str(self.dst)+", "+str(self.src) + ""

"""
    Represents an add action
"""
class AddAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).plus(state.getValueAt(self.src)))
        return next_state

    def __repr__(self):
        return "add "+str(self.dst)+", "+str(self.src) + ""

"""
    Represents a sub action
"""
class SubAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).minus(state.getValueAt(self.src)))
        return next_state

    def __repr__(self):
        return "sub "+str(self.dst)+", "+str(self.src) + ""

"""
    Represents a xor action
"""
class XorAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")

    def doesOverwriteDst(self):
        return self.dst == self.src

    def freshened(self, reassignment, equivalence):
        if self.doesOverwriteDst() and self.dst.isReg():
            fresh = Location.freshReg()
            reassignment[self.dst] = fresh
            equivalence[fresh] = self.dst
        new_src = self.src.reassigned(reassignment)
        new_dst = self.dst.reassigned(reassignment)
        return XorAction(new_dst, new_src)

    def reassigned(self, reass):
        new_src = self.src.reassigned(reass)
        new_dst = self.dst.reassigned(reass)
        return self.__class__(new_dst, new_src)

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).xor(state.getValueAt(self.src)))
        return next_state

    def __repr__(self):
        return "xor "+str(self.dst)+", "+str(self.src) + ""

"""
    Represents a lea action
"""
class LeaAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")
        self.ea = src.getEA()
        if self.ea == None:
            raise ValueError("ERROR: src must be a pointer to memory in lea instruction")

    def doesOverwriteDst(self):
        return True

    def apply(self, state):
        if self.ea != None:
            dst = self.ea
            next_state = state.copy()
            next_state.setValueAt(self.dst, self.ea)
            return next_state
        else:
            raise ValueError("ERROR: src must be a pointer to memory in lea instruction")
            return None

    def __repr__(self):
        return "lea "+str(self.dst)+", "+str(self.src) + ""


"""
    Represents an int action
"""
class IntAction(Action):
    def __init__(self, dst, src = None):
        Action.__init__(self, dst, Value(0))
        if src != None:
            raise ValueError("ERROR: int takes only one argument")
        if not isinstance(dst, Value):
            raise ValueError("ERROR: dst must be a Value")

    def involvedRegs(self):
        return {}

    def apply(self, state):
        next_state = state.copy()
        return next_state

    def freshened(self, reass, eq):
        return self

    def reassigned(self, ass):
        return self

    def equivalence(self, other):
        if isinstance(other, IntAction) and self.dst == other.dst:
            return {}
        else:
            return None

    def __repr__(self):
        return "int "+str(self.dst)+""



"""
    Represents an inc action
"""
class IncAction(Action):
    def __init__(self, dst, src = None):
        Action.__init__(self, dst, Value(0))
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a Location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).plus(Value(1)))
        return next_state

    def __repr__(self):
        return "inc "+str(self.dst)+""


"""
    Represents a dec action
"""
class DecAction(Action):
    def __init__(self, dst, src = None):
        Action.__init__(self, dst, Value(0))
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a Location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).plus(Value(-1)))
        return next_state

    def __repr__(self):
        return "dec "+str(self.dst)+""


"""
    Represents an xchg action
"""
class XchgAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if isinstance(dst, Value) or isinstance(src, Value):
            raise ValueError("ERROR: dst and src must be a Location")

    def apply(self, state):
        next_state = state.copy()
        temp_val = state.getValueAt(self.dst)
        next_state.setValueAt(self.dst, state.getValueAt(self.src))
        next_state.setValueAt(self.src, temp_val)
        return next_state

    def __repr__(self):
        return "xchg "+str(self.dst)+", "+str(self.src)+""


"""
    Represents an and action
"""
class AndAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).and_(state.getValueAt(self.src)))
        return next_state

    def __repr__(self):
        return "and "+str(self.dst)+", "+str(self.src) + ""

"""
    Represents an or action
"""
class OrAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, src)
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).or_(state.getValueAt(self.src)))
        return next_state

    def __repr__(self):
        return "or "+str(self.dst)+", "+str(self.src) + ""

"""
    Represents a neg action
"""
class NegAction(Action):
    def __init__(self, dst, src):
        Action.__init__(self, dst, Value(0))
        if not isinstance(dst, Location):
            raise ValueError("ERROR: dst must be a location")

    def apply(self, state):
        next_state = state.copy()
        next_state.setValueAt(self.dst, state.getValueAt(self.dst).neg())
        return next_state

    def __repr__(self):
        return "neg "+str(self.dst)+""
