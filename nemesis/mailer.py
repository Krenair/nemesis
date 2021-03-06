
from email.mime.text import MIMEText
import smtplib
import traceback
import os

from config import config
from sqlitewrapper import PendingSend

def send_email(toaddr, subject, msg):

    fromaddr = config.get('mailer', 'fromaddr')
    msg = MIMEText(msg)
    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg["Subject"] = subject

    server = smtplib.SMTP_SSL(config.get('mailer', 'smtpserver'), timeout = 5)
    smtp_user = config.get('mailer', 'username')
    smtp_pass = config.get('mailer', 'password')
    server.login(smtp_user, smtp_pass)

    r = server.sendmail(fromaddr, toaddr, str(msg))

    try:
        server.quit()
    except smtplib.sslerror:
        pass

    return len(r) > 0

def send_email_template(toaddr, template_name, template_vars):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_path = os.path.join(script_dir, "templates", template_name + ".txt")

    msg = open(temp_path, 'r').read()

    subject = msg.splitlines()[0]
    assert subject[:8] == "Subject:"
    subject = subject[8:].strip()

    msg = "\n".join(msg.splitlines()[1:])
    msg = msg.format(**template_vars)

    return send_email(toaddr, subject, msg)

def store_template(toaddr, template_name, template_vars):
    ps = PendingSend()
    ps.toaddr = toaddr
    ps.template_name = template_name
    ps.template_vars = template_vars
    ps.save()
    return ps

def try_send(ps):
    try:
        send_email_template(ps.toaddr, ps.template_name, ps.template_vars)
        ps.mark_sent()
    except:
        ps.retried()
        ps.last_error = traceback.format_exc()
    finally:
        ps.save()

def email_template(toaddr, template_name, template_vars):
    # always store the email
    ps = store_template(toaddr, template_name, template_vars)

    # see if we're meant to send it right away
    if not config.getboolean('mailer', 'delayed_send'):
        try_send(ps)
