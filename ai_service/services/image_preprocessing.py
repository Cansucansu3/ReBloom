import io
import os
from pathlib import Path

from PIL import Image


BASE_DIR = Path(__file__).resolve().parents[1]
REMBG_MODEL_DIR = BASE_DIR / "models" / "rembg"
BACKGROUND_REMOVAL_MAX_SIZE = 768


def background_removal_enabled():
    return os.getenv("REBLOOM_ENABLE_BACKGROUND_REMOVAL", "0").lower() not in {
        "0",
        "false",
        "no",
    }


def flatten_alpha(image, background=(255, 255, 255)):
    if image.mode != "RGBA":
        return image.convert("RGB")

    canvas = Image.new("RGB", image.size, background)
    canvas.paste(image, mask=image.getchannel("A"))
    return canvas


def resize_for_background_removal(image):
    image = image.convert("RGBA")
    width, height = image.size
    longest_side = max(width, height)

    if longest_side <= BACKGROUND_REMOVAL_MAX_SIZE:
        return image

    scale = BACKGROUND_REMOVAL_MAX_SIZE / longest_side
    size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def remove_background(image):
    if not background_removal_enabled():
        return None

    try:
        os.environ.setdefault("U2NET_HOME", str(REMBG_MODEL_DIR))
        from rembg import remove
    except ImportError:
        return None

    try:
        result = remove(resize_for_background_removal(image))
        if isinstance(result, Image.Image):
            return flatten_alpha(result)

        if isinstance(result, bytes):
            return flatten_alpha(Image.open(io.BytesIO(result)).convert("RGBA"))
    except Exception:
        return None

    return None


def build_query_image_variants(image):
    variants = [("original", image.convert("RGB"))]
    background_removed = remove_background(image)

    if background_removed is not None:
        variants.append(("background-removed", background_removed))

    return variants
