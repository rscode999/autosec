'''
Functions to print colored text to the standard output
'''

RED = '\033[31m'
YELLOW = '\033[33m'
NORMAL = '\033[0m'

def print_color(
    values: str, 
    color: str, 
    end: str | None ='\n', 
    flush: bool = False
) -> None:
    '''
    Prints `values` to the standard output in the color `color`.

    Args:
        values (str): items to print
        color (str): color to print in (RED, YELLOW)
        end (str or None, default=newline): string to print after the values are printed
        flush (bool, default=False): whether to flush the standard output stream after printing
    '''
    
    print(f"{color}{values}{NORMAL}", end=end, flush=flush)