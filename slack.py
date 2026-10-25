import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import requests
import sys

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

AUTH_FILE = Path.cwd() / Path("auth/tokens.txt")

IMAGE_PATH = Path.cwd() / "images_slack"
OUTPUT_PATH = Path.cwd() / Path("content") / "announcements.json"

CUTOFF_TIMESTAMP = (
    datetime.now(timezone.utc) - timedelta(days=7)
).timestamp()
'''
1 week from today's date
'''




IMAGE_PATH.mkdir(parents=True, exist_ok=True)



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



def safe_filename(name):
    """Prevent unsafe path characters in downloaded filenames."""
    name = Path(name or "image").name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)



def download_images(message, bot_token: str, verbose: bool = False):
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
        destination = IMAGE_PATH / filename

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
                    print(f"Skipping non-image response: {filename}")
                    continue

                destination.write_bytes(response.content)
                if verbose:
                    print(f"Downloaded: {destination}")

            except requests.RequestException as exc:
                print(f"Failed to download {filename}: {exc}")
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

    verbose = False

    channel_id = args[1]
    bot_token = args[2]


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

        output = {"announcements": announcements}

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        if verbose:
            print(f"Processed {len(announcements)} messages.")
            print(f"JSON saved to: {OUTPUT_PATH}")
            print(f"Images saved to: {IMAGE_PATH.resolve()}")

    except SlackApiError as exc:
        if verbose:
            print("Slack API error:", exc.response.get("error"))
            print("Needed scope:", exc.response.get("needed"))
            print("Granted scopes:", exc.response.get("provided"))


if __name__ == '__main__':
    main(sys.argv)