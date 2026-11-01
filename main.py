import combine 
import outlook 
import slack

import argparse
import json

from autosec_constants import TOKEN_FILE


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='Print extra information to the console')

    args = parser.parse_args()

    with open(TOKEN_FILE, 'r') as f:
        token_args = json.load(f)


    slack.main(['', token_args['channel_id'], token_args['bot_token'], args.verbose])
    combine.main(['', args.verbose])
    outlook.main(['', token_args['recipient_email'], args.verbose])