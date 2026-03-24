"""
Envoi d'emails — SMTP avec templates et pieces jointes.
Usage:
  python scripts/email_sender.py send --to dest@mail.com --subject "Sujet" --body "Message"
  python scripts/email_sender.py send --to dest@mail.com --subject "Rapport" --body-file rapport.html --html
  python scripts/email_sender.py send --to dest@mail.com --subject "Docs" --body "Voir PJ" --attach fichier.pdf
  python scripts/email_sender.py template --name rapport --to dest@mail.com --data data.json
  python scripts/email_sender.py test                     # Test avec un email de diagnostic
  python scripts/email_sender.py config                   # Affiche la configuration SMTP actuelle
"""
import sys
import os
import json
import argparse
import smtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import safe, log_info, log_error, CONFIGS_DIR, OUTPUT_DIR

SMTP_CONFIG_FILE = os.path.join(CONFIGS_DIR, "smtp.json")

# Templates email predefinies
EMAIL_TEMPLATES = {
    "rapport": {
        "subject": "Rapport - {{date}}",
        "body": """<html><body style="font-family: Segoe UI, sans-serif; color: #333;">
<h2 style="color: #2c3e50;">Rapport du {{date}}</h2>
<p>Bonjour,</p>
<p>Veuillez trouver ci-joint le rapport demande.</p>
{{#contenu}}<div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #3498db;">
{{contenu}}
</div>{{/contenu}}
<p>Cordialement,<br><em>Super Codex</em></p>
</body></html>"""
    },
    "notification": {
        "subject": "Notification: {{titre}}",
        "body": """<html><body style="font-family: Segoe UI, sans-serif; color: #333;">
<div style="background: #3498db; color: white; padding: 15px; border-radius: 8px 8px 0 0;">
<h2 style="margin: 0;">{{titre}}</h2>
</div>
<div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
<p>{{message}}</p>
<p style="color: #999; font-size: 12px;">Envoye le {{date}} par Super Codex</p>
</div>
</body></html>"""
    },
    "alerte": {
        "subject": "[ALERTE] {{titre}}",
        "body": """<html><body style="font-family: Segoe UI, sans-serif; color: #333;">
<div style="background: #e74c3c; color: white; padding: 15px; border-radius: 8px;">
<h2 style="margin: 0;">[!] {{titre}}</h2>
</div>
<div style="padding: 20px; border: 2px solid #e74c3c; margin-top: -1px;">
<p><strong>Details:</strong></p>
<p>{{message}}</p>
<p style="color: #999; font-size: 12px;">{{date}}</p>
</div>
</body></html>"""
    },
}


def _load_smtp_config():
    """Charge la configuration SMTP."""
    if os.path.exists(SMTP_CONFIG_FILE):
        with open(SMTP_CONFIG_FILE, "r") as f:
            return json.load(f)

    # Config par defaut (a personnaliser)
    default = {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "username": "",
        "password": "",
        "from_email": "",
        "from_name": "Super Codex"
    }
    os.makedirs(os.path.dirname(SMTP_CONFIG_FILE) or ".", exist_ok=True)
    with open(SMTP_CONFIG_FILE, "w") as f:
        json.dump(default, f, indent=2)
    return default


def _render_template(text, data):
    """Remplacement simple de {{variables}}."""
    for key, value in data.items():
        text = text.replace("{{" + key + "}}", str(value))
    # Nettoyer les variables non remplacees
    import re
    text = re.sub(r"\{\{#\w+\}\}.*?\{\{/\w+\}\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\{\{\w+\}\}", "", text)
    return text


@safe
def send_email(to, subject, body, html=False, attachments=None, cc=None, bcc=None):
    """Envoie un email via SMTP."""
    config = _load_smtp_config()

    if not config.get("username") or not config.get("password"):
        print("[ERREUR] SMTP non configure. Editez configs/smtp.json avec vos identifiants.")
        print(f"  Fichier: {SMTP_CONFIG_FILE}")
        print("  Champs requis: host, port, username, password, from_email")
        print("\n  Pour Gmail: activez 'Mots de passe d'application' dans votre compte Google")
        print("  host: smtp.gmail.com, port: 587, use_tls: true")
        return False

    msg = MIMEMultipart("mixed")
    msg["From"] = f"{config.get('from_name', 'Super Codex')} <{config['from_email']}>"
    msg["To"] = to if isinstance(to, str) else ", ".join(to)
    msg["Subject"] = subject
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    if cc:
        msg["Cc"] = cc if isinstance(cc, str) else ", ".join(cc)
    if bcc:
        msg["Bcc"] = bcc if isinstance(bcc, str) else ", ".join(bcc)

    # Corps du message
    content_type = "html" if html else "plain"
    msg.attach(MIMEText(body, content_type, "utf-8"))

    # Pieces jointes
    if attachments:
        for filepath in attachments:
            if not os.path.exists(filepath):
                print(f"[WARN] Piece jointe ignoree (introuvable): {filepath}")
                continue
            mime_type, _ = mimetypes.guess_type(filepath)
            if mime_type is None:
                mime_type = "application/octet-stream"
            main_type, sub_type = mime_type.split("/", 1)

            with open(filepath, "rb") as f:
                part = MIMEBase(main_type, sub_type)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment",
                          filename=os.path.basename(filepath))
            msg.attach(part)

    # Envoi
    recipients = [to] if isinstance(to, str) else list(to)
    if cc:
        recipients.extend(cc if isinstance(cc, list) else [cc])
    if bcc:
        recipients.extend(bcc if isinstance(bcc, list) else [bcc])

    try:
        if config.get("use_tls", True):
            server = smtplib.SMTP(config["host"], config["port"])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config["host"], config["port"])

        server.login(config["username"], config["password"])
        server.sendmail(config["from_email"], recipients, msg.as_string())
        server.quit()

        att_info = f" + {len(attachments)} PJ" if attachments else ""
        log_info(f"Email envoye: {subject} -> {to}{att_info}")
        print(f"[OK] Email envoye a {to}")
        print(f"  Sujet: {subject}")
        if attachments:
            print(f"  Pieces jointes: {', '.join(os.path.basename(a) for a in attachments)}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[ERREUR] Echec d'authentification SMTP. Verifiez username/password dans configs/smtp.json")
        print("  Pour Gmail: utilisez un 'Mot de passe d'application' (pas votre mot de passe normal)")
        return False
    except Exception as e:
        log_error(f"Email error: {e}")
        print(f"[ERREUR] Envoi echoue: {e}")
        return False


