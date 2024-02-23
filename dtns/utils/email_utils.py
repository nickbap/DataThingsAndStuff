from threading import Thread

from flask import current_app
from flask_mail import Message

from dtns import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, msg_body=None, msg_html=None):
    msg = Message(
        subject,
        sender=sender,
        recipients=recipients,
    )
    msg.body = msg_body
    msg.html = msg_html

    Thread(
        target=send_async_email, args=(current_app._get_current_object(), msg)
    ).start()


def send_new_comment_notif(comment):
    send_email(
        f"Test - new comment from: {comment.user.username}",
        ("Data Things and Stuff", current_app.config["MAIL_USERNAME"]),
        [current_app.config["SITE_ADMIN"]],
        f"{comment.user.username} just said:\n {comment.text}",
    )
