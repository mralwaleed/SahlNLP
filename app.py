"""
SahlNLP Live Showcase — Streamlit Web Demo
Zero-dependency Arabic NLP toolkit: https://github.com/mralwaleed/SahlNLP
"""

import time

import sahlnlp
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SahlNLP: High-Speed Arabic NLP",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("⚡ SahlNLP")
st.sidebar.caption(f"v{sahlnlp.__version__} — Zero-dependency Arabic NLP")
page = st.sidebar.radio(
    "Navigate",
    ["Home", "Text Cleaner", "Dialect Radar", "PII Masking (Guardian)", "Tafkeet"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.markdown(
    "[GitHub](https://github.com/mralwaleed/SahlNLP) &nbsp;·&nbsp; "
    "[PyPI](https://pypi.org/project/sahlnlp/)"
)


def timed(func, *args, **kwargs):
    """Run *func* and return (result, elapsed_ms)."""
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = (time.perf_counter() - t0) * 1000
    return result, elapsed


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
if page == "Home":
    st.title("⚡ SahlNLP")
    st.subheader("High-Speed Arabic NLP Toolkit")
    st.markdown(
        """
        A **zero-dependency**, ultra-fast Python toolkit for Arabic text
        preprocessing, normalization, and advanced analysis.

        **Modules:**

        | Module | Description |
        |---|---|
        | 🧹 **Text Cleaner** | Remove Tashkeel, Tatweel, HTML/links, repeated chars |
        | 📡 **Dialect Radar** | Detect Gulf, Levantine, Egyptian, Maghrebi |
        | 🛡️ **Guardian** | Mask or tag PII (phones, IDs, IBANs, emails, names) |
        | 🔢 **Tafkeet** | Convert numbers to Arabic words with full grammar |

        Pick a module from the sidebar to try it live.
        """
    )

# ---------------------------------------------------------------------------
# Text Cleaner
# ---------------------------------------------------------------------------
elif page == "Text Cleaner":
    st.header("🧹 Text Cleaner")
    st.caption("Remove noise from Arabic text — Tashkeel, Tatweel, HTML, and more.")

    sample_clean = "السَّلامُ عَلَيْكُمْ ورحمة الله وبركاتهُ تفـاصيل الموضـوع تجدونها في <b>المقال</b>"
    text = st.text_area("Input Arabic text", value=sample_clean, height=150)

    col1, col2 = st.columns(2)
    with col1:
        do_tashkeel = st.checkbox("Remove Tashkeel", value=True)
        do_tatweel = st.checkbox("Remove Tatweel", value=True)
    with col2:
        do_html = st.checkbox("Remove HTML & Links", value=True)
        do_repeated = st.checkbox("Remove Repeated Chars", value=True)

    if st.button("Clean", type="primary") and text.strip():
        result, ms = timed(
            sahlnlp.clean_all,
            text,
            remove_tashkeel_flag=do_tashkeel,
            remove_tatweel_flag=do_tatweel,
            remove_html_flag=do_html,
            remove_repeated_flag=do_repeated,
        )
        st.success(result)
        st.caption(f"Executed in **{ms:.4f} ms**")

# ---------------------------------------------------------------------------
# Dialect Radar
# ---------------------------------------------------------------------------
elif page == "Dialect Radar":
    st.header("📡 Dialect Radar")
    st.caption("Detect the Arabic dialect in real-time with confidence scores.")

    sample_dialect = "شلونك يا خوي، وش أخبارك؟ الحمد لله اليوم زين"
    text = st.text_area("Input Arabic text", value=sample_dialect, height=120)

    if st.button("Detect Dialect", type="primary") and text.strip():
        result, ms = timed(sahlnlp.detect_dialect, text)

        # Sort by score descending
        sorted_dialects = sorted(result.items(), key=lambda x: x[1], reverse=True)
        top_dialect, top_score = sorted_dialects[0]

        # Confidence badge
        st.metric("Detected Dialect", top_dialect, f"{top_score:.0%}")

        # Bar chart for all dialects
        labels = [d for d, _ in sorted_dialects]
        scores = [s for _, s in sorted_dialects]
        chart_data = {"Dialect": labels, "Confidence": scores}
        st.bar_chart(chart_data, x="Dialect", y="Confidence", horizontal=True)

        # Detail table
        st.dataframe(
            [{"Dialect": d, "Confidence": f"{s:.2%}"} for d, s in sorted_dialects],
            hide_index=True,
            use_container_width=True,
        )
        st.caption(f"Executed in **{ms:.4f} ms**")

# ---------------------------------------------------------------------------
# PII Masking (Guardian)
# ---------------------------------------------------------------------------
elif page == "PII Masking (Guardian)":
    st.header("🛡️ PII Masking (Guardian)")
    st.caption("Detect and redact sensitive information — phones, IDs, IBANs, emails, names.")

    sample_guardian = (
        "العميل محمد الأحمد اتصل على 0551234567 وحوالة على IBAN SA0380000000608010167519"
    )
    text = st.text_area("Input Arabic text", value=sample_guardian, height=130)

    mode = st.radio("Redaction Mode", ["Tag", "Mask"], horizontal=True)
    mask_char = None
    if mode == "Mask":
        mask_char = st.text_input("Mask character", value="*", max_chars=1)

    if st.button("Protect", type="primary") and text.strip():
        kwargs = {"mode": mode.lower()}
        if mask_char:
            kwargs["mask_char"] = mask_char
        result, ms = timed(sahlnlp.mask_sensitive_info, text, **kwargs)

        col_before, col_after = st.columns(2)
        with col_before:
            st.subheader("Original")
            st.info(text)
        with col_after:
            st.subheader("Protected")
            st.success(result)

        st.caption(f"Executed in **{ms:.4f} ms**")

# ---------------------------------------------------------------------------
# Tafkeet (Number → Arabic Words)
# ---------------------------------------------------------------------------
elif page == "Tafkeet":
    st.header("🔢 Tafkeet — Number to Arabic Words")
    st.caption("Convert numbers to fully inflected Arabic words with grammatical case (إعراب).")

    number = st.number_input("Enter a number", value=150, step=1, min_value=0)

    col_case, col_curr = st.columns(2)
    with col_case:
        case_label = st.radio(
            "Grammatical Case (الإعراب)",
            ["رفع (Nominative)", "نصب (Accusative)", "جر (Genitive)"],
            horizontal=True,
        )
        _CASE_MAP = {
            "رفع (Nominative)": "nominative",
            "نصب (Accusative)": "accusative",
            "جر (Genitive)": "genitive",
        }
        case = _CASE_MAP[case_label]
    with col_curr:
        use_sar = st.toggle("Currency Mode (SAR)", value=False)

    if st.button("Convert", type="primary"):
        kwargs = {"case": case}
        if use_sar:
            kwargs["currency"] = "SAR"
        result, ms = timed(sahlnlp.tafkeet, int(number), **kwargs)
        st.success(result)
        if use_sar:
            st.caption(f"with SAR currency · Executed in **{ms:.4f} ms**")
        else:
            st.caption(f"Executed in **{ms:.4f} ms**")
