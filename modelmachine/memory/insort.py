from __future__ import annotations


def insort(a: list[range], x: range) -> None:
    lo = bisect_right(a, x)
    a.insert(lo, x)


def bisect_right(a: list[range], x: range) -> int:
    lo = 0
    hi = len(a)

    while lo < hi:
        mid = (lo + hi) // 2
        if (x.start, x.stop) < (a[mid].start, a[mid].stop):
            hi = mid
        else:
            lo = mid + 1
    return lo
