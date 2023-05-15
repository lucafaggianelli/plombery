from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from httpx import URL

from .templates import render_pipeline_run


_WELL_KNOWN_SERVERS = {
    "gmail.com": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
    }
}


def _get_email_server_config(email_server: str):
    return _WELL_KNOWN_SERVERS[email_server]


def send(channel: URL, title: str, data: dict):
    assert channel.username and channel.password and channel.host

    sender_email = f"{channel.username}@{channel.host}"
    to_addresses = channel.params.get_list("to") or [sender_email]

    # Create a MIMEMultipart object and set sender, receiver, and subject
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = title

    # Attach the HTML message
    html = render_pipeline_run(
        data["pipeline"].name,
        data["status_verb"],
        data["pipeline_run_url"],
    )
    msg.attach(MIMEText(html, "html"))

    # SMTP server configuration
    server_config = _get_email_server_config(channel.host)

    # Create a secure connection to the SMTP server
    server = smtplib.SMTP(server_config["smtp_server"], server_config["smtp_port"])
    server.starttls()
    server.login(channel.username, channel.password)

    # Send the email
    server.send_message(msg)
    server.quit()
