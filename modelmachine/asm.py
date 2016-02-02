# -*- coding: utf-8 -*-

"""Model machine assembler."""

from modelmachine.memory import RandomAccessMemory
from modelmachine.io import InputOutputUnit

from ply import lex, yacc

import sys

class g:
    lexer = None
    parser = None
    error_list = []
    mapper = [] # Will fulled at last step
    output = []

literals = ['(', ')', ':', ',', '\n']

opcodes = {
    # Opcodes
    'load'  : 0x00,
    'add'   : 0x01,
    'sub'   : 0x02,
    'smul'  : 0x03,
    'sdiv'  : 0x04,
    'comp'  : 0x05,
    'umul'  : 0x13,
    'udiv'  : 0x14,
    'store' : 0x10,
    'rmove' : 0x20,
    'radd'  : 0x21,
    'rsub'  : 0x22,
    'rsmul' : 0x23,
    'rsdiv' : 0x24,
    'rcomp' : 0x25,
    'rumul' : 0x33,
    'rudiv' : 0x34,
    'jump'  : 0x80,
    'jeq'   : 0x81,
    'jneq'  : 0x82,
    'sjl'   : 0x83,
    'sjgeq' : 0x84,
    'sjleq' : 0x85,
    'sjg'   : 0x86,
    'ujl'   : 0x93,
    'ujgeq' : 0x94,
    'ujleq' : 0x95,
    'ujg'   : 0x96,
    'halt'  : 0x99,
}

preproc_instructions = {
    '.config' : 'CONFIG',
    '.word'   : 'WORD',
    '.code'   : 'CODE',
    '.dump'   : 'DUMP',
}

# List of token names.   This is always required
tokens = [
    'COMMENT',

    'NUMBER',
    'REGISTER',

    'LABEL',
] + [op.upper() for op in opcodes.keys()] + list(preproc_instructions.values())

def find_column(lexpos):
    last_cr = g.lexer.lexdata.rfind('\n', 0, lexpos)
    if last_cr < 0:
        last_cr = 0
    column = (lexpos - last_cr)
    return column

def position(t):
    return '{line}:{col}'.format(line=t.lineno,
                                 col=find_column(t.lexpos))

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
        if t.value in preproc_instructions:
            t.type = preproc_instructions[t.value]
            return t
        else:
            t.type = 'error'
            return t

    def t_LABEL(t):
        r'[a-z_][\da-z_]*'
        if t.value in opcodes:
            t.type = t.value.upper()
        else:
            t.type = 'LABEL'
        return t

    # Define a rule so we can track line numbers
    def t_newline(t):
        r'\n'
        t.lexer.lineno += len(t.value)
        t.type = '\n'
        return t

    # Error handling rule
    def t_error(t):
        g.error_list.append("Illegal character '{char}' at {position}"
                            .format(char=t.value[0], position=position(t)))

    # Build the lexer
    g.lexer = lex.lex()
    return g.lexer

def parser():

    start = 'program'

    def p_empty(p):
        """empty :"""
        pass

    def p_listtail(p):
        """numberlist : NUMBER
           labellist : LABEL
        """
        p[0] = [p[1]]

    def p_list(p):
        """numberlist : numberlist ',' NUMBER
           labellist : labellist ',' LABEL
        """
        p[0] = p[1].copy()
        p[0].append(p[3])

    def p_address_label(p):
        """address : LABEL"""
        p[0] = (0, p[1])

    def p_address_register(p):
        """address : LABEL '(' REGISTER ')'"""
        if p[3] == 0:
            g.error_list.append("Cannot use R0 for indexing at {line}:{col}"
                                .format(line=p.lineno(3), col=find_column(p.lexpos(1))))
        else:
            p[0] = (p[3], p[1])

    def p_line_empty(p):
        """line : empty"""

    def p_line_deflabel(p):
        """line : deflabel line"""

    def p_deflabel_label(p):
        """deflabel : LABEL ':'"""
        if p[1] in g.label_table:
            prev = g.label_table[p[1]][1]
            g.error_list.append("Double definition of label '{label}' at {line}:{col}"
                                .format(line=p.lineno(1), col=find_column(p.lexpos(1))) +
                                " previously defined at {line}:{col}"
                                .format(label=p[1], line=prev['line'], col=prev['col']))
            raise SyntaxError
        else:
            prev = {'line': p.lineno(1), 'col': find_column(p.lexpos(1))}
            g.label_table[p[1]] = (g.pos, prev)

    def p_line_config(p):
        """line : CONFIG NUMBER"""
        g.pos = p[2]

    def p_line_code(p):
        """line : CODE"""
        g.pos = 0

    def p_line_word(p):
        """line : WORD numberlist"""
        for number in p[2]:
            g.ram.put(g.pos, number, 32)
            g.pos += 2

    def p_line_dump(p):
        """line : DUMP labellist"""
        g.output.extend(p[2])

    def p_error(p):
        if not p:
            g.error_list.append("Unexpected EOF")
            return

        g.error_list.append("Unexpected '{token}' at {position}"
                            .format(token=p.type, position=position(p)))

    def p_line_memops(p):
        """line : LOAD  REGISTER ',' address
                | ADD   REGISTER ',' address
                | SUB   REGISTER ',' address
                | SMUL  REGISTER ',' address
                | SDIV  REGISTER ',' address
                | COMP  REGISTER ',' address
                | UMUL  REGISTER ',' address
                | UDIV  REGISTER ',' address
                | STORE REGISTER ',' address
        """
        data = opcodes[p[1]] << 8 | p[2] << 4 | p[4][0]
        g.ram.put(g.pos, data, 16)
        g.mapper.append((g.pos + 1, p[4][1], p.lineno(3), find_column(p.lexpos(3))))
        g.pos += 2

    def p_line_halt(p):
        """line : HALT"""
        g.ram.put(g.pos, 0x9900, 16)
        g.pos += 1

    def p_program(p):
        """program : line
                   | program '\\n' line"""
        pass

    lexer()

    # Build the parser
    g.parser = yacc.yacc()
    g.pos = 0
    g.label_table = dict()
    g.ram = RandomAccessMemory(word_size=16,
                               memory_size=2 ** 16,
                               endianess='big',
                               is_protected=False)

    return g.parser

if __name__ == "__main__":
    mmasm_parser = parser()
    code = """
    .config 0x100
    sum: .word 0
    array: .word 1,2,3,4,5
    zero: .word 0
    size_word: .word 2
    size_array: .word 5
    .dump sum
    .code
    load R2, size_word
    load RF, size_array
    load R5, zero
    halt
    """

    print(code)
    mmasm_parser.parse(code.lower())

    if len(g.error_list) == 0:
        for insert in g.mapper:
            if insert[1] in g.label_table:
                g.ram.put(insert[0], g.label_table[insert[1]][0], 16)
            else:
                g.error_list.append("Undefined label '{label}' at {line}:{col}"
                                    .format(line=insert[2], col=insert[3]))

    if len(g.error_list) == 0:
        io_unit = InputOutputUnit(g.ram, 0, 16)
        print(io_unit.store_hex(0, 16 * g.pos))
    else:
        for error in g.error_list:
            print(error, file=sys.stderr)
        exit(1)
