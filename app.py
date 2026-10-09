import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(
    page_title="مترجم المانهوا",
    page_icon="📚",
    layout="centered"
)

st.title("📚 مترجم المانهوا")
st.write("ارفع صورة المانهوا لترجمة فقاعات الكلام إلى العربية.")

uploaded_file = st.file_uploader(
    "اختر صورة المانهوا",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="صورة المانهوا", use_container_width=True)

    if st.button("🌐 ترجمة الصورة", type="primary"):
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=90)
            image_base64 = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")
        url = "https://generativelanguage.googleapis.com/v1beta/interactions"

headers = {
    "x-goog-api-key": api_key,
    "Content-Type": "application/json"
}

payload = {
    "model": "gemini-3.8-flash",
    "store": False,
    "input": [
        {
            "type": "text",
            "text": (
                "اقرأ النصوص المطبوعة في فقاعات المانهوا، "
                "ثم ترجم كل حوار إلى العربية الفصحى. "
                "رتب الحوارات حسب ظهورها، ولا تخمّن "
                "النصوص غير الواضحة."
            )
        },
        {
            "type": "image",
            "mime_type": "image/jpeg",
            "data": image_base64
        }
    ]
}

with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

if response.ok:
    data = response.json()
    translation = data.get("output_text", "")

    if not translation:
        for item in data.get("outputs", []):
            for part in item.get("content", []):
                if part.get("type") == "text":
                    translation += part.get("text", "")

    if translation:
        st.subheader("📝 الترجمة العربية")
        st.markdown(translation)

        st.download_button(
            "⬇️ تنزيل الترجمة",
            data=translation,
            file_name="manhwa_translation.txt",
            mime="text/plain"
        )
    else:
        st.error("لم يُرجع النموذج نصًا مترجمًا.")
else:
    st.error(f"تعذر إكمال الترجمة ({response.status_code}).")
    st.caption(response.text[:800])

        except KeyError:
            st.error(
                "لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets."
            )
        except Exception as error:
            st.error("حدث خطأ أثناء معالجة الصورة.")
            st.caption(str(error))
