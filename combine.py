import json 
from pathlib import Path
import sys

ANNOUNCEMENTS_PATH = Path('content/announcements.json')

COMBINED_CONTENT_PATH = Path('content/content.json')

def main() -> None:
    '''
    Main function.

    Inserts the JSON defined at `ANNOUNCEMENTS_PATH` into the content given at `COMBINED_CONTENT_PATH`,
    which also contains definitions of the header, footer, etc.
    '''

    with open(ANNOUNCEMENTS_PATH, 'r') as f:
        announcements = json.load(f)

    with open(COMBINED_CONTENT_PATH, 'r') as f:
        combined = json.load(f)

    combined["announcements"] = announcements['announcements'] 

    with open(COMBINED_CONTENT_PATH, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    main()