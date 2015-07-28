# -*- coding: utf-8 -*-

"""IDE for model machine."""

from modelmachine.cpu import CPU_LIST

POS = [0, 0]
MAX_POS = [20, 20]

# Visual part don't work

"""
def init(curses):
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

def source_to_screen(pos):
    pos = list(pos)
    if 0 <= pos[1] < 2:
        pass
    elif 2 <= pos[1] < 6:
        pos[1] += 1
    elif 6 <= pos[1] < 10:
        pos[1] += 2
    elif 10 <= pos[1] < 14:
        pos[1] += 3
    else:
        pos[1] += 6
    return pos

def draw(curses, stdscr):
    stdscr.clear()
    lines, cols = stdscr.getmaxyx()

    if lines < 10 or cols < 20:
        stdscr.addstr(0, 0, 'Minimal terminal size is 10x40')

    else:
        for line in range(0, lines - 2):
            l_no = hex(line)[2:].rjust(4, '0') + ':'
            l_text = '00 0000 0000 0000'
            l_comment = '; comment'
            stdscr.addstr(line + 1, 1, l_no, curses.color_pair(1))
            stdscr.addstr(line + 1, 2 + len(l_no), l_text, curses.color_pair(0))
            stdscr.addstr(line + 1, 3 + len(l_no + l_text), l_comment, curses.color_pair(2))

        pos = source_to_screen(POS)
        pos[0] += 1
        pos[1] += 7
        stdscr.move(pos[0], pos[1])
    stdscr.refresh()

def update(key):
    if key == 'KEY_UP':
        if POS[0] > 0:
            POS[0] -= 1
    elif key == 'KEY_DOWN':
        if POS[0] < MAX_POS[0]:
            POS[0] += 1
    elif key == 'KEY_LEFT':
        if POS[1] > 0:
            POS[1] -= 1
    elif key == 'KEY_RIGHT':
        if POS[1] < MAX_POS[1]:
            POS[1] += 1

def start(curses):
    def main(stdscr):
        init(curses)
        draw(curses, stdscr)
        key = stdscr.getkey()
        while key not in {'q', 'Q'}:
            update(key)
            draw(curses, stdscr)
            key = stdscr.getkey()

    curses.wrapper(main)

import curses as cur
start(cur)
"""

def print_registers(cpu):
    """Print contents of registers."""
    registers = {cpu.register_names[name]  for name in cpu.register_names}
    for reg in sorted(list(registers)):
        print('  ' + reg + ' : ' + hex(cpu.registers[reg]))

INSTRUCTION = ('Enter\n'
               '  `(s)tep [count]` to start execution\n'
               '  `(r)un` to run the program to the end\n'
               '  `(p)rint` registers state\n'
               '  `(m)emory <begin> <end>` to view random access memory\n'
               '  `(q)uit` to quit\n')

def debug(cpu):
    """Debug cycle."""
    print('Wellcome to interactive debug mode.\n'
          'Beware: now every error breaks the debugger.')
    need_quit = False
    need_help = True
    step = 0

    while not need_quit:
        if need_help:
            print(INSTRUCTION)
            need_help = False
        command = input() + " " # length > 0

        if command[0] == "s":
            command = command.split()
            if len(command) == 2:
                count = int(command[1], 0)
            elif len(command) == 1:
                count = 1
            else:
                need_help = True
                continue

            for i in range(count):
                i = i # pylint hack
                step += 1
                cpu.control_unit.step()
                print('step {step}:'.format(step=step))
                print_registers(cpu)

        elif command[0] == "r":
            cpu.control_unit.run()

        elif command[0] == "p":
            print("Register states:")
            print_registers(cpu)

        elif command[0] == "m":
            command = command.split()
            if len(command) == 3:
                begin = int(command[1], 0)
                end = int(command[2], 0)
                print(cpu.io_unit.store_hex(begin,
                                            (end - begin) * cpu.ram.word_size))
            else:
                need_help = True

        elif command[0] == "q":
            need_quit = True

        else:
            need_help = True

def get_cpu(source):
    """Return empty cpu or raise the ValueError."""
    arch = source[0].strip()
    if arch in CPU_LIST:
        cpu = CPU_LIST[arch]()
        return cpu
    else:
        raise ValueError('Unexpected arch (found in first line): {arch}'
                         .format(arch=arch))

def get_program(filename):
    """Read model machine program."""
    with open(filename, 'r') as source_file:
        source = source_file.readlines()
        cpu = get_cpu(source)
        cpu.load_program(source)
        return cpu
