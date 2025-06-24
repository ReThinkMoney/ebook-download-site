from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import smtplib
from email.message import EmailMessage
from pdf_watermark import add_watermark
import os

app = FastAPI()

CODES_FILE = "codes.csv"
PDF_TEMPLATE = "2025-04-30-ReThink-Money-v45.pdf"
OUTPUT_DIR = "out/"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_codes():
    return pd.read_csv(CODES_FILE)

def save_codes(df):
    df.to_csv(CODES_FILE, index=False)

class CodeRequest(BaseModel):
    code: str
    email: str
    format: str  # wird ignoriert, immer PDF

@app.post("/check-code")
async def check_code(req: CodeRequest):
    df = load_codes()
    match = df[df['code'].str.upper() == req.code.upper()]
    if match.empty:
        return JSONResponse(content={ "valid": False })

    remaining = 20 - int(match.iloc[0].get("count", 0))
    if remaining <= 0:
        return JSONResponse(content={ "valid": False, "reason": "used" })

    # PDF personalisieren und speichern
    output_pdf = os.path.join(OUTPUT_DIR, f"ebook_{req.code}.pdf")
    add_watermark(PDF_TEMPLATE, output_pdf, req.email)

    # E-Mail senden
    send_email(req.email, output_pdf)

    # Downloadzähler erhöhen
    df.loc[df['code'].str.upper() == req.code.upper(), "count"] = 20 - (remaining - 1)
    save_codes(df)

    return { "valid": True, "remaining": remaining - 1 }

def send_email(to_email, attachment_path):
    msg = EmailMessage()
    msg['Subject'] = "Ihr Exemplar ReThink Money"
    msg['From'] = os.getenv("SMTP_USER")
    msg['To'] = to_email
    msg.set_content(
        "Hallo, vielen Dank für das Interesse, wie der digitale Euro / digitales Zentralbankgeld "
        "zum wichtigen Baustein für eine bessere Welt werden kann.

"
        "Euer Exemplar ReThink Money ist im Anhang dieser Mail.

"
        "Dies ist eine no-Reply Mailadresse. Bei Fragen, Anmerkungen oder Kritik "
        "am besten über Threema an E7T69HDV."
    )

    with open(attachment_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename='Buch ReThink Money.pdf')

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        smtp.send_message(msg)
