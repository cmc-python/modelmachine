# -*- coding: utf-8 -*-

"""Test case for assembler."""

from modelmachine import asm

def eq_token(token, type, value):
    return token.type == type and token.value == value

class TestASM:

    code = None
    tokens = None

    def setup(self):

        self.code = '''
        .config 0x100
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
            ('NUMBER', 256),
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
        lexer = asm.lexer()

        # Give the lexer some input
        lexer.input(self.code.lower())

        # Tokenize
        for tok in lexer:
            ground_truth = self.tokens.pop()
            assert eq_token(tok, ground_truth[0], ground_truth[1])

        assert len(self.tokens) == 0
