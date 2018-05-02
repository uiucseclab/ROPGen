from Value import Value
from Location import Location

"""
    Represents a state of memory, which includes actual memory and registers
"""
class MemState:
    def __init__(self, mem = {}):
        self.__mem = mem.copy()

    def copy(self):
        return MemState(self.__mem)

    """
        Returns the value saved at the given location. If no value is known at that location, returns Value.atLocation(location)
    """
    def getValueAt(self, location):
        if isinstance(location, Value):
            return location
        if not location in self.__mem:
            return Value.atLocation(location)
        return self.__mem[location]

    """
        Sets the value at location to new_value
    """
    def setValueAt(self, location, new_value):
        if isinstance(new_value, Location):
            raise ValueError("ERROR: cannot set value to be a Location. Must be a value.")
        self.__mem[location] = new_value

    """
        Similarly to the equivalence method in Action, returns the register equivalence between self and other
    """
    def equivalence(self, other):
        final_eq = {}
        mem1 = self.__mem.copy().items()
        mem2 = other.__mem.copy().items()

        if len(mem1) != len(mem2) :
            return None

        while mem1:
            l1, v1 = mem1[0]
            found = False
            for l2, v2 in mem2:
                eq = l1.equivalence(l2)
                if eq != None:
                    eq2 = v1.equivalence(v2)
                    impossible = False
                    if eq2 == None:
                        continue
                    for r, e in eq.items():
                        if r in eq2 and e != eq2[r]:
                            impossible = True
                            break
                    if impossible:
                        continue
                    eq.update(eq2)
                    impossible = False
                    for r, e in eq.items():
                        if r in final_eq and e != final_eq[r]:
                            impossible = True
                            break
                    if impossible:
                        continue
                    found = True
                    mem1.remove((l1, v1))
                    mem2.remove((l2, v2))
                    final_eq.update(eq)
                    break
            if not found:
                return None
        return final_eq

    """
        Similarly to the reassigned method in Action, returns a new value with registers reassigned according to the assignment parameter
    """
    def reassigned(self, reass):
        new_mem = {}
        for l, v in self.__mem.items():
            new_mem[l.reassigned(reass)] = v.reassigned(reass)
        return MemState(mem = new_mem)

    def __repr__(self):
        s = "<Memory : "
        for l, v in self.__mem.items():
            s += ("" + str(l) + " : "+str(v) + ", ")
        return s + ">"

    def __eq__(self, other):
        return self.equals(other)
    def __ne__(self, other):
        return not self.__eq__(other)

    def equals(self, other):
        return self.__mem == other.__mem

