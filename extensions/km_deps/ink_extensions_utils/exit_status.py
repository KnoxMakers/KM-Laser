import functools
import sys

'''
Attempts to
ensure that error conditions are reported (which inkex does not do properly).
When an error is detected (by catching a
'SystemExit'), the program quits with a non-0 exit status.

Assumes that `func` (usually `effect` or `affect`) only raises `SystemExit`
(e.g. by calling `quit()`, `exit()` or `sys.exit()`) on error conditions.
In the inkscape extensions code, this is true as far as I can tell.
For non-inkscape extensions code, this assumption should also be fine, since
there is never a reason to raise a SystemExit in a function unless there's an
error (e.g. `return` could be used instead).

Usage:

if __name__ == '__main__':
    e = AnEffect()
    exit_status.run(e.affect)
'''

def run(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except SystemExit as se:
        if (se.args == (None,) or se.args == ()): # if quit(), exit(), or sys.exit() was called w/o args
            sys.exit("\nIt is probable that an error occurred in the inkscape software.")
        else: # SystemExit was raised with an error code. Just let it happen.
            raise se