@safe
def send_template(template_name, to, data=None):
    """Envoie un email depuis un template predefini."""
    if template_name not in EMAIL_TEMPLATES:
        print(f"[ERREUR] Template inconnu: {template_name}")
        print(f"  Disponibles: {', '.join(EMAIL_TEMPLATES.keys())}")
        return False

    tmpl = EMAIL_TEMPLATES[template_name]
    data = data or {}
    data.setdefault("date", datetime.now().strftime("%d/%m/%Y %H:%M"))

    subject = _render_template(tmpl["subject"], data)
    body = _render_template(tmpl["body"], data)

    return send_email(to, subject, body, html=True)


@safe
def show_config():
    """Affiche la configuration SMTP actuelle."""
    config = _load_smtp_config()
    print("\n=== Configuration SMTP ===\n")
    for k, v in config.items():
        if k == "password" and v:
            v = "*" * len(v)
        print(f"  {k:15s}: {v}")
    print(f"\n  Fichier: {SMTP_CONFIG_FILE}")
    print(f"\n  Templates disponibles: {', '.join(EMAIL_TEMPLATES.keys())}")

    configured = bool(config.get("username") and config.get("password"))
    if configured:
        print("\n  [OK] SMTP configure")
    else:
        print("\n  [!!] SMTP non configure - editez configs/smtp.json")


@safe
def test_email():
    """Envoie un email de test."""
    config = _load_smtp_config()
    if not config.get("from_email"):
        print("[ERREUR] Configurez d'abord configs/smtp.json (from_email requis)")
        show_config()
        return

    return send_email(
        to=config["from_email"],
        subject=f"[TEST] Super Codex - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        body="""<html><body style="font-family: Segoe UI, sans-serif;">
<h2 style="color: #2ecc71;">[OK] Email de test reussi</h2>
<p>Votre configuration SMTP fonctionne correctement.</p>
<table style="border-collapse: collapse; margin: 20px 0;">
<tr><td style="padding: 5px 15px; border: 1px solid #ddd;"><strong>Date</strong></td>
    <td style="padding: 5px 15px; border: 1px solid #ddd;">""" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + """</td></tr>
<tr><td style="padding: 5px 15px; border: 1px solid #ddd;"><strong>Source</strong></td>
    <td style="padding: 5px 15px; border: 1px solid #ddd;">Super Codex CX</td></tr>
</table>
</body></html>""",
        html=True
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Envoi d'emails SMTP")
    parser.add_argument("action", choices=["send", "template", "test", "config"])
    parser.add_argument("--to", "-t", default=None)
    parser.add_argument("--subject", "-s", default="(Sans sujet)")
    parser.add_argument("--body", "-b", default="")
    parser.add_argument("--body-file", default=None)
    parser.add_argument("--html", action="store_true")
    parser.add_argument("--attach", "-a", nargs="*", default=None)
    parser.add_argument("--cc", default=None)
    parser.add_argument("--bcc", default=None)
    parser.add_argument("--name", "-n", default=None, help="Nom du template")
    parser.add_argument("--data", "-d", default=None, help="Fichier JSON pour template")
    args = parser.parse_args()

    if args.action == "config":
        show_config()
    elif args.action == "test":
        test_email()
    elif args.action == "template":
        if not args.name or not args.to:
            print("[ERREUR] Requis: --name <template> --to <email>")
            sys.exit(1)
        data = {}
        if args.data:
            with open(args.data, "r", encoding="utf-8") as f:
                data = json.load(f)
        send_template(args.name, args.to, data)
    elif args.action == "send":
        if not args.to:
            print("[ERREUR] Destinataire requis: --to email@example.com")
            sys.exit(1)
        body = args.body
        if args.body_file:
            with open(args.body_file, "r", encoding="utf-8") as f:
                body = f.read()
            if args.body_file.endswith(".html"):
                args.html = True
        send_email(args.to, args.subject, body, args.html, args.attach, args.cc, args.bcc)
