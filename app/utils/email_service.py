from app.config import setting
import smtplib
from email.mime.text import MIMEText
def send_email(subject, body, recipients):
    # Create a MIMEText object with the body of the email.
    msg = MIMEText(body)
    # Set the subject of the email.
    msg['Subject'] = subject
    # Set the sender's email.
    msg['From'] = setting.EMAIL_SENDER
    # Join the list of recipients into a single string separated by commas.
    msg['To'] = ', '.join(recipients)
    # Connect to Gmail's SMTP server using SSL.
    with smtplib.SMTP_SSL(setting.EMAIL_SMTP_SERVER, setting.EMAIL_SMTP_PORT) as smtp_server:
        # Login to the SMTP server using the sender's credentials.
        smtp_server.login(setting.EMAIL_SENDER, setting.EMAIL_PASSWORD)
        # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
        smtp_server.sendmail(setting.EMAIL_SENDER, recipients, msg.as_string())