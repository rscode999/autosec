import json
from pathlib import Path
import re
import requests
import sys

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from autosec_constants import *

from autosec_colors import print_color, RED, YELLOW



def get_all_pages(method, **kwargs):
    """Yield individual messages across all API pages."""
    cursor = None

    while True:
        params = {**kwargs, "limit": 200}
        if cursor:
            params["cursor"] = cursor

        response = method(**params)

        for message in response.get("messages", []):
            # Only regular messages.
            if message.get("type") != "message":
                continue

            # Exclude channel join/leave events.
            if message.get("subtype") in {
                "channel_join",
                "channel_leave",
            }:
                continue

            # Exclude thread replies.
            if (
                message.get("thread_ts")
                and message["thread_ts"] != message["ts"]
            ):
                continue

            # Keep messages from the last seven days.
            timestamp = message.get("ts")
            if not timestamp or float(timestamp) < CUTOFF_TIMESTAMP:
                continue

            yield message

        # Advance pagination even if every message was filtered out.
        cursor = response.get("response_metadata", {}).get(
            "next_cursor", ""
        )
        if not cursor:
            break



def safe_filename(name: str):
    """Prevent unsafe path characters in downloaded filenames."""
    name = Path(name or "image").name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)



def download_images(message, bot_token: str, verbose: bool = False) -> list[str]:
    """Download Slack-uploaded image files and return their filenames."""

    filenames = []

    for file_info in message.get("files", []):
        mimetype = file_info.get("mimetype", "")

        if not mimetype.startswith("image/"):
            continue

        url = (
            file_info.get("url_private_download")
            or file_info.get("url_private")
        )

        if not url:
            if verbose:
                print(f"Skipping image without download URL: "
                    f"{file_info.get('name', 'unknown')}")
            continue

        original_name = safe_filename(
            file_info.get("name", "image")
        )

        # Prefix with Slack's file ID to avoid filename collisions.
        file_id = safe_filename(
            file_info.get("id", str(message.get("ts", "image")))
        )
        filename = f"{file_id}_{original_name}"
        destination = SLACK_IMAGE_DIRECTORY / filename

        if not destination.exists():
            try:
                response = requests.get(
                    url,
                    headers={
                        "Authorization":
                            f"Bearer {bot_token}"
                    },
                    timeout=60,
                )
                response.raise_for_status()

                # Avoid saving an HTML error page as an image.
                if not response.headers.get(
                    "Content-Type", ""
                ).startswith("image/"):
                    if verbose:
                        print(f"Skipping non-image response: {filename}")
                    continue

                destination.write_bytes(response.content)
                if verbose:
                    print(f"Downloaded: {destination}")

            except requests.RequestException as exc:
                print_color(f"Failed to download {filename}: {exc}", YELLOW)
                continue

        filenames.append(filename)

    return filenames



def make_announcement(message, bot_token: str):
    """Convert a Slack message into the requested JSON structure."""
    lines = message.get("text", "").splitlines()

    title = lines[0] if lines else ""
    text = "\n".join(lines[1:]) if len(lines) > 1 else ""

    return {
        "title": title,
        "text": text,
        "images": download_images(message, bot_token),
    }



def main(args: list[str]):
    '''
    Main function

    args[1] = channel ID, args[2] = bot token, args[3] (optional, default=False) = verbose option
    '''

    SLACK_IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    if len(args) < 3:
        print_color(f'Usage for {__file__}: python {__file__} <Slack channel ID> <bot token> <verbose (optional, default=False)>', RED)
        sys.exit(1)
    
    channel_id = args[1]
    bot_token = args[2]
    verbose = (False if len(args)<4 else bool(args[3]))

    if not channel_id.startswith("C"):
        print_color(f'Channel ID ({channel_id}) is invalid', RED)
        sys.exit(1)
    if not bot_token.startswith("xoxb-"):
        print_color(f'Bot token ({bot_token}) is invalid', RED)
        sys.exit(1)

    client = WebClient(token=bot_token)

    try:

        messages_by_ts = {}

        # Retrieve messages posted in the last seven days.
        for message in get_all_pages(
            client.conversations_history,
            channel=channel_id
        ):
            messages_by_ts[message["ts"]] = message

        # Oldest first.
        messages = sorted(
            messages_by_ts.values(),
            key=lambda m: float(m["ts"]),
        )

        announcements = [
            make_announcement(message, bot_token)
            for message in messages
        ]

        # Write announcements to output file
        output = {"announcements": announcements}
        with open(ANNOUNCEMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"Processed {len(announcements)} messages.")
            print(f"JSON saved to: {ANNOUNCEMENTS_FILE}")
            print(f"Images saved to: {SLACK_IMAGE_DIRECTORY.resolve()}\n")

    except SlackApiError as exc:
        print_color("Slack API error:", exc.response.get("error"), RED)
        print_color("    Needed scope:", exc.response.get("needed"), RED)
        print_color("    Granted scopes:", exc.response.get("provided"), RED)
        print_color("    Bot token used: ", RED)
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv)