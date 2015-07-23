# -*- coding: utf-8 -*-

"""IDE for model machine."""

from modelmachine.cpu import BordachenkovaMM3

import tempfile
from configparser import ConfigParser

POS = [0, 0]
MAX_POS = [20, 20]

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

# import curses as cur
# start(cur)

def load_source(string_list, cpu_list):
    """Load config and source from string array."""
    source = [line.strip() for line in string_list]
    code_start = source.index("[code]")

    config_file = tempfile.TemporaryFile('w+')
    config_file.write('\n'.join(source[:code_start]))
    config_file.seek(0)

    config = ConfigParser()
    config.read_file(config_file)
    config = config['config']

    cpu = None
    arch = config["arch"]

    if arch in cpu_list:
        cpu = cpu_list[arch]()
        cpu.load_source(source[code_start + 1:])
    else:
        raise ValueError('Unexpected arch: {arch}'.format(arch=arch))

    return (config, cpu)

def load_data(config, cpu):
    """Load sequence of decimal numbers into memory."""
    addresses = [int(index) for index in config["input"].split(",")]
    data = [int(value) for value in data.split()]
    for address, value in zip(addresses, data):
        cpu.load_dec(address, value)

def store_data(config, cpu):
    """Write sequence of decimal numbers to output."""
    addresses = [int(index) for index in config["output"].split(",")]
    data = '\n'.join(str(cpu.get_int(address)) for address in addresses)
    for address, value in zip(addresses, data):
        cpu.load_dec(address, value)

def run_file(filename, cpu_list):
    """Execute all run cycle."""
    with open(filename, 'r') as source_file:
        source = source_file.readlines()
    config, cpu = load_source(source, cpu_list)

    with open(config["input_file"], 'r') as input_data:
        data = ' '.join(input_data.readlines())
    load_data(config, cpu, data)

