"""
    Represents a location on the machine. Can be either a register, or a place in actual memory.
"""
class Location:
    def __init__(self, reg = None, atAddr = None, base = None, index = None, scale = 1, displacement = 0):
        self.reg = None # string
        self.addr = None # Value
        self.mem = None # (Value, Value, int, int)
        if reg == None and atAddr == None:
            self.mem = (base, index, scale, displacement)
        elif reg == None and index == None and scale == 1 and base == None and displacement == 0:
            self.addr = atAddr
        elif atAddr == None and index == None and scale == 1 and base == None and displacement == 0:
            self.reg = reg
        else:
            raiseValueError("Cannot create location with provided arguments. Too many argument")


    """
        Similarly to the involvedRegs method of Action, returns a set of all registers involved with this value
    """
    def involvedRegs(self):
        if self.reg != None:
            return set([self])
        if self.addr != None:
            return self.addr.involvedRegs()
        if self.mem != None:
            s = self.mem[0].involvedRegs()
            if self.mem[1] != None:
                s.update(self.mem[1].involvedRegs())
            return s
        return set()

    """
        Similarly to the equivalence method in Action, returns the register equivalence between self and other
    """
    def equivalence(self, other):
        if not isinstance(other, Location):
            return None
        if self == other:
            return {}
        if self.reg and other.reg:
            if self.reg[0] == 'r' and other.reg[0] != 'r':
                return {self: other}
            elif self.reg[0] != 'r' and other.reg[0] == 'r':
                return {other: self}
            else:
                return None
        if self.addr and other.addr:
            return self.addr.equivalence(other.addr)
        if self.mem and other.mem:
            if self.mem[2] != other.mem[2] or self.mem[3] != other.mem[3]:
                return None
            eq = self.mem[0].equivalence(other.mem[0])
            if eq == None:
                return None
            if self.mem[1] and other.mem[1]:
                eq2 = self.mem[1].equivalence(other.mem[1])
                if eq2 != None:
                    for a, b in eq2.items():
                        if a in eq and eq[a] != b:
                            return None
                    eq.update(eq2)
                else:
                    return None
            elif self.mem[1] or other.mem[1]:
                return None
            return eq
        else:
            return None


    """
        Similarly to the reassigned method in Action, returns a new value with registers reassigned according to the assignment parameter
    """
    def reassigned(self, reass):
        if self in reass:
            return Location(reg = reass[self].reg)
        elif self.reg != None:
            return Location(reg = self.reg)
        if self.addr != None:
            return Location(atAddr = self.addr.reassigned(reass))
        if self.mem != None:
            new_base = self.mem[0].reassigned(reass)
            new_index = None
            if self.mem[1] != None:
                new_index = self.mem[1].reassigned(reass)
            return Location(base = new_base, index = new_index, scale = self.scale, displacement = self.displacement)
        raise ValueError("Impossible to reassign location " + str(self))

    """
        Returns whether location is a register or not
    """
    def isReg(self):
        return self.reg != None

    """
        Returns the effective address of this location, if applicable
    """
    def getEA(self):
        from Value import Value
        if self.reg != None:
            return Value.atLocation(self)
        elif self.addr != None:
            return self.addr
        else:
            return Value.ea(base = self.mem[0], index = self.mem[1], scale = self.mem[2], displacement = self.mem[3])

    __uid = 0

    """
        Returns a fresh register of the form r*
    """
    @staticmethod
    def freshReg():
        Location.__uid += 1
        return Location(reg = "r"+str(Location.__uid - 1))

    def __eq__(self, other):
        return isinstance(self, other.__class__) and self.reg == other.reg and (self.mem == other.mem) and self.addr == other.addr

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.reg)+hash(self.mem) + hash(self.addr)

    def __repr__(self):
        if self.reg != None:
            return str(self.reg)
        elif self.addr != None:
            return "l[" + str(self.addr) + "]"
        elif self.mem != None and len(self.mem) == 4:
            s = "l["+str(self.mem[0])
            if self.mem[1] != None:
                s += " + " + str(self.mem[1])
                if self.mem[2] != 1:
                    s += " * " + str(self.mem[2])
            if self.mem[3] != 0:
                s += " + " + str(self.mem[3])
            s += "]"
            return s
        else:
            return "N/A"
