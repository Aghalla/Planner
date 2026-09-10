"""Pure-Python Jalali (Shamsi) calendar utils — no external dependency.

Ported from the well-tested jalaali algorithm (same as lifeboard's jalali.js).
Saturday-first week layout compatible.
"""
from datetime import date as _date


def _div(a, b):
    return a // b


def _mod(a, b):
    return a - (a // b) * b


def to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy <= 1600:
        jy = 0
        gy -= 621
    else:
        jy = 979
        gy -= 1600
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy + _div(gy2 + 3, 4) - _div(gy2 + 99, 100)
            + _div(gy2 + 399, 400) - 80 + gd + g_d_m[gm - 1])
    jy += 33 * _div(days, 12053)
    days %= 12053
    jy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        jy += _div(days - 1, 365)
        days = _mod(days - 1, 365)
    if days < 186:
        jm = 1 + _div(days, 31)
        jd = 1 + _mod(days, 31)
    else:
        jm = 7 + _div(days - 186, 30)
        jd = 1 + _mod(days - 186, 30)
    return jy, jm, jd


def to_gregorian(jy, jm, jd):
    jy += 1595
    days = (-355668 + 365 * jy + _div(jy, 33) * 8
            + _div(_mod(jy, 33) + 3, 4) + jd
            + ((jm - 1) * 31 if jm < 7 else (jm - 7) * 30 + 186))
    gy = 400 * _div(days, 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * _div(days, 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * _div(days, 1461)
    days %= 1461
    if days > 365:
        gy += _div(days - 1, 365)
        days = _mod(days - 1, 365)
    gd = days + 1
    leap = (gy % 4 == 0 and gy % 100 != 0) or gy % 400 == 0
    sal_a = [0, 31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gm = 0
    while gm < 13 and gd > sal_a[gm]:
        gd -= sal_a[gm]
        gm += 1
    return gy, gm, gd


def is_jalali_leap(jy):
    return jy % 33 in (1, 5, 9, 13, 17, 22, 26, 30)


def jalali_month_length(jy, jm):
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap(jy) else 29


def today_jalali():
    t = _date.today()
    return to_jalali(t.year, t.month, t.day)
