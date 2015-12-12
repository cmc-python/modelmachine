# -*- coding: utf-8 -*-

"""IDE for model machine."""

from modelmachine.cpu import CPU_LIST
from modelmachine.cu import HALTED

import warnings

POS = [0, 0]
MAX_POS = [20, 20]

# TODO: Visual part don't work

# def init(curses):
#     curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
#     curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
#
# def source_to_screen(pos):
#     pos = list(pos)
#     if 0 <= pos[1] < 2:
#         pass
#     elif 2 <= pos[1] < 6:
#         pos[1] += 1
#     elif 6 <= pos[1] < 10:
#         pos[1] += 2
#     elif 10 <= pos[1] < 14:
#         pos[1] += 3
#     else:
#         pos[1] += 6
#     return pos
#
# def draw(curses, stdscr):
#     stdscr.clear()
#     lines, cols = stdscr.getmaxyx()
#
#     if lines < 10 or cols < 20:
#         stdscr.addstr(0, 0, 'Minimal terminal size is 10x40')
#
#     else:
#         for line in range(0, lines - 2):
#             l_no = hex(line)[2:].rjust(4, '0') + ':'
#             l_text = '00 0000 0000 0000'
#             l_comment = '; comment'
#             stdscr.addstr(line + 1, 1, l_no, curses.color_pair(1))
#             stdscr.addstr(line + 1, 2 + len(l_no), l_text, curses.color_pair(0))
#             stdscr.addstr(line + 1, 3 + len(l_no + l_text), l_comment, curses.color_pair(2))
#
#         pos = source_to_screen(POS)
#         pos[0] += 1
#         pos[1] += 7
#         stdscr.move(pos[0], pos[1])
#     stdscr.refresh()
#
# def update(key):
#     if key == 'KEY_UP':
#         if POS[0] > 0:
#             POS[0] -= 1
#     elif key == 'KEY_DOWN':
#         if POS[0] < MAX_POS[0]:
#             POS[0] += 1
#     elif key == 'KEY_LEFT':
#         if POS[1] > 0:
#             POS[1] -= 1
#     elif key == 'KEY_RIGHT':
#         if POS[1] < MAX_POS[1]:
#             POS[1] += 1
#
# def start(curses):
#     def main(stdscr):
#         init(curses)
#         draw(curses, stdscr)
#         key = stdscr.getkey()
#         while key not in {'q', 'Q'}:
#             update(key)
#             draw(curses, stdscr)
#             key = stdscr.getkey()
#
#     curses.wrapper(main)
#
# import curses as cur
# start(cur)


INSTRUCTION = ('Enter\n'
               '  `(s)tep [count]` to start execution\n'
               '  `(c)ontinue` to continue the program to the end\n'
               '  `(p)rint` registers state\n'
               '  `(m)emory <begin> <end>` to view random access memory\n'
               '  `(q)uit` to quit\n')

def exec_step(cpu, step, command):
    """Exec debug step command."""
    need_help = False

    if cpu.control_unit.get_status() == HALTED:
        print('cannot execute command: machine has been halted')
    else:
        command = command.split()
        try:
            if len(command) == 2:
                count = int(command[1], 0) # may be raised value error
            elif len(command) == 1:
                count = 1
            else:
                raise ValueError()

        except ValueError:
            need_help = True
            count = None

        else:
            for i in range(count):
                i = i # pylint hack
                step += 1
                cpu.control_unit.step()
                print('step {step}:'.format(step=step))
                exec_print(cpu, step)
                if cpu.control_unit.get_status() == HALTED:
                    print('machine has halted')
                    break

    return step, need_help, False

def exec_continue(cpu, step):
    """Exec debug continue command."""

    if cpu.control_unit.get_status() == HALTED:
        print('cannot execute command: machine has halted')
    else:
        cpu.control_unit.run()
        print('machine has halted')

    return step, False, False

def exec_print(cpu, step):
    """Print contents of registers."""

    print("Register states:")
    registers = {cpu.register_names[name]  for name in cpu.register_names}
    for reg in sorted(list(registers)):
        size = cpu.registers.register_sizes[reg]
        data = '0x' + hex(cpu.registers[reg])[2:].rjust(size // 4, '0')
        print('  ' + reg + ' : ' + data)

    return step, False, False

def exec_memory(cpu, step, command):
    """Print contents of RAM."""
    need_help = False

    command = command.split()
    if len(command) == 3:
        try:
            begin = int(command[1], 0)
            end = int(command[2], 0)
        except ValueError:
            need_help = True
        else:
            print(cpu.io_unit.store_hex(begin,
                                        (end - begin) * cpu.ram.word_size))
    else:
        need_help = True

    return step, need_help, False

def exec_command(cpu, step, command):
    """Exec one command and generate step, need_help and need_quit variables."""

    if command[0] == "s":
        return exec_step(cpu, step, command)
    elif command[0] == "c":
        return exec_continue(cpu, step)
    elif command[0] == "p":
        return exec_print(cpu, step)
    elif command[0] == "m":
        return exec_memory(cpu, step, command)
    elif command[0] == "q":
        return step, False, True
    else:
        return step, True, False


def debug(cpu):
    """Debug cycle."""
    import readline
    readline = readline

    print('Wellcome to interactive debug mode.\n'
          'Beware: now every error breaks the debugger.')
    need_quit = False
    need_help = True
    step = 0

    while not need_quit:
        if need_help:
            print(INSTRUCTION)
            need_help = False

        try:
            command = input('> ') + " " # length > 0
        except EOFError:
            command = 'quit'
            print(command)

        try:
            with warnings.catch_warnings(record=True) as warns:
                warnings.simplefilter("always")

                step, need_help, need_quit = exec_command(cpu, step, command)

                for warn in warns:
                    print('Warning:', warn.message)

        except Exception as e:
            print('Error:', e.args[0])
            cpu.alu.halt()
            print('machine has halted')

def get_cpu(source, protect_memory):
    """Return empty cpu or raise the ValueError."""
    arch = source[0].strip()
    if arch in CPU_LIST:
        cpu = CPU_LIST[arch](protect_memory)
        return cpu
    else:
        raise ValueError('Unexpected arch (found in first line): {arch}'
                         .format(arch=arch))

def get_program(filename, protect_memory):
    """Read model machine program."""
    with open(filename, 'r') as source_file:
        source = source_file.readlines()
        cpu = get_cpu(source, protect_memory)
        cpu.load_program(source)
        return cpu
