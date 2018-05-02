import sys
import os
from Graph import *
from pwn import *


cache_dir = "./.rop_cache"

# Extract gadgets from binary
def extract_binary(filename):
    # Verifying existance or creating cache folder
    cache_exists = os.path.isdir(cache_dir)
    if cache_exists:
        pass
    else:
        os.makedirs(cache_dir)

    if not os.path.exists(filename):
        raise ValueError("Could not find file " + filename)

    # Trying to use cached data. Otherwise, read from binary
    hsh = md5filehex(filename)

    if os.path.exists(cache_dir + "/" + hsh):
        extracted = retrieve_from_cache(hsh)
    else:
        extracted = retrieve_from_binary(filename)
        save_to_cache(extracted, hsh)

    return extracted

# Extract gadgets from cached data
def retrieve_from_cache(hsh):
    with open(cache_dir + "/" + hsh, 'r') as f:
        extracted = Extracted()
        lines = f.readlines()
        for line in lines:
            elems = line.split(":")
            instr = elems[0]
            elems1 = elems[1].strip()[1:-1].split(",")
            parsed = Graph.parseLine(instr)
            for e in elems1:
                addr = int(e.strip())
                extracted.addGadget(parsed[0], addr)
    return extracted

# Save extracted data to cache
def save_to_cache(extracted, hsh):
    with open(cache_dir + "/" + hsh, 'w') as f:
        for action, addr in extracted.data.items():
            f.write(str(action) + " : " + str(addr) + "\n")

"""
    Represents the gadgets extracted from a binary
"""
class Extracted:
    def __init__(self):
        self.data = {} # {Action, address} dictionary

    # Adds a gadget to the data
    def addGadget(self, action, address):
        if not (action in self.data):
            self.data[action] = [address]
        else:
            self.data[action].append(address)

    # Filters out addresses containing bytes in 'avoid' list
    def filter(self, avoid):
        new_data = {}
        for action, addrs in self.data.items():
            new_entry = []
            for addr in addrs:
                taddr = addr
                addr = hex(addr)[2:]
                if len(addr) % 2 != 0:
                    addr = '0' + addr
                addr = addr.decode('hex')
                valid = True
                for a in avoid:
                    if chr(a) in addr:
                        valid = False
                        break
                if valid:
                    new_entry.append(taddr)
            if len(new_entry) > 0:
                new_data[action] = new_entry
        self.data = new_data

    def __repr__(self):
        string = ""
        categories = {}
        for action, addrs in self.data.items():
            cl = action.__class__
            if not cl in categories:
                categories[cl] = []
            line = str(action) + " : ["
            for i, addr in enumerate(addrs):
                if i > 0:
                    line += ", "
                line += hex(addr)
            line += "]\n"
            categories[cl].append(line)
        for c, ss in categories.items():
            string += str(c) + " :\n"
            for s in ss:
                string += "\t" + s
        return string



# Extract data from binary
def retrieve_from_binary(filename) :
    context.binary = "./" + filename
    found_int = False
    window_size = 7
    found = []
    window = ['\x90'] * window_size
    i = -1

    # First save all sequences ending in 0xc3.
    with open(filename) as f:
        elf = ELF(filename)
        text_header = elf.get_section_by_name(".text").header
        text_vaddr = text_header.sh_addr
        text_size = text_header.sh_size
        text_off = text_header.sh_offset

        c = f.read(1)
        while c:

            i += 1

            window.append(c)
            del window[0]

            if i >= text_off and i <= text_off + text_size:
                if c == "\xc3":
                    s = ""
                    for c in window:
                        s += c
                    found.append((s, elf.offset_to_vaddr(i)))
            c = f.read(1)


    actions = []
    extracted = Extracted()

    # Then try to parse into an Action, and save it if it succeeds
    print("valid/tested/total")
    for i, (f, addr) in enumerate(found):
        if i % 50 == 0:
            print(str(len(actions)) + "/"+str(i)+"/"+str(len(found)))
            if len(actions) > 50 and False :
                break

        # For each subsequence of the 0xc3-ending sequence
        for length in range(3, len(f)):
            hx = f[-length:]

            # pwntool's disasm, returns an objdump-style string
            d = disasm(hx, byte = False, offset = False)
            lines = d.split("\n")
            if len(lines) < 2:
                continue
            if lines[-1] != "ret":
                continue
            line = lines[-2]

            try:
                # trying to parse this instruction
                parsed = Graph.parseLine(line)
                valid = True
                allowed_reg = ["eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"]
                for reg in parsed[1]:
                    if not str(reg) in allowed_reg:
                        valid = False
                        break
                for reg in parsed[2]:
                    if not str(reg) in allowed_reg:
                        valid = False
                        break
                if not valid:
                    continue

                # Computing the address of the gadget
                addr = addr - length + 1

                if not valid:
                    continue

                actions.append(parsed[0])
                extracted.addGadget(parsed[0], addr)
                break
            except ValueError:
                pass

    return extracted

