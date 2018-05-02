from Value import *
from Location import *
from MemState import *
from Action import *
from Graph import *
from Node import *


def valueTests():
    v = Value()
    print(v)
    v2 = Value(5)
    v3 = Value(7)
    v4 = Value.ea(v2, v3, 3, 2)
    v5 = Value.atLocation(Location(atAddr = v4))
    v6 = v5.plus(v4)
    v7 = v3.plus(v6)
    v8 = v7.plus(Value.atLocation(Location(atAddr = v2)))
    assert(str(v2) == "0x5")
    assert(str(v3) == "0x7")
    assert(str(v4) == "0x17")
    assert(str(v5) == "[0x17]")
    assert(str(v6) == "0x17 + [0x17]")
    assert(str(v7) == "0x1e + [0x17]")
    assert(str(v8) == "0x1e + [0x5] + [0x17]")

    print("Success for Values")

def equivalenceTests():

    v1 = Value(5)
    v2 = Value(7)
    r1 = Location(reg = "eax")
    r2 = Location(reg = "r1")
    r3 = Location(reg = "ebx")
    r4 = Location(reg = "r2")
    vl1 = Value.atLocation(r1)
    vl2 = Value.atLocation(r2)
    vl3 = Value.atLocation(r3)
    vl4 = Value.atLocation(r4)
    l3 = Location(base = vl1)
    l4 = Location(base = vl2)
    l5 = Location(base = vl1, index = vl3)
    l6 = Location(base = vl2, index = vl4)
    vl5 = Value.atLocation(l5)
    vl6 = Value.atLocation(l6)
    a1 = AddAction(r1, r3)
    a2 = AddAction(r2, r2)
    m1 = MemState()
    m2 = MemState()
    m1.setValueAt(r1, vl5)
    m1.setValueAt(r3, v1)
    m2.setValueAt(r2, vl6)
    m2.setValueAt(r4, v1)


    print(v1.equivalence(v2))
    print(v1.equivalence(Value(5)))
    print(r1, r2, r1.equivalence(r2))
    print(r3, r4, r3.equivalence(r4))
    print(l5, l6, l5.equivalence(l6))
    print(a1, a2, a1.equivalence(a2))
    print(m1, m2, m1.equivalence(m2))

    a1 = XorAction(r1, r1)
    a2 = XorAction(r1, r1)
    print(a1, a2, a1.equivalence(a2))


def actionTests():
    s = MemState()
    eax = Location(reg = "eax")
    ebx = Location(reg = "ebx")
    esi = Location(reg = "esi")
    one = Value(1)
    twenty = Value(17)
    at_one = Value.atLocation(Location(atAddr = one))
    move1 = MoveAction(eax, one)
    move2 = MoveAction(ebx, eax)
    move3 = MoveAction(eax, twenty)
    xor1 = XorAction(eax, Location(atAddr = one))
    add1 = AddAction(eax, ebx)
    add2 = AddAction(eax, at_one)
    sub1 = SubAction(eax, ebx)
    sub2 = SubAction(eax, at_one)
    print(XorAction(eax, eax))
    print(XorAction(eax, eax).apply(MemState()))

    print("\n Starting from state :")
    print(s)

    print(move1)
    s = move1.apply(s)
    print(s)

    print(move2)
    s = move2.apply(s)
    print(s)

    print(move3)
    s2 = move3.apply(s)
    print(s)
    print(s2)

    print("moving 100 to one")
    moveatone = MoveAction(Location(atAddr = one), Value(100))
    print(moveatone)
    st = moveatone.apply(s2)
    print(st)

    print("xoring")

    print(xor1)
    s3 = xor1.apply(st)
    print(s3)

    print("\nstarting back from state "+str(s))
    print(add1)
    print(add1.apply(s))
    print(add2)
    print(add2.apply(s))
    print(sub1)
    print(sub1.apply(s))
    print(sub2)
    print(sub2.apply(s))

    print("\nstarting from MemState() again :")
    lea1 = LeaAction(Location(base = one), Value.atLocation(Location(atAddr = at_one)))
    #lea1 = LeaAction(Location(base = one), at_one)
    s5 = lea1.apply(MemState())
    print(lea1)
    print(s5)
    add = AddAction(Location(base = one), Value(42))
    s6 = add.apply(s5)
    print(add)
    print(s6)
    add = AddAction(eax, Location(base = one))
    s7 = add.apply(s6)
    print(add)
    print(s7)
    add = AddAction(Location(base = one), Value(42))
    s8 = add.apply(s7)
    print(add)
    print(s8)
    add = AddAction(eax, Location(base = one))
    s9 = add.apply(s8)
    print(add)
    print(s9)

    assert(XorAction(eax, eax).doesOverwriteDst())
    assert(not XorAction(eax, ebx).doesOverwriteDst())
    assert(MoveAction(eax, ebx).doesOverwriteDst())
    assert(not AddAction(eax, ebx).doesOverwriteDst())
    assert(LeaAction(eax, at_one).doesOverwriteDst())

    print(IntAction(Value(2)))


def graphTests():
    g = Graph.from_file("input.txt")
    print(g)
    print("roots:")
    for r, s in g.getRoots().items():
        print(r, s)
    print("without last root : " + str(r))
    rootless_g = g.withoutRoot(r)
    print("new roots:")
    for r, s in rootless_g.getRoots().items():
        print(r, s)
    print(rootless_g) # TODO error here
    print("freshened :")
    eq = g.freshen()
    print(g)
    print("equivalences : " + str(eq))
    for r in g.getRoots():
        break
    print("remove root from freshened : "+str(r))
    print(g.withoutRoot(r))

def reassTests():
    eax = Location(reg = "eax")
    ebx = Location(reg = "ebx")
    r1 = Location(reg = "r1")
    a = XorAction(eax, ebx)
    b = a.reassigned({eax: r1})
    print(a)
    print(b)




valueTests()
#equivalenceTests()
#actionTests()
#graphTests()
#reassTests()
