import json 
import sys 

from autosec_constants import *


def main(args: list[str]) -> None:
    '''
    Main function.

    Inserts the JSON defined at `ANNOUNCEMENTS_FILE` into the content given at `CONTENT_FILE`,
    which also contains definitions of the header, footer, etc.
    '''

    verbose = (bool(args[1]) if len(args)>1 else False)

    with open(ANNOUNCEMENTS_FILE, 'r') as f:
        announcements = json.load(f)

    with open(CONTENT_FILE, 'r') as f:
        combined = json.load(f)

    combined["announcements"] = announcements['announcements'] 

    with open(CONTENT_FILE, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f'Copied announcements from "{str(ANNOUNCEMENTS_FILE)}" to "{str(CONTENT_FILE)}"\n')

if __name__ == '__main__':
    main(sys.argv)