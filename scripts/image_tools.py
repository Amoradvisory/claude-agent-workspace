"""
Outils image — Resize, compress, watermark, convert, info, crop, thumbnail.
Usage:
  python scripts/image_tools.py info photo.jpg
  python scripts/image_tools.py resize photo.jpg 800x600 -o resized.jpg
  python scripts/image_tools.py compress photo.jpg --quality 60 -o light.jpg
  python scripts/image_tools.py watermark photo.jpg "Mon texte" -o marked.jpg
  python scripts/image_tools.py convert photo.png jpeg -o photo.jpg
  python scripts/image_tools.py crop photo.jpg 100,100,500,400 -o cropped.jpg
  python scripts/image_tools.py thumbnail photo.jpg 200x200 -o thumb.jpg
  python scripts/image_tools.py rotate photo.jpg 90 -o rotated.jpg
  python scripts/image_tools.py flip photo.jpg horizontal -o flipped.jpg
  python scripts/image_tools.py batch resize "*.jpg" 800x600
"""
import sys
import os
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import ensure, safe, log_info, OUTPUT_DIR

ensure("Pillow", "PIL")

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ExifTags

@safe
def image_info(path):
    """Affiche les informations d'une image."""
    img = Image.open(path)
    size_kb = os.path.getsize(path) / 1024
    info = {
        "fichier": os.path.basename(path),
        "format": img.format or "N/A",
        "mode": img.mode,
        "dimensions": f"{img.width}x{img.height}",
        "pixels": f"{img.width * img.height:,}",
        "taille": f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB",
    }

    # EXIF data
    exif = {}
    try:
        raw_exif = img._getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if isinstance(value, (str, int, float)) and tag in (
                    "Make", "Model", "DateTime", "ExposureTime",
                    "FNumber", "ISOSpeedRatings", "FocalLength"
                ):
                    exif[tag] = value
    except Exception:
        pass

    if exif:
        info["exif"] = exif

    for k, v in info.items():
        if k == "exif":
            print(f"  {'EXIF':15s}:")
            for ek, ev in v.items():
                print(f"    {ek:13s}: {ev}")
        else:
            print(f"  {k:15s}: {v}")
    return info

@safe
def resize_image(path, size_str, output=None):
    """Redimensionne une image (ex: 800x600, 50%)."""
    img = Image.open(path)

    if "%" in size_str:
        pct = int(size_str.replace("%", "")) / 100
        new_size = (int(img.width * pct), int(img.height * pct))
    elif "x" in size_str:
        w, h = size_str.split("x")
        new_size = (int(w), int(h))
    else:
        # Single number = max dimension, keep ratio
        max_dim = int(size_str)
        ratio = min(max_dim / img.width, max_dim / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))

    resized = img.resize(new_size, Image.LANCZOS)
    out = output or _auto_output(path, "_resized")
    resized.save(out, quality=95)
    log_info(f"Image resize: {img.width}x{img.height} -> {new_size[0]}x{new_size[1]}")
    print(f"[OK] Redimensionne {img.width}x{img.height} -> {new_size[0]}x{new_size[1]} -> {out}")
    return out

@safe
def compress_image(path, quality=70, output=None):
    """Compresse une image (JPEG quality 1-95)."""
    img = Image.open(path)
    if img.mode == "RGBA":
        img = img.convert("RGB")
    out = output or _auto_output(path, "_compressed", ".jpg")
    img.save(out, "JPEG", quality=quality, optimize=True)
    orig_size = os.path.getsize(path) / 1024
    new_size = os.path.getsize(out) / 1024
    ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
    log_info(f"Image compress: {orig_size:.0f}KB -> {new_size:.0f}KB ({ratio:.0f}% reduction)")
    print(f"[OK] Compresse: {orig_size:.0f}KB -> {new_size:.0f}KB (-{ratio:.0f}%) -> {out}")
    return out

