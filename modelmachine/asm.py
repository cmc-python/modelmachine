# -*- coding: utf-8 -*-

"""Model machine assembler."""

from ply import lex

literals = ['(', ')', ':', ',']

opcodes = {
    # Opcodes
    'load'  : 'LOAD',
    'add'   : 'ADD',
    'sub'   : 'SUB',
    'smul'  : 'SMUL',
    'sdiv'  : 'SDIV',
    'comp'  : 'COMP',
    'umul'  : 'UMUL',
    'udiv'  : 'UDIV',
    'store' : 'STORE',
    'rmove' : 'RMOVE',
    'radd'  : 'RADD',
    'rsub'  : 'RSUB',
    'rsmul' : 'RSMUL',
    'rsdiv' : 'RSDIV',
    'rcomp' : 'RCOMP',
    'rumul' : 'RUMUL',
    'rudiv' : 'RUDIV',
    'jump'  : 'JUMP',
    'jeq'   : 'JEQ',
    'jneq'  : 'JNEQ',
    'sjl'   : 'SJL',
    'sjgeq' : 'SJGEQ',
    'sjleq' : 'SJLEQ',
    'sjg'   : 'SJG',
    'ujl'   : 'UJL',
    'ujgeq' : 'UJGEQ',
    'ujleq' : 'UJLEQ',
    'ujg'   : 'UJG',
    'halt'  : 'HALT',
}

# List of token names.   This is always required
tokens = [
    'COMMENT',

    'NUMBER',
    'REGISTER',

    'PREPROCINSTR',
    'LABEL',
] + list(opcodes.values())

def lexer():

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'
    t_ignore_COMMENT = r';.*'

    # A regular expression rule with some action code
    def t_NUMBER(t):
        r'(?:0x[\da-f]+)|(?:0b[01]+)|(?:0o[0-7]+)|(?:\d+)'
        t.value = int(t.value, 0)
        return t

    # Get register number
    def t_REGISTER(t):
        r'r[\da-f]'
        t.value = int(t.value[1], 16)
        return t

    def t_PREPROCINSTR(t):
        r'\.[a-z]+'
        t.value = t.value[1:]
        return t

    def t_LABEL(t):
        r'[a-z_][\da-z_]*'
        t.type = opcodes.get(t.value, 'LABEL')    # Check for opcodes
        return t

    # Define a rule so we can track line numbers
    def t_newline(t):
        r'\n'
        t.lexer.lineno += len(t.value)

    # Error handling rule
    def t_error(t):
        print("Illegal character '{char}'".format(char=t.value[0]))
        t.lexer.skip(1)

    # Compute column.
    #     input is the input text string
    #     token is a token instance
    def find_column(input,token):
        last_cr = input.rfind('\n',0,token.lexpos)
        if last_cr < 0:
            last_cr = 0
        column = (token.lexpos - last_cr) + 1
        return column

    # Build the lexer
    return lex.lex()

