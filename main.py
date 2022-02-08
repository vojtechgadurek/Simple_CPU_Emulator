import threading
import time


class Carry(int):
    def __init__(self):
        self.value = 0

    def __add__(self, other):
        value = self.value
        self.value = 0
        return int(value + other)

    def set(self):
        self.value = 1

    def eraze(self):
        self.value = 0


class Operations:
    def __init__(self, bit_length):
        self.pointer = 0
        self.carry = Carry()
        self.acumulators = [0] * 8
        self.memory = [0] * 2 ** 8
        self.bit_length = bit_length

    def make8bit(self, first, carry=False):
        if self.acumulators[first] >= 2 ** self.bit_length:
            self.acumulators[first] %= (2 ** self.bit_length)
            if carry:
                self.carry.set()

    def getcode(self):
        code = open("CODE.txt", "r").readlines()
        for i in len(code):
            self.memory[i] = code[i]

    def ldp(self, first, second):
        self.acumulators[first] = self.memory[self.acumulators[second]]

    def ldn(self, first, second):
        self.acumulators[first] = self.memory[self.pointer + 1]

    def str(self, first, second):
        self.memory[self.acumulators[second]] = self.acumulators[first]

    def add(self, first, second):
        self.acumulators[first] += self.acumulators[second] + self.carry
        self.make8bit(first, True)

    def adc(self, first, second):
        self.acumulators[first] += self.acumulators[second]
        self.carry.eraze()
        self.make8bit(first, True)

    def jmp(self, first, second):
        self.pointer = self.acumulators[first] - 1

    def jif(self, first, second):
        if self.acumulators[first] != 0:
            self.pointer = self.acumulators[second] - 1

    def an0(self, first, second):
        self.acumulators[first] &= self.acumulators[second]

    def orr(self, first, second):
        self.acumulators[first] |= self.acumulators[second]

    def shl(self, first, second):
        self.acumulators[first] = self.acumulators[first] << 1
        self.make8bit(first)

    def scr(self, first, second):
        self.acumulators[first] = self.acumulators[first] << 1
        if self.acumulators[first] % 4 == 1:
            self.acumulators[first] += 1
        self.make8bit(first)

    def shr(self, first, second):
        self.acumulators[first] = self.acumulators[first] >> 1

    def src(self, first, second):
        self.acumulator[first] = self.acumulator[first] >> 1
        if not (self.acumulator[first] % 2 ^ (self.bit_lenght - 1) == 0):
            self.acumulators[first] = + 2 ^ (self.bit_lenght - 1)

    def mov(self, first, second):
        self.acumulators[first] = self.memory[0]

    def miv(self, first, second):
        self.memory[0] = self.acumulators[first]

    def end(self, first, second):
        self.pointer = -100
        print("<---------Program-------------has---------------ended-------->")

    def n0t(self, first, second):
        self.acumulators[first] = (2 ** self.bit_length - self.acumulators[first] - 1) % (2 ** self.bit_length)

    def xor(self, first, second):
        self.acumulators[first]  ^= self.acumulators[second]

class Translator(Operations):
    def __init__(self, bit_length):
        super().__init__(bit_length)
        self.unary = ["LDN", "N0T", "SHL", "SHR", "SCL", "SCR", "JMP", "MOV", "MIV"]
        self.binary = ["ADD", "ADC", "AN0", "XOR", "JIF", "STR", "LDP", "ORR"]
        self.next = ["LDN"]
        self.operations = {}
        self.bin_to_operations = {}
        self.n_binary = 0  # čísla jsou ve formátu 0b 0... yyxx
        self.n_unary = 2 ** (bit_length - 1)  # čísla jsou ve formátu  0b 1... .xxx
        self.acumulators_to_id = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7}
        self.acumulators_to_name = ["A", "B", "C", "D", "E", "F", "G", "H"]
        self.createoperations()
        self.operations["END"] = {
            "name": "END", "id": 2 ** self.bit_length - 1, "func": self.end, "binary": False
        }
        self.bin_to_operations[2 ** self.bit_length - 1] = self.operations["END"]

    def createoperations(self):
        # Vytvoří překlad pro binární operace
        def func_not_exist():
            raise Exception("Operation is not defined")

        for operation in self.binary:
            self.operations[operation] = {
                "name": operation, "id": self.n_binary, "func": getattr(self, operation.lower(), func_not_exist),
                "binary": True
            }
            self.bin_to_operations[self.n_binary] = self.operations[operation]
            if self.n_binary >= 2 ** (self.bit_length - 1):  # Kontroluje jestli index operace nepřetekl do unárních
                raise Exception("Overflow, max number of binary operations is 8")
            assert self.n_binary % 16 == 0, "Binary id has number in 0b 0000 xxyy"
            self.n_binary += 2 ** 4

        # Vytvoří překlad pro unární operace
        for operation in self.unary:
            self.operations[operation] = {
                "name": operation, "id": self.n_unary, "func": getattr(self, operation.lower(), func_not_exist),
                "binary": False
            }
            self.bin_to_operations[self.n_unary] = self.operations[operation]
            self.n_unary += 8
            if len(self.unary) >= 2 ** self.bit_length:
                raise Exception("Overflow, max number of unary operations is 16")
            assert self.n_unary % 8 == 0, "Binary id has number in 0b 0000 0xxx"


