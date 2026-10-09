
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="مترجم المانهوا",
    page_icon="📖",
    layout="centered"
)

st.title("📖 مترجم المانهوا")
st.write("ارفع صورة المانهوا للبدء في تجهيزها للترجمة إلى العربية.")

uploaded_file = st.file_uploader(
    "اختر صورة المانهوا",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.image(
        image,
        caption="الصورة المرفوعة",
        use_container_width=True
    )

    st.success("تم رفع الصورة بنجاح!")

    st.info(
        "المرحلة التالية: إضافة الذكاء الاصطناعي "
        "لاستخراج النصوص وترجمتها إلى العربية."
    )

    if st.button("بدء الترجمة"):
        st.warning(
            "محرك استخراج النصوص والترجمة لم يُربط بعد. "
            "سنضيفه في الخطوة التالية."
        )
