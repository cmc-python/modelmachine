# -*- coding: utf-8 -*-

"""Control unit parse instruction and give the commands to another part of computer."""

from modelmachine.alu import HALT, LESS, GREATER, EQUAL

RUNNING = 1
HALTED = 2

class AbstractControlUnit:

    """Abstract control unit allow to execute two methods: step and run."""

    def __init__(self, registers, ram, alu, operand_size):
        """See help(type(x))."""
        self.registers = registers
        self.ram = ram
        self.alu = alu
        self.operand_size = operand_size

    def step(self):
        """Execution of one instruction."""
        self.fetch_and_decode()
        self.load()
        self.execute()
        self.write_back()

    def get_status(self):
        """Show, can we or not execute another one instruction."""
        if self.registers.fetch('FLAGS', self.operand_size) & HALT != 0:
            return HALTED
        else:
            return RUNNING

    def run(self):
        """Execute instruction one-by-one until we met HALT command."""
        while self.get_status() == RUNNING:
            self.step()

    def fetch_and_decode(self):
        """Fetch instruction and decode them. At last, method should increment IP.

        Recommendation: set up address registers A1, A2, AS for loading
        into operation registers R1, R2, S.
        """
        raise NotImplementedError()

    def load(self):
        """Load data from memory to operation registers."""
        raise NotImplementedError()

    def execute(self):
        """Send message to ALU."""
        raise NotImplementedError()

    def write_back(self):
        """Save result of calculation to memory."""
        raise NotImplementedError()

class BordachenkovaControlUnit(AbstractControlUnit):

    """Abstract Bordachenkova control unit (need to inherit to determine machine)."""

    OPCODES = {
        "move": 0x00,

        "add": 0x01,
        "sub": 0x02,
        "smul": 0x03,
        "sdivmod": 0x04,

        "comp": 0x05,

        "umul": 0x13,
        "udivmod": 0x14,

        "jump": 0x80,
        "jeq": 0x81,
        "jneq": 0x82,

        "sjl": 0x83,
        "sjgeq": 0x84,
        "sjleq": 0x85,
        "sjg": 0x86,

        "ujl": 0x93,
        "ujgeq": 0x94,
        "ujleq": 0x95,
        "ujg": 0x96,

        "halt": 0x99
    }

    OPCODE_SIZE = 8
    ARITHMETIC_OPCODES = {OPCODES["add"], OPCODES["sub"],
                          OPCODES["smul"], OPCODES["sdivmod"],
                          OPCODES["umul"], OPCODES["udivmod"]}
    DIVMOD_OPCODES = {OPCODES["sdivmod"], OPCODES["udivmod"]}

    CONDJUMP_OPCODES = {OPCODES["jeq"], OPCODES["jneq"],
                        OPCODES["sjl"], OPCODES["sjgeq"],
                        OPCODES["sjleq"], OPCODES["sjg"],
                        OPCODES["ujl"], OPCODES["ujgeq"],
                        OPCODES["ujleq"], OPCODES["ujg"]}
    JUMP_OPCODES = CONDJUMP_OPCODES | {OPCODES["jump"]}

    BINAR_OPCODES = ARITHMETIC_OPCODES | {OPCODES["comp"]}
    UNAR_OPCODES = JUMP_OPCODES
    MONAR_OPCODES = {OPCODES["halt"]}

    opcode = 0

    def __init__(self, ir_size, address_size, *vargs, **kvargs):
        """Create necessary registers."""
        super().__init__(*vargs, **kvargs)
        self.ir_size = ir_size
        self.address_size = address_size

        # Instruction register
        self.registers.add_register('IP', self.address_size)
        self.registers.add_register('IR', self.ir_size)
        self.registers.put('IP', 0, self.address_size)


    def fetch_instruction(self, instruction_size):
        """Read instruction and fetch opcode."""
        instruction_pointer = self.registers.fetch('IP', self.address_size)
        instruction = self.ram.fetch(instruction_pointer, instruction_size)
        self.registers.put('IR', instruction, self.ir_size)
        self.opcode = instruction >> (instruction_size - self.OPCODE_SIZE)

        instruction_pointer += instruction_size // self.ram.word_size
        self.registers.put('IP', instruction_pointer, self.address_size)

        return instruction

    def execute(self):
        """Run arithmetic instructions."""
        if self.opcode == self.OPCODES["move"]:
            self.alu.move()
        elif self.opcode == self.OPCODES["halt"]:
            self.alu.halt()
        elif self.opcode == self.OPCODES["add"]:
            self.alu.add()
        elif self.opcode == self.OPCODES["sub"]:
            self.alu.sub()
        elif self.opcode == self.OPCODES["smul"]:
            self.alu.smul()
        elif self.opcode == self.OPCODES["umul"]:
            self.alu.umul()
        elif self.opcode == self.OPCODES["sdivmod"]:
            self.alu.sdivmod()
        elif self.opcode == self.OPCODES["udivmod"]:
            self.alu.udivmod()
        else:
            raise ValueError('Invalid opcode `{opcode}`'
                             .format(opcode=hex(self.opcode)))

    def execute_jump(self):
        """Conditional jump part of execution."""
        if self.opcode == self.OPCODES["jump"]:
            self.alu.jump()
        elif self.opcode == self.OPCODES["jeq"]:
            self.alu.cond_jump(True, EQUAL, True)
        elif self.opcode == self.OPCODES["jneq"]:
            self.alu.cond_jump(True, EQUAL, False)
        elif self.opcode == self.OPCODES["sjl"]:
            self.alu.cond_jump(True, LESS, False)
        elif self.opcode == self.OPCODES["sjgeq"]:
            self.alu.cond_jump(True, GREATER, True)
        elif self.opcode == self.OPCODES["sjleq"]:
            self.alu.cond_jump(True, LESS, True)
        elif self.opcode == self.OPCODES["sjg"]:
            self.alu.cond_jump(True, GREATER, False)
        elif self.opcode == self.OPCODES["ujl"]:
            self.alu.cond_jump(False, LESS, False)
        elif self.opcode == self.OPCODES["ujgeq"]:
            self.alu.cond_jump(False, GREATER, True)
        elif self.opcode == self.OPCODES["ujleq"]:
            self.alu.cond_jump(False, LESS, True)
        elif self.opcode == self.OPCODES["ujg"]:
            self.alu.cond_jump(False, GREATER, False)


    def fetch_and_decode(self):
        """Fetch instruction and addresses."""
        raise NotImplementedError()

    def load(self):
        """Load data to registers R1 and R2."""
        raise NotImplementedError()

    def write_back(self):
        """Write back calculation result."""
        raise NotImplementedError()


