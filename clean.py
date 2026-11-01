import json 
import shutil
from pathlib import Path

from autosec_constants import ANNOUNCEMENTS_FILE, EMAIL_CONTENT_FILE, ROOT_DIRECTORY

def main():
    # load email contents
    with open(EMAIL_CONTENT_FILE, 'r') as f:
        email_contents = json.load(f)

    
    try:
        # remove announcements, if they exist
        email_contents.pop('announcements')

        # write contents back
        with open(EMAIL_CONTENT_FILE, 'w') as f:
            json.dump(email_contents, f, indent=4)

    except KeyError:
        pass


    # delete automatically generated announcements file
    ANNOUNCEMENTS_FILE.unlink(missing_ok=True)

    # delete pycache
    shutil.rmtree(str(ROOT_DIRECTORY / '__pycache__'))
    shutil.rmtree(str(ROOT_DIRECTORY / '.venv/Lib/site-packages/__pycache__'))


if __name__ == '__main__':
    main()
