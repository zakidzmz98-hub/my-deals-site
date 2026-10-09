
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="مترجم المانهوا",
    page_icon="📖",
    layout="centered"
)

st.title("📖 مترجم المانهوا")
st.write("ارفع صورة مانهوا لنبدأ ترجمتها إلى العربية.")

uploaded_file = st.file_uploader(
    "اختر صورة المانهوا",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="الصورة الأصلية", use_container_width=True)

    st.success("تم تحميل الصورة بنجاح!")

    st.subheader("النص المستخرج")
    st.info("سيظهر النص هنا بعد إضافة نظام التعرّف على الحروف.")

    st.subheader("الترجمة العربية")
    st.info("ستظهر الترجمة هنا في المرحلة التالية.")
