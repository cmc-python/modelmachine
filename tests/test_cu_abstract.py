"""Test case for abstract control units."""

from unittest.mock import NonCallableMagicMock, call, create_autospec

import pytest

from modelmachine.alu import (
    AluRegisters,
    ArithmeticLogicUnit,
    Flags,
)
from modelmachine.cell import Cell
from modelmachine.cu import (
    OPCODE_BITS,
    ControlUnit,
    Opcode,
    OpcodeBitset,
    Status,
    WrongOpcodeError,
)
from modelmachine.ram import RandomAccessMemory
from modelmachine.register import RegisterMemory, RegisterName

AB = 16


def test_opcode_bitset() -> None:
    for op in Opcode:
        bs = OpcodeBitset([op])
        assert len(bs) == 1

        for op2 in bs:
            assert op2 is op

        for op2 in Opcode:
            if op2 is op:
                assert op2 in bs

                bs2 = bs | {op2}
                assert isinstance(bs2, OpcodeBitset)
                assert bs2 == {op}
            else:
                assert op2 not in bs

                bs2 = bs | {op2}
                assert isinstance(bs2, OpcodeBitset)
                assert bs2 == {op, op2}


def test_opcode_bitset_sub() -> None:
    bs1 = OpcodeBitset((Opcode.add, Opcode.sub))
    assert repr(bs1) == "OpcodeBitset((<Opcode.add: 1>, <Opcode.sub: 2>))"
    assert str(bs1) == "OpcodeBitset((<Opcode.add: 1>, <Opcode.sub: 2>))"
    bs2 = {Opcode.add, Opcode.udivmod}
    assert bs1 - bs2 == {Opcode.sub}


class TestControlUnit:
    """Test case for abstract control unit."""

    ram: RandomAccessMemory
    registers: NonCallableMagicMock
    alu: NonCallableMagicMock
    control_unit: ControlUnit

    IR_BITS = 3 * AB + OPCODE_BITS
    WB = IR_BITS
    OPERAND_BITS = IR_BITS

    def setup_method(self) -> None:
        """Init state."""
        self.ram = RandomAccessMemory(word_bits=self.WB, address_bits=AB)
        self.registers = create_autospec(RegisterMemory(), True, True)
        self.alu = create_autospec(
            ArithmeticLogicUnit(
                registers=self.registers,
                register_map=AluRegisters(
                    S=RegisterName.S,
                    RES=RegisterName.R1,
                    R1=RegisterName.R1,
                    R2=RegisterName.R2,
                ),
                address_bits=AB,
                operand_bits=self.OPERAND_BITS,
            ),
            True,
            True,
        )
        self.alu.operand_bits = self.OPERAND_BITS
        self.control_unit = ControlUnit(
            name="cu_abstract",
            registers=self.registers,
            ram=self.ram,
            alu=self.alu,
            known_opcodes=OpcodeBitset(
                (
                    Opcode.move,
                    Opcode.halt,
                    Opcode.add,
                    Opcode.sub,
                    Opcode.umul,
                    Opcode.smul,
                    Opcode.sdivmod,
                    Opcode.udivmod,
                )
            ),
            ir_bits=self.IR_BITS,
        )

    def test_status_running(self) -> None:
        self.registers.__getitem__.return_value = Cell(0, bits=7 * 8)
        assert self.control_unit.status is Status.RUNNING

    def test_status_halted(self) -> None:
        self.registers.__getitem__.return_value = Cell(Flags.HALT.value, bits=7 * 8)
        assert self.control_unit.status is Status.HALTED

    def test_step_and_run(self) -> None:
        """Test command execution."""

        def do_nothing() -> None:
            """Empty function."""

        self.control_unit._fetch_and_decode = create_autospec(do_nothing)  # type: ignore
        self.control_unit._load = create_autospec(do_nothing)  # type: ignore
        self.control_unit._write_back = create_autospec(do_nothing)  # type: ignore
        self.registers.__getitem__.return_value = Cell(Flags.CLEAR.value, bits=7 * 8)

        self.control_unit.step()
        self.control_unit._fetch_and_decode.assert_called_once_with()  # type: ignore
        self.control_unit._load.assert_called_once_with()  # type: ignore
        self.control_unit._write_back.assert_called_once_with()  # type: ignore

        self.registers.__getitem__.return_value = Cell(Flags.HALT.value, bits=7 * 8)

        self.control_unit.run()
        self.control_unit._fetch_and_decode.assert_called_once_with()  # type: ignore
        self.control_unit._load.assert_called_once_with()  # type: ignore
        self.control_unit._write_back.assert_called_once_with()  # type: ignore

    def run_fetch(
        self,
        *,
        instruction: Cell,
        opcode: Opcode,
        and_decode: bool = True,
    ) -> None:
        """Run one fetch test."""
        address = Cell(10, bits=AB)
        self.ram.put(address=address, value=instruction)
        increment = Cell(instruction.bits // self.ram.word_bits, bits=AB)

        def get_register(name: RegisterName) -> Cell:
            """Get PC."""
            if name is RegisterName.PC:
                return address

            raise NotImplementedError

        self.registers.__getitem__.side_effect = get_register

        if and_decode:
            self.control_unit._fetch_and_decode()
        else:
            self.control_unit._fetch_instruction(instruction.bits)

        self.registers.__getitem__.assert_any_call(RegisterName.PC)
        self.registers.__setitem__.assert_has_calls(
            [
                call(RegisterName.RI, instruction),
                call(RegisterName.PC, address + increment),
            ]
        )
        assert self.control_unit._opcode == opcode

    def test_fetch_instruction(self) -> None:
        for opcode in self.control_unit._known_opcodes:
            self.run_fetch(
                instruction=Cell(
                    opcode.value << (self.IR_BITS - OPCODE_BITS),
                    bits=self.IR_BITS,
                ),
                opcode=opcode,
                and_decode=False,
            )

    def test_fetch_unknown_instruction(self) -> None:
        for opcode in set(Opcode) - self.control_unit._known_opcodes:
            with pytest.raises(WrongOpcodeError):
                self.run_fetch(
                    instruction=Cell(
                        opcode.value << (self.IR_BITS - OPCODE_BITS),
                        bits=self.IR_BITS,
                    ),
                    opcode=opcode,
                    and_decode=False,
                )

    def test_fail_decode(self) -> None:
        for opcode in set(Opcode) - self.control_unit._known_opcodes:
            self.control_unit._opcode = opcode
            with pytest.raises(WrongOpcodeError):
                self.control_unit._execute()

    def test_move_execute(self, *, should_move: bool = True) -> None:
        """Test basic operations."""
        if should_move is not None:
            self.control_unit._opcode = Opcode.move
            self.control_unit._execute()
            if should_move:
                self.alu.move.assert_called_once_with()
            else:
                assert not self.alu.move.called

    @pytest.mark.parametrize(
        ("opcode", "alu_method"),
        [
            (Opcode.move, "move"),
            (Opcode.add, "add"),
            (Opcode.sub, "sub"),
            (Opcode.smul, "smul"),
            (Opcode.umul, "umul"),
            (Opcode.sdivmod, "sdivmod"),
            (Opcode.udivmod, "udivmod"),
            (Opcode.halt, "halt"),
        ],
    )
    def test_alu_execute(self, opcode: Opcode, alu_method: str) -> None:
        self.control_unit._opcode = opcode
        self.control_unit._execute()
        self.alu.__getattribute__(alu_method).assert_called_once_with()
