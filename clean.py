import json 

from autosec_constants import ANNOUNCEMENTS_FILE, EMAIL_CONTENT_FILE

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



if __name__ == '__main__':
    main()
