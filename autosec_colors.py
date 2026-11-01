RED = '\033[31m'
YELLOW = '\033[33m'
NORMAL = '\033[0m'

def print_color(
    *values, 
    color: str = NORMAL, 
    sep: str | None = ' ', 
    end: str | None ='\n', 
    flush: bool = False
) -> None:
    '''
    Prints `values` to the standard output in the color `color`.

    Args:
        values: items to print
        color (str, default=NORMAL): color to print in (RED, YELLOW, NORMAL)
        sep (str or None, default=' '): separator between values
        end (str or None, default=newline): string to print after the values are printed
        flush (bool, default=False): whether to flush the standard output stream after printing
    '''
    
    print(color, end='')
    print(values, sep=sep, end='')
    print(NORMAL, end=end, flush=flush)

