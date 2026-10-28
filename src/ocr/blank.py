from pathlib import Path

from PIL import Image, ImageChops

MIN_INK_AREA = 400
# A blank sheet keeps dust and show-through under a thousandth of its area (measured
# 5k dark pixels on a 17.4M-pixel scan); one line of type carries far more.
BLANK_INK_RATIO = 0.001
# Ink differs from the paper tone by this much, so toned stock is not ink and a cover's
# light type on a dark ground still is.
INK_CONTRAST = 60
BLANK_TRANSCRIPT = "<!-- blank page -->\n"


def paper_level(band: Image.Image) -> int:
    """The median of one band, which is the paper tone because type covers far less than half."""
    hist = band.histogram()
    half = sum(hist) / 2
    seen = 0
    for level, count in enumerate(hist):
        seen += count
        if seen >= half:
            return level
    return 255


def ink_mask(img: Image.Image) -> Image.Image:
    """255 where any color band differs from that band's paper tone by more than `INK_CONTRAST`."""
    masks = [_band_ink(band) for band in img.convert("RGB").split()]
    return ImageChops.lighter(ImageChops.lighter(masks[0], masks[1]), masks[2])


def _band_ink(band: Image.Image) -> Image.Image:
    paper = paper_level(band)
    return band.point(lambda p: 255 if abs(p - paper) > INK_CONTRAST else 0)


def crop_and_measure_ink(
    img: Image.Image, padding: int = 24
) -> tuple[Image.Image, int]:
    """Remove outer paper margins and return (cropped_image, ink pixel count).

    The count is ink, not the bounding box: dust specks in two corners make a blank
    page's box span the sheet, and a blank page sent to the model comes back invented.
    """
    bw = ink_mask(img)
    bbox = bw.getbbox()
    if not bbox:
        return img, 0
    ink_pixels = bw.histogram()[255]
    w, h = img.size
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(w, bbox[2] + padding)
    bottom = min(h, bbox[3] + padding)
    return img.crop((left, top, right, bottom)), ink_pixels


def blank_page_threshold(img: Image.Image) -> int:
    """Dark pixels below which a scan holds no text to transcribe."""
    return max(MIN_INK_AREA, int(img.width * img.height * BLANK_INK_RATIO))


def is_blank_page(path: Path) -> bool:
    with Image.open(path) as raw:
        image = raw.convert("RGB")
    _, ink = crop_and_measure_ink(image)
    return ink < blank_page_threshold(image)