class Device(Translator):
    def __init__(self, bit_length, code_directory=""):
        super(Device, self).__init__(bit_length)
        self.code_directory = code_directory
        self.memory = [0] * 2 ** bit_length
        self.loadmemory()
        self.loadcode()
        self.pointer = 1
        self.run = False
        self.log = []
        self.takt = 1
        self.showcommands = False
        self.acumulators_print = False

    def loadmemory(self):
        x = open(self.code_directory + "MEMORY.txt", "r")
        memory = x.readlines()
        x.close()
        for line in memory:
            line = line.split()
            self.memory[int(line[0])] = int(line[1])

    def loadcode(self):
        x = open(self.code_directory + "CODE.txt", "r")
        code = x.readlines()
        x.close()
        pointer = 1
        for line in code:
            if not line.startswith('%'):
                line = line.split()
                command = self.operations[line[0]]["id"]
                in_next = line[0] in self.next
                if len(line) == 2 or (in_next and len(line) == 3):
                    command += int(self.acumulators_to_id[line[1]])
                elif len(line) == 3:
                    command += int(self.acumulators_to_id[line[1]]) * 2 ** 2 + int(
                        self.acumulators_to_id[line[2]])  # příkaz + first + second = 0B 1... yyxx
                self.memory[pointer] = command
                pointer += 1
                if line[0] in self.next:
                    self.memory[pointer] = int(line[2])
                    pointer += 1

    def runcode(self):
        # Doba jednoho tiku
        while self.pointer >= 0 and self.pointer < 2 ** 8 and self.run:  # Hard nakodeny rozsah
            start = time.time()
            self.next_step()
            end = time.time()
            if (end - start) < self.takt:
                time.sleep(self.takt - end + start)
            else:
                time.sleep(0.001)

    def next_step(self):
        id_operation = self.memory[self.pointer]
        if id_operation == 255:
            first = 0
            second = 0
        elif id_operation >= 128:  # Je unary
            first = id_operation % 8
            id_operation -= first
            second = None
        else:  # Je binary
            first = id_operation % 2 ** 4 >> 2
            second = id_operation % 2 ** 2
            id_operation -= first << 2
            id_operation -= second
        operation = self.bin_to_operations[id_operation]
        operation["func"](first, second)
        if self.showcommands:
            try:
                print(operation["name"], self.acumulators_to_name[first], self.acumulators_to_name[second], "/", self.acumulators[first], self.acumulators[second], "/",
                      self.pointer, sep=" ")
            except:
                print(operation["name"], self.acumulators_to_name[first], second, "/", self.acumulators[first], "/", self.pointer, sep=" ")
        if self.acumulators_print:
            print(self.acumulators)
        if operation["name"] in self.next:
            self.pointer += 1
        self.pointer += 1
        self.log.append(operation)


def runner(location):
    device = Device(8, location)
    device.run = False
    threading1 = threading.Thread(target=device.runcode)
    threading1.daemon = True
    threading1.start()

    on_run = True
    print(
        "Hi, program is running. To start type: run, to step type: step, for more help type: help. Author: Vojtech Gadurek")
    while on_run:
        control_command = input().lower()
        if control_command == "stop":
            device.run = False
            print("Program stopped")
        elif control_command == "end":
            on_run = False
            device.run = False
            print("You have ended the program")
        elif control_command.startswith("rychlost"):
            device.takt = float(control_command.split()[1])
        elif control_command == "run":
            device.run = True
            threading1 = threading.Thread(target=device.runcode)
            threading1.start()
        elif control_command.startswith("step"):
            device.next_step()
        elif control_command.startswith("memory"):
            control_command = control_command.split()
            if len(control_command) > 1:
                data = device.memory[int(control_command[1]): int(control_command[2]):1]
                start = int(control_command[1])
            else:
                data = device.memory
                start = 0
            print("pointer ", device.pointer)
            for i in range(len(data) // 16 + 1):
                data_bit = str(i * 16 + start)
                add_space = " " * (3 - len(data_bit))
                print(add_space, data_bit, end=" ")
                for k in range(16):
                    try:
                        data_bit = str(data[i * 16 + k])
                        add_space = " " * (3 - len(data_bit))
                        print(add_space, data_bit, end=" ")
                    except:
                        print("   ", end=" ")
                print()
        elif control_command.startswith("showprikazy"):
            device.showcommands = not device.showcommands
        elif control_command.startswith("akumulatory"):
            print(device.acumulators)
        elif control_command.startswith("log"):
            print(device.log)
        elif control_command.startswith("ak_zmena"):
            device.acumulators_print = not device.acumulators_print
        elif control_command.startswith("debug"):
            device.acumulators_print = not device.acumulators_print
            device.showcommands = not device.showcommands
        elif control_command.startswith("help"):
            print(" run => to start program \n",
                  "stop => to stop program \n",
                  "rychlost  N => to change speed to N\n",
                  "debug => for quick debug \n",
                  "akumulatory => shows content in acumulators\n",
                  "step => Do one command => step\n",
                  "log => shows command log \n",
                  "ak_zmena => after every step shows content of acumulators\n",
                  "memory => show content of memory\n",
                  "showprikazy => after every step shows command used\n",
                  "end => ends program\n"
                  )
        else:
            device.run = False
            print("command does not exists, program stopped")


"""device = Device(8,"trial_prg/prg3/" )
while True:
    device.next_step()"""
runner("trial_prg/prg3/")
