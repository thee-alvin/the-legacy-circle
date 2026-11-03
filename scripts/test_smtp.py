from pathlib import Path
import os
import smtplib
import ssl
from dotenv import load_dotenv

load_dotenv(Path(".env"), override=True)

host = os.getenv("TLC_SMTP_HOST")
port = int(os.getenv("TLC_SMTP_PORT", "587"))
username = os.getenv("TLC_SMTP_USERNAME")
password = os.getenv("TLC_SMTP_PASSWORD")

print("========================================")
print("TLC SMTP DIAGNOSTIC")
print("========================================")
print("HOST :", host)
print("PORT :", port)
print("USER :", username)
print()

try:
    if port == 465:
        print("Mode : SMTP SSL")
        with smtplib.SMTP_SSL(
            host,
            port,
            timeout=30,
            context=ssl.create_default_context()
        ) as server:
            server.ehlo()
            server.login(username, password)

    else:
        print("Mode : SMTP STARTTLS")
        with smtplib.SMTP(
            host,
            port,
            timeout=30
        ) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(username, password)

    print()
    print("RESULT: SMTP CONNECTION + LOGIN SUCCESSFUL")

except Exception as error:
    print()
    print("RESULT: SMTP FAILED")
    print("ERROR :", repr(error))
