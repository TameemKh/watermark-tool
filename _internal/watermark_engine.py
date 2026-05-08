import math
import fitz  # PyMuPDF


def calculate_rotation(width, height):
    angle_rad = math.atan(height / width)
    return math.degrees(angle_rad)


def calculate_font_size(width, height):
    diagonal = math.sqrt(width**2 + height**2)
    return diagonal / 18


def insert_watermark(page, page_index, config):

    rect = page.rect
    w, h = rect.width, rect.height

    wm_type       = config["watermark_type"]   # text | image | text_img
    mode          = config["mode"]             # corners | adaptive_diagonal | full_single
    opacity       = config["opacity"]
    wm_text       = config.get("watermark_text", "IVR TEAM")
    wm_image      = config.get("watermark_image", None)
    step_x        = config.get("step_x", 180)
    step_y        = config.get("step_y", 120)

    rotation  = calculate_rotation(w, h)
    font_size = calculate_font_size(w, h)
    matrix    = fitz.Matrix(1, 1).prerotate(rotation)

    # ── helpers ──────────────────────────────────────────────

    def draw_text(p, fs, morph_matrix=None):
        page.insert_text(
            p,
            wm_text,
            fontsize=fs,
            color=(1, 0, 0),
            fill_opacity=opacity,
            morph=(fitz.Point(*p), morph_matrix) if morph_matrix else None,
        )

    def draw_image(r):
        if wm_image:
            page.insert_image(r, filename=wm_image, overlay=True)

    # ── CORNERS ──────────────────────────────────────────────
    if mode == "corners":

        points = [
            (w - 150, h - 120),   # أسفل يمين
        ]

        for i, p in enumerate(points):
            if wm_type == "text":
                draw_text(p, font_size / 2)
            elif wm_type == "image":
                draw_image(fitz.Rect(p[0], p[1], p[0] + 120, p[1] + 120))
            elif wm_type == "text_img":
                if i % 2 == 0:
                    draw_text(p, font_size / 3)
                else:
                    draw_image(fitz.Rect(p[0], p[1], p[0] + 120, p[1] + 120))

    # ── ADAPTIVE DIAGONAL ────────────────────────────────────
    elif mode == "adaptive_diagonal":

        x      = 0
        toggle = True

        while x < w:
            y = 0
            while y < h:
                if wm_type == "text":
                    draw_text((x, y), font_size, matrix)
                elif wm_type == "image":
                    size = font_size * 3
                    draw_image(fitz.Rect(x, y, x + size, y + size))
                elif wm_type == "text_img":
                    size = font_size * 3
                    if toggle:
                        draw_image(fitz.Rect(x, y, x + size, y + size))
                    else:
                        draw_text((x, y), font_size, matrix)
                    toggle = not toggle
                y += step_y
            x += step_x

    # ── FULL SINGLE ──────────────────────────────────────────
    elif mode == "full_single":

        diagonal  = math.sqrt(w**2 + h**2)
        font_size = diagonal / (len(wm_text) * 0.6)
        start_pt  = (font_size / 2, h)

        if wm_type == "text":
            draw_text(start_pt, font_size * 0.85, matrix)

        elif wm_type == "image":
            draw_image(
                fitz.Rect(
                    start_pt[0],
                    start_pt[1] - diagonal,
                    start_pt[0] + diagonal,
                    start_pt[1],
                )
            )

        elif wm_type == "text_img":
            if page_index % 2 == 0:
                draw_text(start_pt, font_size, matrix)
            else:
                draw_image(
                    fitz.Rect(
                        start_pt[0],
                        start_pt[1] - diagonal,
                        start_pt[0] + diagonal,
                        start_pt[1],
                    )
                )


# ─────────────────────────────────────────────────────────────
#  الدالة الرئيسية: تستقبل bytes وترجع bytes
# ─────────────────────────────────────────────────────────────

def process_pdf_bytes(pdf_bytes: bytes, config: dict, exclude_pages: list = None) -> bytes:
    """
    pdf_bytes     : محتوى ملف PDF كـ bytes
    config        : dict يحتوي إعدادات العلامة
    exclude_pages : قائمة أرقام الصفحات المستثناة (index يبدأ من 0)
    returns       : PDF مُعالَج كـ bytes
    """
    if exclude_pages is None:
        exclude_pages = []

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for i, page in enumerate(doc):
        if i in exclude_pages:
            continue
        insert_watermark(page, i, config)

    result = doc.tobytes(garbage=0, deflate=False)
    doc.close()
    return result
