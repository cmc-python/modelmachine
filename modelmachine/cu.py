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

    OPCODE_SIZE = 8

    MOVE = 0x00
    ADD, SUB = 0x01, 0x02
    SMUL, SDIVMOD = 0x03, 0x04
    UMUL, UDIVMOD = 0x13, 0x14
    COMP = 0x05
    JUMP = 0x80
    JEQ, JNEQ = 0x81, 0x82
    SJL, SJGEQ, SJLEQ, SJG = 0x83, 0x84, 0x85, 0x86
    UJL, UJGEQ, UJLEQ, UJG = 0x93, 0x94, 0x95, 0x96
    HALT = 0x99

    ARITHMETIC_OPCODES = {ADD, SUB, SMUL, SDIVMOD, UMUL, UDIVMOD}
    CONDJUMP_OPCODES = {JEQ, JNEQ, SJL, SJGEQ, SJLEQ, SJG,
                        UJL, UJGEQ, UJLEQ, UJG}

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
        if self.opcode == self.MOVE:
            self.alu.move()
        elif self.opcode == self.HALT:
            self.alu.halt()
        elif self.opcode == self.ADD:
            self.alu.add()
        elif self.opcode == self.SUB:
            self.alu.sub()
        elif self.opcode == self.SMUL:
            self.alu.smul()
        elif self.opcode == self.UMUL:
            self.alu.umul()
        elif self.opcode == self.SDIVMOD:
            self.alu.sdivmod()
        elif self.opcode == self.UDIVMOD:
            self.alu.udivmod()
        else:
            raise ValueError('Invalid opcode `{opcode}`'
                             .format(opcode=hex(self.opcode)))

    def execute_cond_jump(self):
        """Conditional jump part of execution."""
        if self.opcode == self.JEQ:
            self.alu.cond_jump(True, EQUAL, True)
        elif self.opcode == self.JNEQ:
            self.alu.cond_jump(True, EQUAL, False)
        elif self.opcode == self.SJL:
            self.alu.cond_jump(True, LESS, False)
        elif self.opcode == self.SJGEQ:
            self.alu.cond_jump(True, GREATER, True)
        elif self.opcode == self.SJLEQ:
            self.alu.cond_jump(True, LESS, True)
        elif self.opcode == self.SJG:
            self.alu.cond_jump(True, GREATER, False)
        elif self.opcode == self.UJL:
            self.alu.cond_jump(False, LESS, False)
        elif self.opcode == self.UJGEQ:
            self.alu.cond_jump(False, GREATER, True)
        elif self.opcode == self.UJLEQ:
            self.alu.cond_jump(False, LESS, True)
        elif self.opcode == self.UJG:
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
        self.opcodes = (self.ARITHMETIC_OPCODES | self.CONDJUMP_OPCODES |
                        {self.JUMP, self.MOVE, self.HALT})

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
             self.opcode == self.MOVE):

            operand1 = self.ram.fetch(self.address1, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)

            if self.opcode != self.MOVE:
                operand2 = self.ram.fetch(self.address2, self.operand_size)
                self.registers.put('R2', operand2, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps."""
        if  (self.opcode in self.CONDJUMP_OPCODES or
             self.opcode == self.JUMP):

            if self.opcode != self.JUMP:
                self.alu.sub()
            self.registers.put('R1', self.address3, self.operand_size)

            if self.opcode == self.JUMP:
                self.alu.jump()
            else: # self.opcode in self.CONDJUMP_OPCODES
                self.execute_cond_jump()
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if  (self.opcode in self.ARITHMETIC_OPCODES or
             self.opcode == self.MOVE):

            value = self.registers.fetch('S', self.operand_size)
            self.ram.put(self.address3, value, self.operand_size)

            if self.opcode in {self.SDIVMOD, self.UDIVMOD}:
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
        self.opcodes = (self.ARITHMETIC_OPCODES | self.CONDJUMP_OPCODES |
                        {self.JUMP, self.MOVE, self.HALT, self.COMP})

    def fetch_and_decode(self):
        """Fetch 3 addresses."""
        instruction = self.fetch_instruction(self.instruction_size)
        mask = 2 ** self.address_size - 1
        self.address1 = (instruction >> self.address_size) & mask
        self.address2 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        if self.opcode in self.ARITHMETIC_OPCODES | {self.COMP}:
            operand1 = self.ram.fetch(self.address1, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
            operand2 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R2', operand2, self.operand_size)
        elif self.opcode == self.MOVE:
            operand1 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
        elif self.opcode in self.CONDJUMP_OPCODES | {self.JUMP}:
            self.registers.put("R1", self.address2, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps and cmp."""
        if self.opcode == self.COMP:
            self.alu.sub()
        elif self.opcode == self.JUMP:
            self.alu.jump()
        elif self.opcode in self.CONDJUMP_OPCODES:
            self.execute_cond_jump()
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if self.opcode in self.ARITHMETIC_OPCODES | {self.MOVE}:
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

    def __init__(self, *vargs, **kvargs):
        """See help(type(x))."""
        # dynamic instruction size
        super().__init__(instruction_size=42, *vargs, **kvargs)

        self.opcodes = (self.ARITHMETIC_OPCODES | self.CONDJUMP_OPCODES |
                        {self.JUMP, self.MOVE, self.HALT, self.COMP})

    def fetch_and_decode(self):
        """Fetch 3 addresses."""
        instruction_pointer = self.registers.fetch('IP', self.address_size)
        self.opcode = self.ram.fetch(instruction_pointer, self.OPCODE_SIZE)

        if self.opcode in self.ARITHMETIC_OPCODES | {self.MOVE}:
            self.instruction_size = self.OPCODE_SIZE + 2 * self.address_size

            super().fetch_and_decode()

            instruction = self.registers.fetch('IR', self.instruction_size)
            mask = 2 ** self.address_size - 1
            self.address1 = (instruction >> self.address_size) & mask
            self.address2 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        if self.opcode in self.ARITHMETIC_OPCODES | {self.COMP}:
            operand1 = self.ram.fetch(self.address1, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
            operand2 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R2', operand2, self.operand_size)
        elif self.opcode == self.MOVE:
            operand1 = self.ram.fetch(self.address2, self.operand_size)
            self.registers.put('R1', operand1, self.operand_size)
        elif self.opcode in self.CONDJUMP_OPCODES | {self.JUMP}:
            self.registers.put("R1", self.address2, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps and cmp."""
        if self.opcode == self.COMP:
            self.alu.sub()
        elif self.opcode == self.JUMP:
            self.alu.jump()
        elif self.opcode in self.CONDJUMP_OPCODES:
            self.execute_cond_jump()
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if self.opcode in self.ARITHMETIC_OPCODES | {self.MOVE}:
            value = self.registers.fetch('S', self.operand_size)
            self.ram.put(self.address1, value, self.operand_size)
            if self.opcode in {0x04, 0x14}:
                address = self.address1 + self.operand_size // self.ram.word_size
                address %= self.ram.memory_size
                value = self.registers.fetch('R1', self.operand_size)
                self.ram.put(address, value, self.operand_size)


