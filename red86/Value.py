from Location import *

"""
    Represents a value. Can be a simple immediate, or a more complex representation for values that are unknown before runtime
"""
class Value:
    def __init__(self, imm = 0):
        self.__off = imm
        self.__mem = {}

    """
        Similarly to the equivalence method in Action, returns the register equivalence between self and other
    """
    def equivalence(self, other):
        if self.__class__ != other.__class__:
            return None
        if self == other:
            return {}
        if self.__off != other.__off:
            return None
        if len(self.__mem) != len(other.__mem):
            return None
        eq = {}
        for l, i in self.__mem.items():
            found = False
            for ol, oi in other.__mem.items():
                if i == oi:
                    eq2 = l.equivalence(ol)
                    if eq2 != None:
                        found = True
                        impossible = False
                        for a, b in eq2.items():
                            if a in eq and eq[a] != b:
                                found = False
                                impossible = True
                                break
                        if found and not impossible:
                            eq.update(eq2)
                            break
            if not found:
                return None
        return eq


    """
        Similarly to the reassigned method in Action, returns a new value with registers reassigned according to the assignment parameter
    """
    def reassigned(self, assignment):
        new_mem = {}
        for v, mult in self.__mem.items():
            new_mem[v.reassigned(assignment)] = mult
        new_v = Value(self.__off)
        new_v.__mem = new_mem
        return new_v


    """
        Returns the result of adding self and other
    """
    def plus(self, other):
        new_v = Value()
        new_v.__off += self.__off + other.__off
        new_v.__mem.update(self.__mem.copy())
        for v, mult in other.__mem.items():
            if v in new_v.__mem:
                new_v.__mem[v] += mult
            else:
                new_v.__mem[v] = mult
            if new_v.__mem[v] == 0:
                del new_v.__mem[v]
        return new_v

    """
        Returns the result of adding other from self
    """
    def minus(self, other):
        new_v = Value()
        new_v.__off += self.__off - other.__off
        new_v.__mem.update(self.__mem.copy())
        for v, mult in other.__mem.items():
            if v in new_v.__mem:
                new_v.__mem[v] -= mult
            else:
                new_v.__mem[v] = -mult
            if new_v.__mem[v] == 0:
                del new_v.__mem[v]
        return new_v

    """
        Returns the result of xoring self and other
    """
    def xor(self, other):
        new_v = Value()
        if self == other:
            new_v.__off = 0
        elif self.isKnown() and other.isKnown() :
            new_v.__off = self.__off ^ other.__off
        else:
            new_v.__mem = {("xor", self.copy(), other.copy()): 1}
        return new_v

    """
        Returns the result of an and on self and other
    """
    def and_(self, other):
        new_v = Value()
        if self == other:
            new_v.__off = self.__off
        elif self.isKnown() and other.isKnown() :
            new_v.__off = self.__off & other.__off
        else:
            new_v.__mem = {("and", self.copy(), other.copy()): 1}
        return new_v

    """
        Returns the result of an or on self and other
    """
    def or_(self, other):
        new_v = Value()
        if self == other:
            new_v.__off = self.__off
        elif self.isKnown() and other.isKnown() :
            new_v.__off = self.__off | other.__off
        else:
            new_v.__mem = {("or", self.copy(), other.copy()): 1}
        return new_v

    """
        Returns the result of negating self
    """
    def neg(self):
        new_v = Value()
        if self.isKnown():
            new_v.__off = - self.__off

        for v, mult in self.__mem.items():
            new_v.__mem[v] = -mult

        return new_v

    """
        Returns whether the value is known before runtime
    """
    def isKnown(self):
        return not self.__mem

    """
        Returns the effective address of this value, if applicable.
    """
    def getEA(self):
        if len(self.__mem) == 1:
            return self.__mem.items()[0][0].getEA()
        else:
            return None

    """
        Returns a copy of self
    """
    def copy(self):
        new_v = Value(self.__off)
        new_v.__mem = self.__mem.copy()
        return new_v

    """
        Similarly to the involvedRegs method of Action, returns a set of all registers involved with this value
    """
    def involvedRegs(self):
        s = set()
        for v, i in self.__mem.items():
            s.add(v.involvedRegs())
        return s

    """
        Returns a value representing the effective address (base + index * scale + displacement)
    """
    @staticmethod
    def ea(base, index = None, scale = 1, displacement = 0):
        if not isinstance(base, Value):
            raise ValueError("base " + str(base) + " is not a value!")
        v = Value(displacement)
        if index:
            for i in range(scale):
                v = v.plus(index)
        v.plus(base)
        return v

    """
        Returns the value at the provided location
    """
    @staticmethod
    def atLocation(location):
        if not isinstance(location, Location) :
            raise ValueError("atLocation takes a Location")
        v = Value(0)
        v.__mem = {location: 1}
        return v

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        if self and other :
            return self.__off == other.__off and self.__mem == other.__mem
        elif self or other :
            return False
        else :
            return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        h = 0
        for v, i in self.__mem.items():
            h += hash((v, i))
        return hash(self.__off) + h

    def __repr__(self):
        if self.__mem :
            s = ""
            if self.__off != 0:
                s += hex(self.__off)
            for v, i in self.__mem.items():
                if s != "":
                    s += " + "
                if i != 1:
                    s += str(i) + " * "
                if isinstance(v, Location) and not v.isReg():
                    s += str(v)[1:]
                else:
                    s += str(v)
            return s
        else:
            return hex(self.__off)
