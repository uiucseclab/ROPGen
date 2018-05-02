# ROPGen

> 1. [Introduction](#introduction)
>    1. [Return Oriented Programming](#rop)
> 1. [ROPGen](#ropgen)
>    1. [red86](#red86)
>    1. [Finding Gadgets](#findinggadgets)
>    1. [Memory State](#memorystate)
>    1. [Choosing gadgets](#choosinggadgets)
> 1. [ropgen.py](#ropgenpy)
> 1. [Limitations](#limitations)
>    1. [More Gadgets](#moregadgets)
>    1. [Longer Gadgets](#longergadgets)
>    1. [Pop Gadgets](#popgadgets)
>    1. [Jump Gadgets](#jumpgadgets)

<a name="introduction"></a>
## Introduction
<a name="rop"></a>
### Return Oriented Programming
On poorly secured systems, buffer overflow vulnerabilities can be easily exploited by overwriting the return address with a pointer to a chosen sequence of instructions, often saved on the stack, called the **Shellcode**. However most systems now implement Address Space Layout Randomization to randomize instruction addresses, canaries to prevent overwriting return addresses, or Executable Stack Protection (ESP) to prevent any (shell)code saved on the stack from being executed.

In this project, I am focusing on the Return Oriented Programming technique that circumvents ESP. Though the return address must still be overwritten, no actual instructions have to be saved onto the stack. Instead, the return address is overwritten by a series of pointers to instructions in the binary that are immediately followed by a `ret` instruction. One such pointer to the binary (usually in `libc`) is called a **gadget**. However, since canaries and ASLR would prevent the specific ROP attacks I am focusing on in this project, I had to configure my machine to disable ASLR, and the binaries are compiled without canaries.

<a name="ropgen"></a>
## ROPGen
Finding such gadgets in the binary using objdump, hexdump and other tools alike is very tedious, as most instructions one might want to execute will not be available in the original binary in the required form of a gadget (i.e. immediately followed by a `ret` instruction). The idea with this project is to allow the attacker to write the sequence of instructions they want to find, and let the program look for them in the binary, potentially reorganizing them or finding different but equivalent sequences of instructions.

<a name="red86"></a>
### red86
When the attacker provides the sequence of instructions they want to find, the program will parse each one of them, generating an internal representation of that code in the form of a graph, where each node is an instruction (internally referred to as an **Action**) and each edge is a read/write dependency indicating that one instruction must be executed before the next. This however means that only instructions that have an internal representation are understood by the program, which is one first reason why it is not as efficient as I would have liked it to be. Those recognized instructions are :

- `mov dst, src/imm`
- `xor dst, src/imm`
- `and dst, src/imm`
- `or  dst, src/imm`
- `add dst, src/imm`
- `sub dst, src/imm`
- `inc dst`
- `dec dst`
- `neg dst`
- `xchg dst, src`
- `lea dst, src`
- `int imm`

where `dst` and `src` are either registers, or memory addresses of the form `[reg]`, `[reg + reg * imm]` or `[reg + reg * imm + imm]`, and `imm** is any immediate value. This reduced set of x86 instructions will be referred to as **red86**.

The second step after parsing the attacker's input code is to "**freshen**" it. Freshening will replace all registers in the graph representation of the code with "_anonymous_" registers of the form `ri` where `i` starts from `0`. This means that any register in the code that does not need to be specific will get replaced with an anonymous register. For example:

```
mov eax, 0x10
mov ebx, 0x20
add eax, ebx
xor ebx, ebx
int 0x80
```
will be rewritten as

```
mov r0, 0x10
mov r1, 0x20
add r0, r1
xor r2, r2   ; ebx gets overwritten, so it can be a different register
int 0x80
```
However, because some instructions do care about specific registers, like the `int` instruction, those registers will remain specific:

```
mov eax, 0x10  ; eax will not get overwritten again before the call to int, so it stays specific
mov r1, 0x20   ; However ebx will get overwritten, so this one can stay anonymous
add eax, r1
xor ebx, ebx
int 0x80
```

Again, because registers need to be understood by the parser, only a subset of those available in x86 exist in _red86_:

- `eax`
- `ebx`
- `ecx`
- `edx`
- `esi`
- `edi`
- `ebp`

<a name="findinggadgets"></a>
### Finding Gadgets
In order to find gadgets from the binary, the program makes use of the `pwntools` library on python. Going over all bytes of the `.text` section of the binary, the program will look for `0xc3` bytes (opcode for `ret`) and check the instructions preceding it, trying to disassemble them using pwntools and then parse them into their internal _Action_ representation. The virtual address at which the gadget was found will also be saved as they will be used in the final output of the program.

<a name="memorystate"></a>
### Memory State
Because the idea is for this program to be clever enough to find different sequences of instructions that lead to the same result, it also needs an internal representation of the memory, which is taken care of by the `MemState`, `Location` and `Value` classes:

- The `Location` class represents either a register, or a place in memory.
- The `Value` class contains an immediate integer, and a set of `Location`s with multiplicity. Ideally, this set should always be empty, but if the attacker's input code starts with `add eax, 1` or `mov eax, [ebx + 0x8]` for example, the values contained in `eax` and `[ebx + 0x8]` respectively will not be known and will hence have to be referred to using their `Location`.
- Finally, the `MemState` class keeps a map of `Location`s to `Value`s. Additionally, all `Action`s have an `apply` method that returns a new `MemState` resulting from applying the given action to it. For instance, the following piece of code will pass the assert test:

```
eax = Location(reg = "eax")
s0 = MemState({eax : Value(5)})
s1 = AddAction(eax, Value(1)).apply(s0)
assert(s1, MemState({eax : Value(6)})
```

<a name="choosinggadgets"></a>
### Choosing Gadgets
In order to choose which gadgets to pick from the set of gadgets found in the binary, the program uses something similar to an A* algorithm. It keeps track of a priority queue called the **frontier** that ranks all states reachable from the current memory state from most to least similar to the attacker's input code. It also knows of all the "roots" of the graph representation of the code, i.e. all instructions that could be executed next without violating any memory dependencies. Memory states in the frontier that derive from the exact instruction specified by the attacker's input code get the highest rank, followed by states that are equivalent to one of the roots but use a different gadget.

When comparing Actions with the attacker's input code, or memory states with roots of the graph, and because of these _anonymous_ registers, `Action`s and `MemState`s are most of the time compared using their `equivalence` method. This method returns a set of `(exx, rxx)` pairs, where `exx` is an original, specific register, and `rxx` is an anonymous one. Those pairs represent which `rxx` to `exx` assignments must be made for the two actions or states to be identical. For example, the following assertions would both pass:
```
eax = Location(reg = "eax")
ebx = Location(reg = "ebx")
e_ptr = Location(base = ebx, displacement = 0x4)

r0 = Location(reg = "r0")
r1 = Location(reg = "r1")
r_ptr = Location(base = r1, displacement = 0x4)

assert( AddAction(e_ptr, eax).equivalence(AddAction(r_ptr, r0)), {r0: eax, r1: ebx})

assert( MemState({eax: Value(0), ebx: Value.atLocation(e_ptr)}
       .equivalence(
        MemState({r0 : Value(0), r1 : Value.atLocation(r_ptr)}))), {r0: eax, r1: ebx})
```

 The program needs to keep track of these assignments, and make sure they stay coherent throughout the final sequence of gadgets. It will also need to "free" these assignments when an `rxx` register stops being used for the rest of the code, hence allowing the associated `exx` register to be reused for a subsequent `rxx`. For example the following, very simple shellocde:
```
xor r0, r0
xor r1, r1
```
could become the following sequence of gadgets:
```
xor eax, eax
xor eax, eax
```
Because after the first instruction, `r0` is never used again, `eax` will never be used again either and can therefore be reused for another anonymous register, here `r1`.

<a name="ropgenpy"></a>
# ropgen.py
The main program, `ropgen.py` can take the following command line arguments:

- `-i=<filename>` or `--input=<filename>` : specifies the name of the file containing the input code in `red86`. Lines starting with a `#` will be ignored.
- `-o=<filename>` or `--output=<filename>` : specifies the name of the file in which to save the string that should be given as input to the vulnerable program.
- `-b=<filename>` or `--binary=<filename>` **[required]** : specifies the name of the binary to attack.
- `-a=<filename>` or `--avoid=<filename>` : specifies the name of a text file containing one byte per line that should be avoided, in the form `0x**`. For instance, most code injection attacks take advantage of `scanf` or functions that will cut the string when encountering a space `0x20`, an end of file `0x00` or a tab `0x09`. Specifying those in the `avoid` file will make sure they never occur in the final output string.
- `-p=<integer>` or `--padding=<integer` : specifies the number of bytes separating the start of the vulnerable buffer on the stack, and the return address. Is used to determine the size of the padding that allows the first gadget to overwrite the return address on the stack.
- `-v` or `--verbose` : when specified, will output more descriptive text about what the program is doing.

Only the binary file is required at first. The reason for this is that the first task `ropgen.py` does is to retrieve gadgets from the provided binary. After that, it prompts the user with the following options

```text
What now ?
    c - See current configuration
    g - See Found Gadgets
    i - Change filename of input instructions
    o - Change filename of output file
    a - Change filename of bytes to avoid
    p - Change number of bytes of padding between buffer and return address
    q - Exit
    s - Start generating!
```
At this stage, the user is expected to hit one of the above letters and press enter. The program will refuse to start generating until it has a filename for the input instructions and the output file. The default padding is zero and the bytes to avoid is an empty set.

Note that, at this stage, the program has saved all the found gadgets into the `.rop_cache/<hash>` file, where `<hash>` is the _md5_ hash of the binary. This avoids having to go through the quite lengthy process of finding gadgets in the same binary every time.

Allowing users to specify their input instructions and bytes to avoid at this stage rather than as soon as they start running `ropgen.py` is meant to give them the opportunity to change them depending on the gadgets that were found. For instance, if no `xor` gadgets were found, the user might want to modify their input code accordingly.



<a name="limitations"></a>
# Limitations
Although I intended this program to be able to generate a correct sequence of gadgets for any given piece of assembly code, it is still missing a few features that limit its capabilities. I do have a clear idea of how to implement most of them, but they would also require lots of redesign and refactoring.

<a name="moregadgets"></a>
#### More Gadgets
This program works well only when it has all necessary gadgets available, or if it suffices to deviate for a single instruction. If it cannot find a gadget equivalent to an instruction from the input code, it will still be able to find another gadget that produces the same state, if it exists. For instance, if `eax` is set to `0` in the current memory state, and the input code asks for a `mov eax, 0x1` instruction, this program will be able to efficiently find a `add eax, 0x1` instruction if the former is missing. However, it will not be able to replace a single missing instruction from the input code with multiple gadgets. For example, if it wants to find `add eax, 0x2` but only has `add eax, 0x1` gadgets, it will not simply use the latter twice. I had a working instance of my program that could solve this particular problem, but would sometimes get stuck in infinite loops for other inputs for which straight forward solutions could exist.

<a name="longergadgets"></a>
#### Longer Gadgets
This program also does not try to find gedgets that execute multiple instructions at once before returning. Although this could help unlock some tricky situations, it might end up skipping a state from the graph, or producing a different memory state that only the user would know is ok, but the program would reject. For instance, if the only gadget containing `add eax, 0x2` is `add eax, 0x2; mov edx, 0x10; ret`, using this gadget would end up updating the value of `edx`, which my program would consider an invalid memory state, even though the user might know that this difference irrelevent. In order for the program to be able to know on its own when an unsollicited modification of a register is acceptable, it would have to reorganize the graph of remaining instructions to take care of new dependencies each time, while keeping track of dependencies of already found gadgets. Although I have a fair idea of how to implement this, it would represent a very important amount of work for which I unfortunately haven't had time this semester. I have already spent more time on this project than intended because of how fun it was, but I am thinking of working on it during summer break.

<a name="popgadgets"></a>
#### Pop Gadgets
Another feature I was planning to add but ended up not having enough time to implement was the use of the stack. In ROP, when arbitrary values are needed, it is sometimes useful to add them on the stack, between two gadgets, and then call a `pop` gadget to retrieve them. In order to allow this, _red86_ would need a syntax to specify adding something on the stack, a `PopAction` class would have to be added, and the `MemState` class would have to be able to represent this behavior.

<a name="jumpgadgets"></a>
#### Jump Gadgets
Finally, one feature I was not planning on implementing, but I know would have been very useful, is jump and conditional jump instructions. I know this has to be possible, but it would require this program to have an even deeper understanding of the memory's state with carry, zero, overflow flags. It would also need to find relative jumps with the exact number of bytes corresponding to the correct number of gadgets to jump over. While this is not impossible, I again knew that it was a too big feature to work on.

<br>
<br>
Even though most of these missing features would require a lot of work, I believe my current implementation and the Action and MemoryState representations are generic enough to make the job slightly easier. In fact I was planning on adding most of these features before I realized how much work I was putting into it, so the core of the code was made with these features in mind.


# Testing Environment
### Configuration
I tested my program on a 64-bit Ubuntu Virtual Machine. In order for Return Oriented Attacks to work on a buffer overflow vulnerable program, ASLR must be disabled on the machine by running 

```echo 0 | sudo tee /proc/sys/kernel/randomize_va_space```

### Prerequisites
This program requires the `pwntools` library to work. On an ubuntu machine, and based on the instructions given on `pwntools`' <a href="http://docs.pwntools.com/en/stable/install.html">documentation</a>, run the following commands to install `pwntools`:

```text

$ sudo apt-get install software-properties-common
$ sudo apt-add-repository ppa:pwntools/binutils
$ sudo apt-get update
$ sudo apt-get install binutils-$(arch)-linux-gnu

$ sudo apt-get install python2.7 python-pip python-dev git libssl-dev libffi-dev build-essential
$ pip install --upgrade pip
$ pip install --upgrade pwntools
```

### Example usage
This repo contains a simple `test.c` program that is vulnerable to a buffer-overflow attack, along with a `Makefile` that will allow you to compile it into a binary called `teststatic` using `make`. It also contains a very, very simple sequence of instructions in `input.txt` as well as a set of bytes to avoid in `avoid.txt`. In order to attack this binary, an example command would be the following:

```text
python ropgen.py --input=input.txt --output=out.txt --avoid=avoid.txt --binary=teststatic --padding=76
```

Where I assume the padding has been determined to be 76 using a tool like `gdb` on the target binary `teststatic`. If the generation succeeds (which might not necessarily be the case since the addresses of each gadget are machine dependent, and some addresses might be filtered out because of the `avoid.txt` file), one could get the instructions in `input.txt` to be executed on behalf of the `statictest` binary by simply running:

```
./teststatic < out.txt
```

Although the gadgets found by `ropgen.py` will be executed correctly, which can be verified using `gdb`, the sample code provided in `input.txt` will not achieve anything, and is only intended to be a proof of concept. More complex sequences of instructions might be possible on larger binaries.
