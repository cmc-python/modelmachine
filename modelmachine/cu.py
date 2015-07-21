# -*- coding: utf-8 -*-

"""Control unit parse instruction and give the commands to another part of computer."""

from modelmachine.alu import HALT, LESS, GREATER, EQUAL

RUNNING = 1
HALTED = 2

class AbstractControlUnit:

    """Abstract control unit allow to execute two methods: step and run."""

    def __init__(self, registers, memory, alu, operand_size, address_size):
        """See help(type(x))."""
        self.registers = registers
        self.memory = memory
        self.alu = alu
        self.operand_size = operand_size
        self.address_size = address_size

    def step(self):
        """Execution of one instruction."""
        self.fetch_and_decode()
        self.increment_ip()
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
        """Fetch instruction and decode them.

        Recommendation: set up address registers A1, A2, AS for loading
        into operation registers R1, R2, S.
        """
        raise NotImplementedError()

    def increment_ip(self):
        """Incrementing instruction pointer."""
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
    ARITHMETIC_OPCODES = {0x00, 0x01, 0x02, 0x03, 0x13, 0x04, 0x14}

    opcode = 0

    def __init__(self, instruction_size, *vargs, **kvargs):
        """Create necessary registers."""
        super().__init__(*vargs, **kvargs)
        self.instruction_size = instruction_size

        # Instruction register
        self.registers.add_register('IR', self.instruction_size)


    def fetch_and_decode(self):
        """Read instruction and fetch opcode."""
        instruction_pointer = self.registers.fetch('IP', self.address_size)
        instruction = self.memory.fetch(instruction_pointer, self.instruction_size)
        self.registers.put('IR', instruction, self.instruction_size)
        self.opcode = instruction >> (self.instruction_size - self.OPCODE_SIZE)

    def increment_ip(self):
        """Increment = self.address_size."""
        instruction_pointer = self.registers.fetch('IP', self.address_size)
        instruction_pointer += self.instruction_size // self.memory.word_size
        self.registers.put('IP', instruction_pointer, self.address_size)

    def execute(self):
        """Run arithmetic instructions."""
        if self.opcode == 0x00:
            self.alu.move()
        elif self.opcode == 0x99:
            self.alu.halt()
        elif self.opcode == 0x01:
            self.alu.add()
        elif self.opcode == 0x02:
            self.alu.sub()
        elif self.opcode == 0x03:
            self.alu.smul()
        elif self.opcode == 0x13:
            self.alu.umul()
        elif self.opcode == 0x04:
            self.alu.smod()
            mod = self.registers.fetch('S', self.operand_size)
            self.alu.sdiv()
            self.registers.put('R1', mod, self.operand_size)
        elif self.opcode == 0x14:
            self.alu.umod()
            mod = self.registers.fetch('S', self.operand_size)
            self.alu.udiv()
            self.registers.put('R1', mod, self.operand_size)
        else:
            raise ValueError('Invalid opcode `{opcode}`'
                             .format(opcode=self.opcode))


class BordachenkovaControlUnit3(BordachenkovaControlUnit):

    """Control unit for model-machine-3."""

    address1 = 0
    address2 = 0
    address3 = 0

    def fetch_and_decode(self):
        """Fetch 3 addresses."""
        super().fetch_and_decode()
        instruction = self.registers.fetch('IR', self.instruction_size)
        mask = 2 ** self.address_size - 1
        self.address1 = (instruction >> 2 * self.address_size) & mask
        self.address2 = (instruction >> self.address_size) & mask
        self.address3 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        operand1 = self.memory.fetch(self.address1, self.operand_size)
        self.registers.put('R1', operand1, self.operand_size)
        operand2 = self.memory.fetch(self.address2, self.operand_size)
        self.registers.put('R2', operand2, self.operand_size)

    def execute(self):
        """Add specific commands: conditional jumps."""
        if self.opcode in {0x81, 0x82, 0x83, 0x84, 0x85, 0x86,
                           0x93, 0x94, 0x95, 0x96}:
            self.alu.sub()
            self.registers.put('R1', self.address3, self.operand_size)
            if self.opcode == 0x81:
                self.alu.cond_jump(True, EQUAL, True)
            elif self.opcode == 0x82:
                self.alu.cond_jump(True, EQUAL, False)
            elif self.opcode == 0x83:
                self.alu.cond_jump(True, LESS, False)
            elif self.opcode == 0x84:
                self.alu.cond_jump(True, GREATER, True)
            elif self.opcode == 0x85:
                self.alu.cond_jump(True, LESS, True)
            elif self.opcode == 0x86:
                self.alu.cond_jump(True, GREATER, False)
            elif self.opcode == 0x93:
                self.alu.cond_jump(False, LESS, False)
            elif self.opcode == 0x94:
                self.alu.cond_jump(False, GREATER, True)
            elif self.opcode == 0x95:
                self.alu.cond_jump(False, LESS, True)
            elif self.opcode == 0x96:
                self.alu.cond_jump(False, GREATER, False)
        else:
            super().execute()

    def write_back(self):
        """Write result back."""
        if self.opcode in self.ARITHMETIC_OPCODES:
            value = self.registers.fetch('S', self.operand_size)
            self.memory.put(self.address3, value, self.operand_size)
            if self.opcode in {0x13, 0x14}:
                address = self.address3 + self.operand_size // self.memory.word_size
                value = self.registers.fetch('R1', self.operand_size)
                self.memory.put(address, value, self.operand_size)

class BordachenkovaControlUnit2(BordachenkovaControlUnit):

    """Control unit for model-machine-2."""

    address1 = 0
    address2 = 0

    def fetch_and_decode(self):
        """Fetch 2 addresses."""
        super().fetch_and_decode()
        instruction = self.registers.fetch('IR', self.instruction_size)
        mask = 2 ** self.address_size - 1
        self.address1 = (instruction >> self.address_size) & mask
        self.address2 = instruction & mask

    def load(self):
        """Load registers R1 and R2."""
        operand1 = self.memory.fetch(self.address1, self.operand_size)
        self.registers.put('R1', operand1, self.operand_size)
        operand2 = self.memory.fetch(self.address2, self.operand_size)
        self.registers.put('R2', operand2, self.operand_size)

    def execute(self):
        """Add specific commands: comparasion."""
