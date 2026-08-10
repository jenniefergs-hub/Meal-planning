import io

from PIL import Image, ImageOps

MAX_DIMENSION = 1200
JPEG_QUALITY = 82


def process_recipe_image(image_bytes: bytes):
    """Normalize an uploaded photo to a reasonably sized JPEG for storage.

    Applies EXIF orientation (phone photos often store rotation as
    metadata rather than rotating the actual pixels) and caps the longest
    side so a multi-megabyte phone photo doesn't bloat the database.
    Returns (processed_bytes, content_type).
    """
    img = Image.open(io.BytesIO(image_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue(), "image/jpeg"
