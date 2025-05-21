# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from pdf_watermark import add_watermark
from email.message import EmailMessage
import smtplib
import os

app = FastAPI()

# CORS erlauben für alle Domains (z. B. deine HTML-Seite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    code: str
    email: str
    format: str  # "pdf" oder "epub"

@app.post("/check-code")
def check_code(data: CodeRequest):
    df = pd.read_csv("codes.csv")

    match = df[df['code'].str.upper() == data.code.upper()]
    if match.empty or match.iloc[0]['used']:
        return { "valid": False }

    # Markiere als verwendet
    df.loc[df['code'].str.upper() == data.code.upper(), 'used'] = True
    df.to_csv("codes.csv", index=False)

    if data.format == "pdf":
        filename = f"ebook_{data.code}.pdf"
        add_watermark("2025-04-30-ReThink-Money-v45.pdf", filename, data.email)
    else:
        filename = "ReThinkMoney.epub"  # Falls du diese Datei hast

    send_email(data.email, filename)
    return { "valid": True }

def send_email(to_address, file_path):
     print(f"[📬] Sende E-Mail an: {to_address}")
    print(f"[📎] Anhang: {file_path}")

    msg = EmailMessage()
    msg["Subject"] = "Dein ReThink Money eBook"
    msg["From"] = os.getenv("SMTP_USER")
    msg["To"] = to_address
    msg.set_content("Im Anhang findest du dein persönliches Exemplar von ReThink Money.")

    with open(file_path, "rb") as f:
        file_data = f.read()
        msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=os.path.basename(file_path))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        smtp.send_message(msg)
     print("[✅] E-Mail erfolgreich versendet.")
    except Exception as e:
        print("[❌] Fehler beim Versenden der E-Mail:", e)
