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

def get_cpu(source):
    """Return empty cpu or raise the ValueError."""
    arch = source[0].strip()
    if arch in CPU_LIST:
        cpu = CPU_LIST[arch]()
        return cpu
    else:
        raise ValueError('Unexpected arch (found in first line): {arch}'
                         .format(arch=arch))
