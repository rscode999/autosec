'''
Inserts the JSON defined at `autosec_constants.ANNOUNCEMENTS_FILE` into the content JSON given at `autosec_constants.EMAIL_CONTENT_FILE`,
which also contains definitions of the header, footer, etc.

Converts the output of `slack.py` into a format usable by `outlook.py`.
'''

import json 
import sys 

from autosec_constants import ANNOUNCEMENTS_FILE, EMAIL_CONTENT_FILE
from autosec_colors import print_color, RED


def main(args: list[str]) -> None:
    '''
    Main function.

    Inserts the JSON defined at `ANNOUNCEMENTS_FILE` into the content given at `EMAIL_CONTENT_FILE`,
    which also contains definitions of the header, footer, etc.

    args[1] (optional) = verbose option
    '''

    verbose = (bool(args[1]) if len(args)>1 else False)

    with open(ANNOUNCEMENTS_FILE, 'r') as f:
        announcements = json.load(f)

    combined = dict()
    try:
        with open(EMAIL_CONTENT_FILE, 'r') as f:
            combined = json.load(f)
    except FileNotFoundError:
        print_color(f'Email content file "{str(EMAIL_CONTENT_FILE.absolute())}" was not found', RED)
        sys.exit(1)

    combined["announcements"] = announcements['announcements'] 

    with open(EMAIL_CONTENT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f'Copied announcements from "{str(ANNOUNCEMENTS_FILE)}" to "{str(EMAIL_CONTENT_FILE)}"\n')


if __name__ == '__main__':
    main(sys.argv)