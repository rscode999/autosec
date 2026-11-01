from pathlib import Path
import win32com.client as win32
import json
import html
import re
import sys

from autosec_constants import *
from autosec_colors import print_color, RED


def generate_image(
    image_path: Path,
    mail: win32.CDispatch,
    width: int | str = 300,
    height: int | str = 'auto'
) -> str:
    """
    Returns the HTML that inserts the image at `image_path` into the mail message `mail`,
    giving the image width `width` and height `height`.

    Mutates `mail`.

    Args:
        image_path (pathlib.Path): path to the image to add
        mail (win32com.client.CDispatch): Outlook mail object to add the image to
        width (int or str, default=300): width of the image to add. Positive integer, or the string 'auto'
        height (int or str, default='auto'): height of the image to add. Positive integer, or the string 'auto'
    Returns:
        str: HTML containing the image at `image_path`
    """
    assert (type(width)==int and width>0) or (type(width)==str and width=='auto'), 'Width must be a positive integer or "auto"'
    assert (type(height)==int and height>0) or (type(height)==str and height=='auto'), 'Height must be a positive integer or "auto"'

    html_string = ""

    image_filename = image_path.name
    content_id = image_filename

    # Ensure the image exists before attaching it
    if not image_path.is_file():
        raise FileNotFoundError(f"Image '{image_path}' not found")

    # Add attachment to mail object
    attachment = mail.Attachments.Add(str(image_path), 1, 0)

    # Assign a Content-ID to the attachment
    MAPI_PROPERTY_CID = (
        "http://schemas.microsoft.com/mapi/proptag/0x3712001F"
    )
    attachment.PropertyAccessor.SetProperty(
        MAPI_PROPERTY_CID, content_id
    )

    # Add image to HTML output
    html_string += f"""<img src="cid:{html.escape(content_id, quote=True)}"
    alt="{html.escape(image_filename, quote=True)}"
    width="{width}"
    style="width:{width}px; height:{height}; display:block;">
    <br><br>"""

    return html_string


def generate_header(header_dict: dict) -> str:
    """
    Returns the HTML containing the header information in `header_dict`.

    Args:
        header_dict (dict): dictionary containing the email message's title and subheading.
        Contains the fields "title" (str), the header for the email message; and "text" (str), the subheading for the email message
    Returns:
        str: HTML with email header
    """

    title = html.escape(header_dict["title"])
    text = html.escape(header_dict["text"]).replace("\n", "<br>\n")

    header_html = f"""
        <h1 style="
            font-family: OCRB, monospace;
            font-size: 22px;
            line-height: 26px;
            font-weight: normal;
            color: #40c0ed;
            margin: 0 0 10px 0;
        ">
            <span style="
                font-family: OCRB, monospace;
                font-size: 22px;
                color: #40c0ed;
            ">{title}</span>
        </h1>

        <p style="
            font-family: Arial, sans-serif;
            font-size: 16px;
            line-height: 20px;
            color: #194959;
            margin: 0;
        ">
            <span style="
                font-family: Arial, sans-serif;
                font-size: 16px;
                color: #194959;
            ">{text}</span>
        </p>
    """

    return header_html


def generate_announcement(announcement_dict: dict, mail: win32.CDispatch) -> str:
    """
    Returns the HTML message for the announcement defined in `announcement_dict`, adding the announcement to `mail`.

    Inserts all images into the given mail message object.

    `announcement_dict` must contain the following fields:
    - "title" (str), the announcement's headline
    - "text" (str), the content of the announcement
    - "images" (list[str]), a list of all filepaths to the announcement's flyers, posters, etc, with paths relative to the `SLACK_IMAGE_DIRECTORY` directory
    
    Mutates `mail`.

    Parameters:
        announcement_dict (dict): announcement to add
        mail (win32com.client.CDispatch): email message object to add the announcement to
    Returns:
        str: HTML message with the given announcement
    """

    announcement_html = ""

    # Add the text
    title = html.escape(announcement_dict["title"])

    announcement_html += f"""
        <h2 style="
            font-family: OCRB, monospace;
            font-size: 18px;
            font-weight: normal;
            color: #197a9c;
            margin: 0 0 10px 0;
        ">{title}</h2>
    """

    # Add the formatted body text
    text = html.escape(announcement_dict["text"])
    text = re.sub(r'\*(.*?)\*', r'<b>\1</b>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)

    announcement_html += f"""
        <p style="
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #000000;
            margin: 0 0 15px 0;
        ">{text}</p>
    """

    # Add all the images
    for image in announcement_dict["images"]:
        announcement_html += generate_image(SLACK_IMAGE_DIRECTORY / image, mail)

    return announcement_html



def generate_footer(footer_dict: dict) -> str:
    """
    Returns the HTML containing the footer information in `footer_dict`.

    `footer_dict` must contain the following fields:
    - "text" (str), the closing message of the email
    - "images" (list[dict])

    Each element of the "images" list must contain the following fields:
    - "image" (str), the path to the image, relative to the `IMAGES_DIRECTORY` directory
    - "link" (str), the link to attach to the image

    Args:
        footer_dict (dict): dictionary containing the email message's final message and linked images

    Returns:
        str: HTML with email footer
    """

    footer_html = ""

    footer_text = html.escape(footer_dict["text"])
    footer_text = footer_text.replace("\n", "<br>")

    footer_html += f"""
        <p style="
            font-family: OCRB, monospace;
            font-size: 14px;
            color: #000000;
            margin: 0 0 15px 0;
        ">{footer_text}</p>
    """
    
    for footer in footer_dict["images"]:
        footer_html += f"""
        <a href="{footer["link"]}" target="_blank">
            <img src="{IMAGE_DIRECTORY / footer["image"]}"
                alt="Footer image"
                height="35"
                style="height:35px; width:auto; max-width:100%;
                        border:0; display:block;">
        </a>
        """

    return footer_html



def main(args: list[str]) -> None:
    """
    Main function

    args[1] = mail receipient, args[2] (optional, default=False) = verbose option
    """
    if len(args) < 2:
        print_color(f"Usage for {__file__}: python {__file__} <mail recipient's email> <verbose (optional, default=False)>", RED)
        sys.exit(1)

    verbose = (bool(args[2]) if len(args)>2 else False)

    # initialize the Outlook application object
    outlook = win32.Dispatch("Outlook.Application")

    # Create a new mail item (0 represents an olMailItem)
    mail = outlook.CreateItem(0)

    with open(CONTENT_FILE, 'r', encoding='utf-8') as file:
        data = json.load(file) 

    # Set the recipients and subject
    mail.To = args[1]
    mail.Subject = data["email"]["subject"]


    mail_html = "<html>\n<body>"

    mail_html += generate_header(data["header"])

    if verbose:
        print('Email header generated')

    mail_html += DIVIDER
    mail_html += generate_image(IMAGE_DIRECTORY / "events.png", mail, width=450)
    mail_html += DIVIDER

    for announcement in data["announcements"]:
        mail_html += generate_announcement(announcement, mail)
        mail_html += DIVIDER

        if verbose:
            print(f"""Added announcement "{announcement['title']}" """)

    # Footer
    mail_html += generate_footer(data["footer"])
    mail_html += "\n</body>\n</html>"

    if verbose:
        print('Email footer generated')

    # Yeet the mail
    mail.HTMLBody = mail_html
    mail.Send()

    if verbose:
        print(f'Email sent to "{args[1]}"\n')


if __name__ == "__main__":
    main(sys.argv)
