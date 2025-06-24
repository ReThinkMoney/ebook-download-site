from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import smtplib
import os
import csv
from email.message import EmailMessage
from PyPDF2 import PdfReader, PdfWriter
from tempfile import NamedTemporaryFile

app = FastAPI()

# ✅ CORS aktivieren für GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rethinkmoney.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CODES_FILE = "codes.csv"
PDF_TEMPLATE = "ReThink_Money_v45.pdf"

class CodeRequest(BaseModel):
    code: str
    email: str
    format: str = "pdf"

def personalize_pdf(email: str) -> str:
    reader = PdfReader(PDF_TEMPLATE)
    writer = PdfWriter()
    for page in reader.pages:
        page.merge_text(
            text=f"Persönliches Exemplar für {email} – nur zur privaten Verwendung",
            tx=50, ty=20, rotation=0, size=10
        )
        writer.add_page(page)
    tmp_file = NamedTemporaryFile(delete=False, suffix=".pdf")
    with open(tmp_file.name, "wb") as f:
        writer.write(f)
    return tmp_file.name

def send_email(recipient: str, filename: str):
    msg = EmailMessage()
    msg['Subject'] = "Ihr Exemplar ReThink Money"
    msg['From'] = os.getenv("SMTP_USER")
    msg['To'] = recipient
    msg.set_content("""Hallo,

vielen Dank für dein Interesse an unserem Projekt: Wie der digitale Euro / digitales Zentralbankgeld zum wichtigen Baustein für eine bessere Welt werden kann.

Dein persönliches Exemplar von ReThink Money findest du im Anhang dieser Mail.

Dies ist eine no-reply-Adresse. Bei Fragen oder Feedback erreichst du uns am besten per Threema: E7T69HDV
""")

    with open(filename, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="Buch ReThink Money.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        smtp.send_message(msg)

@app.post("/check-code")
async def check_code(data: CodeRequest):
    updated_rows = []
    valid = False
    remaining = 0
    reason = "invalid"

    with open(CODES_FILE, newline='') as csvfile:
        rows = list(csv.DictReader(csvfile))
        for row in rows:
            if row['code'] == data.code:
                remaining = int(row['uses'])
                if remaining > 0:
                    valid = True
                    remaining -= 1
                    row['uses'] = str(remaining)
                    reason = ""
                else:
                    reason = "used"
            updated_rows.append(row)

    if valid:
        filename = personalize_pdf(data.email)
        send_email(data.email, filename)
        with open(CODES_FILE, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['code', 'uses'])
            writer.writeheader()
            writer.writerows(updated_rows)
        return {"valid": True, "remaining": remaining}
    else:
        return JSONResponse(content={"valid": False, "reason": reason})
