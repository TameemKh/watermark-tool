import io
import os
import zipfile

import streamlit as st

from watermark_engine import process_pdf_bytes

# ─────────────────────────────────────────────────────────────
#  ⚙️  إعداد واحد فقط يحتاج تعديل: مسار ملف اللوجو
#  ضع ملف اللوجو بجانب هذا الملف واسمه logo.png
#  أو عدّل المسار أدناه مرة واحدة
# ─────────────────────────────────────────────────────────────
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")
# ─────────────────────────────────────────────────────────────


# ── إعداد الصفحة ─────────────────────────────────────────────
st.set_page_config(
    page_title="IVR Watermark Tool",
    page_icon="🔏",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS بسيط لتحسين الشكل ─────────────────────────────────────
st.markdown("""
<style>
    .main { max-width: 750px; }
    div[data-testid="stRadio"] > label { font-size: 15px; }
    .stButton > button { border-radius: 10px; font-size: 16px; padding: 0.6em 1em; }
</style>
""", unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=70)
with col_title:
    st.markdown("## 🔏 IVR Watermark Tool")
    st.caption("أداة وضع العلامة المائية — فريق IVR")

st.divider()


# ── رفع الملفات ──────────────────────────────────────────────
st.markdown("### 📂 ارفع ملفات PDF")
uploaded_files = st.file_uploader(
    label="يمكنك رفع أكثر من ملف في نفس الوقت",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="visible",
)

if uploaded_files:
    st.success(f"✅ تم رفع **{len(uploaded_files)}** ملف")

st.divider()


# ── الإعدادات ────────────────────────────────────────────────
st.markdown("### ⚙️ إعدادات العلامة المائية")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**نوع العلامة**")
    wm_type = st.radio(
        label="wm_type",
        options=["image", "text", "text_img"],
        format_func=lambda x: {
            "image":    "🖼️  صورة  (اللوجو)",
            "text":     "✏️  نص فقط",
            "text_img": "🔀  نص + صورة",
        }[x],
        label_visibility="collapsed",
    )

with col2:
    st.markdown("**وضعية العلامة**")
    mode = st.radio(
        label="mode",
        options=["corners", "adaptive_diagonal", "full_single"],
        format_func=lambda x: {
            "corners":           "📐  زاوية  (أسفل يمين)",
            "adaptive_diagonal": "↗️  قطري متكرر",
            "full_single":       "🔲  كامل الصفحة",
        }[x],
        label_visibility="collapsed",
    )

st.markdown(" ")

# ── نص العلامة (يظهر فقط إذا اختار text أو text_img) ──────────
watermark_text = "IVR TEAM"
if wm_type in ["text", "text_img"]:
    watermark_text = st.text_input(
        "نص العلامة المائية",
        value="IVR TEAM",
        max_chars=40,
    )

# ── الشفافية ────────────────────────────────────────────────
opacity_pct = st.slider(
    "الشفافية  (كلما زادت كانت العلامة أوضح)",
    min_value=1,
    max_value=100,
    value=10,
    format="%d%%",
)
opacity = opacity_pct / 100

# ── صفحات مستثناة ───────────────────────────────────────────
exclude_input = st.text_input(
    "صفحات مستثناة  (أرقام مفصولة بفاصلة — مثال: 1, 2, 5)",
    value="",
    placeholder="اتركه فارغاً إذا لا تريد استثناء أي صفحة",
)

exclude_pages = []
if exclude_input.strip():
    try:
        raw = [x.strip() for x in exclude_input.split(",") if x.strip()]
        exclude_pages = [int(n) - 1 for n in raw if n.isdigit()]
        st.caption(f"سيتم تخطي الصفحات: {[x+1 for x in exclude_pages]}")
    except Exception:
        st.warning("⚠️ تأكد من إدخال أرقام صحيحة مفصولة بفاصلة")

st.divider()


# ── زر التشغيل ───────────────────────────────────────────────
run_btn = st.button("🚀  تطبيق العلامة المائية", use_container_width=True, type="primary")

if run_btn:

    if not uploaded_files:
        st.error("❗ الرجاء رفع ملف PDF واحد على الأقل")

    elif wm_type in ["image", "text_img"] and not os.path.exists(LOGO_PATH):
        st.error(
            f"❗ ملف اللوجو غير موجود في المسار:\n`{LOGO_PATH}`\n\n"
            "ضع ملف اللوجو بجانب `app.py` باسم `logo.png` ثم حاول مجدداً."
        )

    else:
        config = {
            "watermark_type": wm_type,
            "mode":           mode,
            "opacity":        opacity,
            "watermark_text": watermark_text,
            "watermark_image": LOGO_PATH if os.path.exists(LOGO_PATH) else None,
            "step_x":         180,
            "step_y":         120,
        }

        results = {}
        errors  = []

        progress_bar = st.progress(0, text="جاري المعالجة...")

        for idx, file in enumerate(uploaded_files):
            try:
                pdf_bytes    = file.read()
                watermarked  = process_pdf_bytes(pdf_bytes, config, exclude_pages)
                results[file.name] = watermarked
            except Exception as e:
                errors.append((file.name, str(e)))

            progress_bar.progress(
                (idx + 1) / len(uploaded_files),
                text=f"جاري المعالجة... {idx + 1} / {len(uploaded_files)}",
            )

        progress_bar.empty()

        # ── نتائج الأخطاء ────────────────────────────────────
        if errors:
            for name, err in errors:
                st.error(f"❌ **{name}** — {err}")

        # ── تحميل النتائج ────────────────────────────────────
        if results:
            st.success(f"✅ تمت معالجة **{len(results)}** ملف بنجاح!")

            if len(results) == 1:
                # ملف واحد → زر تحميل مباشر
                name, data = list(results.items())[0]
                st.download_button(
                    label=f"⬇️  تحميل  {name}",
                    data=data,
                    file_name=name,
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                # أكثر من ملف → ZIP
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for name, data in results.items():
                        zf.writestr(name, data)
                zip_buffer.seek(0)

                st.download_button(
                    label=f"⬇️  تحميل الكل ({len(results)} ملفات) — ZIP",
                    data=zip_buffer,
                    file_name="IVR_watermarked.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

st.divider()
st.caption("IVR Engineering Society  •  Watermark Tool v1.0")
