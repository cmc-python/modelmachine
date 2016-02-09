# -*- coding: utf-8 -*-

"""Test case for assembler."""

from modelmachine import asm

RESULT_CODE = """mmm

[config]
output = 32

[code]
0020 002e 00f0 0030 0050 002c 2266 0156 0022 2162 256f 8200 0007 1050 0020 9900 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0001 0000 0002 0000 0003 0000 0004 0000 0005 0000 0000 0000 0002 0000 000a

[input]

"""

def eq_token(token, tok_type, value):
    """Test tokens equals."""
    return token.type == tok_type and token.value == value

class TestASM:

    """Tast case for modelmachine.asm."""

    code = None
    tokens = None

    def setup(self):
        """Sample program."""
        self.code = '''
        .config 0x20
        sum: .word 0
        array: .word 1,2,3,4,5 ; Input array
        zero: .word 0
        size_word: .word 2
        size_array: .word 10
        .dump sum
        .code
        load R2, size_word
        load RF, size_array
        load R5, zero
        rsub R6, R6
        rpt: add R5, array(R6)
        radd R6, R2
        rcomp R6, RF
        jneq rpt
        store R5, sum
        halt
        '''

        self.tokens = [
            ('\n', '\n'),
            ('CONFIG', '.config'),
            ('NUMBER', 32),
            ('\n', '\n'),
            ('LABEL', 'sum'),
            (':', ':'),
            ('WORD', '.word'),
            ('NUMBER', 0),
            ('\n', '\n'),
            ('LABEL', 'array'),
            (':', ':'),
            ('WORD', '.word'),
            ('NUMBER', 1),
            (',', ','),
            ('NUMBER', 2),
            (',', ','),
            ('NUMBER', 3),
            (',', ','),
            ('NUMBER', 4),
            (',', ','),
            ('NUMBER', 5),
            ('\n', '\n'),
            ('LABEL', 'zero'),
            (':', ':'),
            ('WORD', '.word'),
            ('NUMBER', 0),
            ('\n', '\n'),
            ('LABEL', 'size_word'),
            (':', ':'),
            ('WORD', '.word'),
            ('NUMBER', 2),
            ('\n', '\n'),
            ('LABEL', 'size_array'),
            (':', ':'),
            ('WORD', '.word'),
            ('NUMBER', 10),
            ('\n', '\n'),
            ('DUMP', '.dump'),
            ('LABEL', 'sum'),
            ('\n', '\n'),
            ('CODE', '.code'),
            ('\n', '\n'),
            ('LOAD', 'load'),
            ('REGISTER', 2),
            (',', ','),
            ('LABEL', 'size_word'),
            ('\n', '\n'),
            ('LOAD', 'load'),
            ('REGISTER', 15),
            (',', ','),
            ('LABEL', 'size_array'),
            ('\n', '\n'),
            ('LOAD', 'load'),
            ('REGISTER', 5),
            (',', ','),
            ('LABEL', 'zero'),
            ('\n', '\n'),
            ('RSUB', 'rsub'),
            ('REGISTER', 6),
            (',', ','),
            ('REGISTER', 6),
            ('\n', '\n'),
            ('LABEL', 'rpt'),
            (':', ':'),
            ('ADD', 'add'),
            ('REGISTER', 5),
            (',', ','),
            ('LABEL', 'array'),
            ('(', '('),
            ('REGISTER', 6),
            (')', ')'),
            ('\n', '\n'),
            ('RADD', 'radd'),
            ('REGISTER', 6),
            (',', ','),
            ('REGISTER', 2),
            ('\n', '\n'),
            ('RCOMP', 'rcomp'),
            ('REGISTER', 6),
            (',', ','),
            ('REGISTER', 15),
            ('\n', '\n'),
            ('JNEQ', 'jneq'),
            ('LABEL', 'rpt'),
            ('\n', '\n'),
            ('STORE', 'store'),
            ('REGISTER', 5),
            (',', ','),
            ('LABEL', 'sum'),
            ('\n', '\n'),
            ('HALT', 'halt'),
            ('\n', '\n'),
        ]

        self.tokens.reverse() # for popping from front

    def test_lexer(self):
        """Test lexer."""
        # Give the lexer some input
        error_list, lexems = asm.get_lexems(self.code)
        assert error_list == []

        # Tokenize
        for tok in lexems:
            ground_truth = self.tokens.pop()
            assert eq_token(tok, ground_truth[0], ground_truth[1])

        assert len(self.tokens) == 0

        error_list, lexems = asm.get_lexems("tilda~is_not_allowed")
        assert error_list == ["Illegal character '~' at 1:6"]

        error_list, lexems = asm.get_lexems("0abacaba")
        assert error_list == ["Illegal token '0abacaba' at 1:1"]

    def test_parse(self):
        """Test parser."""
        error_list, code = asm.parse("tilda~is_not_allowed")
        assert error_list == ["Illegal character '~' at 1:6"]

        error_list, code = asm.parse("0abacaba")
        assert error_list == ["Illegal token '0abacaba' at 1:1"]

        error_list, code = asm.parse("load load")
        assert error_list == ["Unexpected 'LOAD' at 1:6"]

        error_list, code = asm.parse("double: halt\ndouble: halt")
        assert error_list == ["Double definition of label 'double'" +
                              " at 2:1 previously defined at 1:1"]

        error_list, code = asm.parse("load R0, array(R0)")
        assert error_list == ["Cannot use R0 for indexing at 1:10"]

        error_list, code = asm.parse("load R0")
        assert error_list == ["Unexpected EOF"]

        error_list, code = asm.parse("load R0, undef_label")
        assert error_list == ["Undefined label 'undef_label' at 1:8"]

        error_list, code = asm.parse(".dump undef_label")
        assert error_list == ["Undefined label 'undef_label' at output"]

        error_list, code = asm.parse(self.code)
        assert error_list == []
        assert code == RESULT_CODE
