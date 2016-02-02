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
            ('PREPROCINSTR', 'config'),
            ('NUMBER', 256),
            ('LABEL', 'sum'),
            (':', ':'),
            ('PREPROCINSTR', 'word'),
            ('NUMBER', 0),
            ('LABEL', 'array'),
            (':', ':'),
            ('PREPROCINSTR', 'word'),
            ('NUMBER', 1),
            (',', ','),
            ('NUMBER', 2),
            (',', ','),
            ('NUMBER', 3),
            (',', ','),
            ('NUMBER', 4),
            (',', ','),
            ('NUMBER', 5),
            ('LABEL', 'zero'),
            (':', ':'),
            ('PREPROCINSTR', 'word'),
            ('NUMBER', 0),
            ('LABEL', 'size_word'),
            (':', ':'),
            ('PREPROCINSTR', 'word'),
            ('NUMBER', 2),
            ('LABEL', 'size_array'),
            (':', ':'),
            ('PREPROCINSTR', 'word'),
            ('NUMBER', 10),
            ('PREPROCINSTR', 'dump'),
            ('LABEL', 'sum'),
            ('PREPROCINSTR', 'code'),
            ('LOAD', 'load'),
            ('REGISTER', 2),
            (',', ','),
            ('LABEL', 'size_word'),
            ('LOAD', 'load'),
            ('REGISTER', 15),
            (',', ','),
            ('LABEL', 'size_array'),
            ('LOAD', 'load'),
            ('REGISTER', 5),
            (',', ','),
            ('LABEL', 'zero'),
            ('RSUB', 'rsub'),
            ('REGISTER', 6),
            (',', ','),
            ('REGISTER', 6),
            ('LABEL', 'rpt'),
            (':', ':'),
            ('ADD', 'add'),
            ('REGISTER', 5),
            (',', ','),
            ('LABEL', 'array'),
            ('(', '('),
            ('REGISTER', 6),
            (')', ')'),
            ('REGISTER', 10),
            ('LABEL', 'dd'),
            ('REGISTER', 6),
            (',', ','),
            ('REGISTER', 2),
            ('REGISTER', 12),
            ('LABEL', 'omp'),
            ('REGISTER', 6),
            (',', ','),
            ('REGISTER', 15),
            ('JNEQ', 'jneq'),
            ('LABEL', 'rpt'),
            ('STORE', 'store'),
            ('REGISTER', 5),
            (',', ','),
            ('LABEL', 'sum'),
            ('HALT', 'halt'),
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
