
from pathlib import Path
import win32com.client as win32
import json
import html
import re
import sys

from slack import SLACK_IMAGE_PATH

CURRENT_DIRECTORY = Path.cwd()

CONTENT_DIRECTORY = CURRENT_DIRECTORY / Path("content")
FOOTER_DIRECTORY = CURRENT_DIRECTORY  / Path("footer")

DIVIDER = """
    <hr style="
        border: 0;
        border-top: 1px solid #cccccc;
        margin: 20px 0;
    ">
"""


def generate_image(image_path: Path, mail: win32.CDispatch, width: int | str = 300, height: int | str = 'auto'):
    assert type(width)==int or (type(width)==str and width=='auto')
    assert type(height)==int or (type(height)==str and height=='auto')

    html_string = ""

    image_filename = image_path.name
    content_id = image_filename

    # Ensure the image exists before attaching it
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

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
    
    Mutates `mail`.

    Parameters:
        announcement_dict (dict): announcement to add. Contains 2 fields: "text", a string, and "images", a list of strings 
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
        announcement_html += generate_image(SLACK_IMAGE_PATH / image, mail)

    return announcement_html



def generate_footer(footer_dict: dict) -> str:
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
            <img src="{FOOTER_DIRECTORY / footer["image"]}"
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
    """


    # initialize the Outlook application object
    outlook = win32.Dispatch("Outlook.Application")

    # Create a new mail item (0 represents an olMailItem)
    mail = outlook.CreateItem(0)

    with open(CONTENT_DIRECTORY / "content.json", 'r', encoding='utf-8') as file:
        data = json.load(file) 

    # Set the recipients and subject
    mail.To = args[1]
    mail.Subject = data["email"]["subject"]


    mail_html = "<html>\n<body>"

    mail_html += generate_header(data["header"])

    mail_html += DIVIDER
    mail_html += generate_image(CURRENT_DIRECTORY / Path("images/events.png"), mail, width=450)
    mail_html += DIVIDER

    for announcement in data["announcements"]:
        mail_html += generate_announcement(announcement, mail)

        mail_html += DIVIDER

    # Footer
    mail_html += generate_footer(data["footer"])
    mail_html += "\n</body>\n</html>"


    # Yeet the mail
    mail.HTMLBody = mail_html
    mail.Send()




if __name__ == "__main__":
    main(sys.argv)
