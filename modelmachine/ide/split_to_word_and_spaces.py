from __future__ import annotations


def split_to_word_and_spaces(s: str) -> list[str]:
    res = []
    if not s:
        return res

    last = s[0].isspace()
    word = ""
    for i, c in enumerate(s):
        if c.isspace() != last:
            res.append(word)
            word = c
            last = c.isspace()
        else:
            word += c

        if i == len(s) - 1 and word:
            res.append(word)

    return res