class BordachenkovaControlUnit3(BordachenkovaControlUnit):

    """Control unit for model-machine-3."""

    address1 = 0
    address2 = 0
    address3 = 0

    def __init__(self, instruction_size, *vargs, **kvargs):
        """See help(type(x))."""
        super().__init__(instruction_size, *vargs, **kvargs)
        self.instruction_size = instruction_size
        self.opcodes = (self.ARITHMETIC_OPCODES | self.JUMP_OPCODES |
                        {self.OPCODES["move"],
                         self.OPCODES["halt"]})

    def fetch_and_decode(self):
        """Fetch 3 addresses."""
        instruction = self.fetch_instruction(self.instruction_size)
        mask = 2 ** self.address_size - 1
        self.address1 = (instruction >> 2 * self.address_size) & mask
        self.address2 = (instruction >> self.address_size) & mask
        self.address3 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        if  (self.opcode in self.ARITHMETIC_OPCODES or
             self.opcode in self.CONDJUMP_OPCODES or
             self.opcode == self.OPCODES["move"]):

            operand1 = self.ram.fetch(self.address1, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)

            if self.opcode != self.OPCODES["move"]:
                operand2 = self.ram.fetch(self.address2, self.operand_size)
                self.registers.put('R2', operand2, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps."""
        if self.opcode in self.JUMP_OPCODES:
            if self.opcode != self.OPCODES["jump"]:
                self.alu.sub()
            self.registers.put('R1', self.address3, self.operand_size)

            self.execute_jump()
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if  (self.opcode in self.ARITHMETIC_OPCODES or
             self.opcode == self.OPCODES["move"]):

            value = self.registers.fetch('S', self.operand_size)
            self.ram.put(self.address3, value, self.operand_size)

            if self.opcode in self.DIVMOD_OPCODES:
                address = self.address3 + self.operand_size // self.ram.word_size
                address %= self.ram.memory_size
                value = self.registers.fetch('R1', self.operand_size)
                self.ram.put(address, value, self.operand_size)

class BordachenkovaControlUnit2(BordachenkovaControlUnit):

    """Control unit for model-machine-2."""

    address1 = 0
    address2 = 0

    def __init__(self, instruction_size, *vargs, **kvargs):
        """See help(type(x))."""
        super().__init__(instruction_size, *vargs, **kvargs)
        self.instruction_size = instruction_size

        self.instruction_size = instruction_size
        self.opcodes = (self.ARITHMETIC_OPCODES | self.JUMP_OPCODES |
                        {self.OPCODES["move"],
                         self.OPCODES["halt"],
                         self.OPCODES["comp"]})

    def fetch_and_decode(self):
        """Fetch 3 addresses."""
        instruction = self.fetch_instruction(self.instruction_size)
        mask = 2 ** self.address_size - 1
        self.address1 = (instruction >> self.address_size) & mask
        self.address2 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        if self.opcode in self.BINAR_OPCODES:
            operand1 = self.ram.fetch(self.address1, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
            operand2 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R2', operand2, self.operand_size)
        elif self.opcode == self.OPCODES["move"]:
            operand1 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
        elif self.opcode in self.JUMP_OPCODES:
            self.registers.put("R1", self.address2, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps and cmp."""
        if self.opcode == self.OPCODES["comp"]:
            self.alu.sub()
        elif self.opcode in self.JUMP_OPCODES:
            self.execute_jump()
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if self.opcode in self.ARITHMETIC_OPCODES | {self.OPCODES["move"]}:
            value = self.registers.fetch('S', self.operand_size)
            self.ram.put(self.address1, value, self.operand_size)
            if self.opcode in {0x04, 0x14}:
                address = self.address1 + self.operand_size // self.ram.word_size
                address %= self.ram.memory_size
                value = self.registers.fetch('R1', self.operand_size)
                self.ram.put(address, value, self.operand_size)

class BordachenkovaControlUnitV(BordachenkovaControlUnit):

    """Control unit for model-machine-variable."""

    address1 = 0
    address2 = 0

    def __init__(self, ir_size, *vargs, **kvargs):
        """See help(type(x))."""
        # dynamic instruction size
        super().__init__(ir_size, *vargs, **kvargs)

        self.opcodes = (self.ARITHMETIC_OPCODES | self.JUMP_OPCODES |
                        {self.OPCODES["move"],
                         self.OPCODES["halt"],
                         self.OPCODES["comp"]})

    def fetch_and_decode(self):
        """Fetch 3 addresses."""
        mask = 2 ** self.address_size - 1
        two_operands = self.BINAR_OPCODES | {self.OPCODES["move"]}

        instruction_pointer = self.registers.fetch('IP', self.address_size)
        self.opcode = self.ram.fetch(instruction_pointer, self.OPCODE_SIZE)

        if self.opcode in two_operands:
            instruction_size = self.OPCODE_SIZE + 2 * self.address_size
        elif self.opcode in self.UNAR_OPCODES:
            instruction_size = self.OPCODE_SIZE + self.address_size
        else:
            instruction_size = self.OPCODE_SIZE

        instruction = self.fetch_instruction(instruction_size)

        if self.opcode in two_operands:
            self.address1 = (instruction >> self.address_size) & mask
            self.address2 = instruction & mask
        elif self.opcode in self.UNAR_OPCODES:
            self.address1 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        if self.opcode in self.BINAR_OPCODES:
            operand1 = self.ram.fetch(self.address1, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
            operand2 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R2', operand2, self.operand_size)
        elif self.opcode == self.OPCODES["move"]:
            operand1 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
        elif self.opcode in self.JUMP_OPCODES:
            self.registers.put("R1", self.address1, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps and cmp."""
        if self.opcode == self.OPCODES["comp"]:
            self.alu.sub()
        elif self.opcode in self.JUMP_OPCODES:
            self.execute_jump()
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if self.opcode in self.ARITHMETIC_OPCODES | {self.OPCODES["move"]}:
            value = self.registers.fetch('S', self.operand_size)
            self.ram.put(self.address1, value, self.operand_size)
            if self.opcode in {0x04, 0x14}:
                address = self.address1 + self.operand_size // self.ram.word_size
                address %= self.ram.memory_size
                value = self.registers.fetch('R1', self.operand_size)
                self.ram.put(address, value, self.operand_size)