@safe
def watermark_image(path, text, output=None, opacity=128, font_size=0):
    """Ajoute un watermark texte diagonal sur l'image."""
    img = Image.open(path).convert("RGBA")

    # Overlay transparent
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    if font_size == 0:
        font_size = max(20, min(img.width, img.height) // 10)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # Dessiner le texte en diagonale au centre
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Creer un sous-image pour le texte avec rotation
    txt_img = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    txt_draw.text((10, 10), text, fill=(255, 255, 255, opacity), font=font)
    txt_img = txt_img.rotate(30, expand=True, resample=Image.BICUBIC)

    # Placer au centre
    paste_x = (img.width - txt_img.width) // 2
    paste_y = (img.height - txt_img.height) // 2
    overlay.paste(txt_img, (paste_x, paste_y))

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out = output or _auto_output(path, "_watermarked")
    result.save(out, quality=95)
    log_info(f"Image watermark: '{text}' -> {out}")
    print(f"[OK] Watermark '{text}' applique -> {out}")
    return out

@safe
def convert_image(path, target_format, output=None):
    """Convertit entre formats (jpeg, png, webp, bmp, tiff, gif)."""
    img = Image.open(path)
    fmt = target_format.upper().replace("JPG", "JPEG")

    if fmt == "JPEG" and img.mode == "RGBA":
        img = img.convert("RGB")

    ext = "." + target_format.lower().replace("jpeg", "jpg")
    out = output or _auto_output(path, "", ext)
    img.save(out, fmt, quality=95)
    log_info(f"Image convert: {img.format} -> {fmt}")
    print(f"[OK] Converti {img.format or '?'} -> {fmt} -> {out}")
    return out

@safe
def crop_image(path, coords, output=None):
    """Recadre une image (left,top,right,bottom)."""
    img = Image.open(path)
    parts = [int(x.strip()) for x in coords.split(",")]
    if len(parts) == 4:
        box = tuple(parts)
    else:
        print("[ERREUR] Format attendu: left,top,right,bottom (ex: 100,100,500,400)")
        return None

    cropped = img.crop(box)
    out = output or _auto_output(path, "_cropped")
    cropped.save(out, quality=95)
    print(f"[OK] Recadre {box} -> {cropped.width}x{cropped.height} -> {out}")
    return out

@safe
def thumbnail_image(path, size_str="200x200", output=None):
    """Cree une miniature (garde les proportions)."""
    img = Image.open(path)
    w, h = [int(x) for x in size_str.split("x")]
    img.thumbnail((w, h), Image.LANCZOS)
    out = output or _auto_output(path, "_thumb")
    img.save(out, quality=90)
    print(f"[OK] Thumbnail {img.width}x{img.height} -> {out}")
    return out

@safe
def rotate_image(path, angle, output=None):
    """Rotation (90, 180, 270 ou angle libre)."""
    img = Image.open(path)
    rotated = img.rotate(-int(angle), expand=True, resample=Image.BICUBIC)
    out = output or _auto_output(path, f"_rot{angle}")
    rotated.save(out, quality=95)
    print(f"[OK] Rotation {angle} degres -> {out}")
    return out

@safe
def flip_image(path, direction="horizontal", output=None):
    """Miroir horizontal ou vertical."""
    img = Image.open(path)
    if direction.startswith("h"):
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
    else:
        flipped = img.transpose(Image.FLIP_TOP_BOTTOM)
    out = output or _auto_output(path, f"_flip{direction[0]}")
    flipped.save(out, quality=95)
    print(f"[OK] Flip {direction} -> {out}")
    return out

@safe
def batch_images(action, pattern, *args, output_dir=None):
    """Operations batch sur plusieurs images."""
    files = glob.glob(pattern)
    if not files:
        print(f"[WARN] Aucun fichier ne correspond a: {pattern}")
        return

    out_dir = output_dir or os.path.join(OUTPUT_DIR, "batch_images")
    os.makedirs(out_dir, exist_ok=True)

    actions = {
        "resize": resize_image,
        "compress": compress_image,
        "convert": convert_image,
        "thumbnail": thumbnail_image,
    }

    if action not in actions:
        print(f"[ERREUR] Action batch inconnue: {action}. Disponibles: {', '.join(actions)}")
        return

    print(f"[...] Batch {action} sur {len(files)} fichier(s)")
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        ext = os.path.splitext(f)[1]
        if action == "convert" and args:
            ext = "." + args[0].lower().replace("jpeg", "jpg")
        out = os.path.join(out_dir, name + ext)
        if action == "resize" and args:
            actions[action](f, args[0], output=out)
        elif action == "compress":
            q = int(args[0]) if args else 70
            actions[action](f, quality=q, output=out)
        elif action == "convert" and args:
            actions[action](f, args[0], output=out)
        elif action == "thumbnail" and args:
            actions[action](f, args[0], output=out)
        else:
            actions[action](f, output=out)

    print(f"[OK] Batch {action}: {len(files)} fichier(s) traite(s) -> {out_dir}")


def _auto_output(path, suffix, ext=None):
    """Genere un chemin de sortie automatique."""
    base, orig_ext = os.path.splitext(os.path.basename(path))
    ext = ext or orig_ext
    out = os.path.join(OUTPUT_DIR, f"{base}{suffix}{ext}")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Outils image avances")
    parser.add_argument("action", choices=[
        "info", "resize", "compress", "watermark", "convert",
        "crop", "thumbnail", "rotate", "flip", "batch"
    ])
    parser.add_argument("file", help="Fichier image ou pattern glob")
    parser.add_argument("param", nargs="?", default=None, help="Parametre (taille, texte, format, angle...)")
    parser.add_argument("--output", "-o", default=None)
    parser.add_argument("--quality", "-q", type=int, default=70)
    args = parser.parse_args()

    if args.action == "info":
        image_info(args.file)
    elif args.action == "resize":
        resize_image(args.file, args.param or "50%", args.output)
    elif args.action == "compress":
        compress_image(args.file, args.quality, args.output)
    elif args.action == "watermark":
        watermark_image(args.file, args.param or "CONFIDENTIEL", args.output)
    elif args.action == "convert":
        if not args.param:
            print("[ERREUR] Format cible requis (jpeg, png, webp, bmp)")
            sys.exit(1)
        convert_image(args.file, args.param, args.output)
    elif args.action == "crop":
        crop_image(args.file, args.param or "0,0,100,100", args.output)
    elif args.action == "thumbnail":
        thumbnail_image(args.file, args.param or "200x200", args.output)
    elif args.action == "rotate":
        rotate_image(args.file, args.param or "90", args.output)
    elif args.action == "flip":
        flip_image(args.file, args.param or "horizontal", args.output)
    elif args.action == "batch":
        # cx image batch resize "*.jpg" 800x600
        extra = sys.argv[4:] if len(sys.argv) > 4 else []
        batch_images(args.file, args.param, *extra, output_dir=args.output)
