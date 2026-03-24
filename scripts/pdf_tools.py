"""
Outils PDF avances — Merge, split, watermark, extract.
Usage:
  python scripts/pdf_tools.py merge file1.pdf file2.pdf -o combined.pdf
  python scripts/pdf_tools.py split input.pdf --pages 1-3 -o extract.pdf
  python scripts/pdf_tools.py watermark input.pdf "CONFIDENTIEL" -o marked.pdf
  python scripts/pdf_tools.py info input.pdf
  python scripts/pdf_tools.py count input.pdf
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ensure, safe, log_info, OUTPUT_DIR

@safe
def merge_pdfs(files, output):
    ensure("PyPDF2")
    from PyPDF2 import PdfMerger
    merger = PdfMerger()
    for f in files:
        if not os.path.exists(f):
            print(f"[WARN] Fichier ignore (introuvable): {f}")
            continue
        merger.append(f)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    merger.write(output)
    merger.close()
    log_info(f"PDF merge: {len(files)} fichiers -> {output}")
    print(f"[OK] {len(files)} PDFs fusionnes -> {output}")

@safe
def split_pdf(input_file, pages, output):
    ensure("PyPDF2")
    from PyPDF2 import PdfReader, PdfWriter
    reader = PdfReader(input_file)
    writer = PdfWriter()

    if "-" in pages:
        start, end = pages.split("-")
        start, end = int(start) - 1, int(end)
    else:
        start, end = int(pages) - 1, int(pages)

    for i in range(max(0, start), min(len(reader.pages), end)):
        writer.add_page(reader.pages[i])

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    log_info(f"PDF split: pages {pages} -> {output}")
    print(f"[OK] Pages {pages} extraites -> {output}")

@safe
def watermark_pdf(input_file, text, output):
    ensure("PyPDF2")
    ensure("reportlab")
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import Color
    import io

    # Create watermark
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    c.setFont("Helvetica-Bold", 50)
    c.setFillColor(Color(0.8, 0.8, 0.8, alpha=0.3))
    c.saveState()
    c.translate(A4[0]/2, A4[1]/2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()
    packet.seek(0)

    watermark = PdfReader(packet)
    reader = PdfReader(input_file)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark.pages[0])
        writer.add_page(page)

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "wb") as f:
        writer.write(f)
    log_info(f"PDF watermark: {text} -> {output}")
    print(f"[OK] Watermark '{text}' applique -> {output}")

@safe
def pdf_info(input_file):
    ensure("PyPDF2")
    from PyPDF2 import PdfReader
    reader = PdfReader(input_file)
    meta = reader.metadata
    info = {
        "fichier": os.path.basename(input_file),
        "pages": len(reader.pages),
        "titre": getattr(meta, "title", None) or "N/A",
        "auteur": getattr(meta, "author", None) or "N/A",
        "createur": getattr(meta, "creator", None) or "N/A",
        "taille": f"{os.path.getsize(input_file) / 1024:.1f} KB",
    }
    for k, v in info.items():
        print(f"  {k:12s}: {v}")

@safe
def pdf_count(input_file):
    ensure("PyPDF2")
    from PyPDF2 import PdfReader
    print(len(PdfReader(input_file).pages))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Outils PDF avances")
    parser.add_argument("action", choices=["merge", "split", "watermark", "info", "count"])
    parser.add_argument("files", nargs="+", help="Fichier(s) PDF")
    parser.add_argument("--pages", "-p", default="1-1")
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args()

    if args.action == "merge":
        out = args.output or os.path.join(OUTPUT_DIR, "merged.pdf")
        merge_pdfs(args.files, out)
    elif args.action == "split":
        out = args.output or os.path.join(OUTPUT_DIR, "split.pdf")
        split_pdf(args.files[0], args.pages, out)
    elif args.action == "watermark":
        text = args.files[1] if len(args.files) > 1 else "CONFIDENTIEL"
        out = args.output or os.path.join(OUTPUT_DIR, "watermarked.pdf")
        watermark_pdf(args.files[0], text, out)
    elif args.action == "info":
        pdf_info(args.files[0])
    elif args.action == "count":
        pdf_count(args.files[0])
