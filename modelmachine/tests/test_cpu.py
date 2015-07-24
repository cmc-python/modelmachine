# -*- coding: utf-8 -*-

"""Test case for complex CPU."""

from modelmachine.cpu import AbstractCPU
from modelmachine.cpu import BordachenkovaMM3, BordachenkovaMM2

from modelmachine.memory import RandomAccessMemory, RegisterMemory

from modelmachine.cu import AbstractControlUnit
from modelmachine.alu import ArithmeticLogicUnit
from modelmachine.io import InputOutputUnit

from unittest.mock import create_autospec
from pytest import raises

class TestAbstractCPU:

    """Test case for Abstract CPU."""

    cpu = None
    source = None

    def setup(self):
        """Init state and mock."""
        self.cpu = AbstractCPU()
        self.cpu.memory = create_autospec(RandomAccessMemory, True, True)
        self.cpu.registers = create_autospec(RegisterMemory, True, True)
        self.cpu.alu = create_autospec(ArithmeticLogicUnit, True, True)
        self.cpu.control_unit = create_autospec(AbstractControlUnit, True, True)
        self.cpu.io_unit = create_autospec(InputOutputUnit, True, True)
        self.cpu.io_unit.get_int.return_value = 789
        self.source = ["[config]",                          # 0
                       "arch = mm1",                        # 1
                       "input  =0o100, 0x101, 102   \n",    # 2
                       "output=   102\n\n",                 # 3
                       "key=value",                         # 4
                       "[code]",                            # 5
                       "00 00; comment",                    # 6
                       "99 00",                             # 7
                       "[input]",                           # 8
                       "0o123 0x456",                       # 9
                       "789"]                               # 10

    def test_load_program(self):
        """Test load all program."""
        self.cpu.load_program(self.source)
        assert self.cpu.config == {"arch": "mm1",
                                   "input": "0o100, 0x101, 102",
                                   "output": "102",
                                   "key": "value"}
        self.cpu.io_unit.load_source.assert_called_once_with(self.source[6:8])
        self.cpu.io_unit.load_data.assert_called_once_with([0o100, 0x101, 102],
                                                           self.source[9:])

        with raises(ValueError):
            source = list(self.source)
            source[0] = "wrong_format"
            self.cpu.load_program(source)

        with raises(ValueError):
            source = list(self.source)
            source[0] = "[input]"
            source[8] = "[config]"
            self.cpu.load_program(source)

        with raises(ValueError):
            source = list(self.source)
            source[1] = "wrong_format"
            self.cpu.load_program(source)

    def test_print_result(self, tmpdir):
        """CPU should print to file."""
        self.cpu.load_program(self.source)
        out = tmpdir.join("output.txt")
        with open(str(out), 'w') as output:
            self.cpu.print_result(output=output)
        self.cpu.io_unit.get_int.assert_called_once_with(102)
        assert out.read() == "789\n"

    def test_run_file(self, tmpdir):
        """Send run message to control unit."""
        source = tmpdir.join("source.mmach")
        source.write("\n".join(self.source))
        out = tmpdir.join("output.txt")
        with open(str(out), 'w') as output:
            self.cpu.run_file(str(source), output=output)

        assert self.cpu.config == {"arch": "mm1",
                                   "input": "0o100, 0x101, 102",
                                   "output": "102",
                                   "key": "value"}
        self.cpu.io_unit.load_source.assert_called_once_with(self.source[6:8])
        self.cpu.io_unit.load_data.assert_called_once_with([0o100, 0x101, 102],
                                                           self.source[9:])
        self.cpu.control_unit.run.assert_called_with()
        self.cpu.io_unit.get_int.assert_called_once_with(102)
        assert out.read() == "789\n"


class TestBordachenkovaMM3:

    """Smoke test for mm-3."""

    cpu = None
    source = None

    def setup(self):
        """Init state."""
        self.cpu = BordachenkovaMM3()
        self.source = ("[config]\ninput=0x101,0x102\noutput=0x103\n" +
                       "[code]\n01 0101 0102 0103\n80 0000 0000 0003\n" +
                       "02 0103 0103 0103; never be used\n" +
                       "02 0103 0005 0103\n99 0000 0000 0000\n" +
                       "00000000000002\n" +
                       "[input]\n100 200\n")

    def test_smoke(self, tmpdir):
        """Smoke test."""
        source = tmpdir.join("source.mmach")
        source.write(self.source)
        out = tmpdir.join("output.txt")
        with open(str(out), 'w') as output:
            self.cpu.run_file(str(source), output=output)

        assert out.read() == "298\n"


class TestBordachenkovaMM2:

    """Smoke test for mm-2."""

    cpu = None
    source = None

    def setup(self):
        """Init state."""
        self.cpu = BordachenkovaMM2()
        self.source = ("[config]\n" +
                       "input=0x101,0x102\n" +
                       "output=0x103\n" +
                       "[code]\n" +
                       "01 0101 0102\n" +
                       "00 0103 0101\n" +
                       "05 0101 0102\n" +
                       "86 0000 0005\n" +
                       "02 0103 0103; never be used\n" +
                       "02 0103 0007\n" +
                       "99 0000 0000\n" +
                       "0000000002\n" +
                       "[input]\n" +
                       "100 200\n")

    def test_smoke(self, tmpdir):
        """Smoke test."""
        source = tmpdir.join("source.mmach")
        source.write(self.source)
        out = tmpdir.join("output.txt")
        with open(str(out), 'w') as output:
            self.cpu.run_file(str(source), output=output)

        assert out.read() == "298\n"