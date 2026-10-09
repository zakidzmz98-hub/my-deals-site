import base64
from io import BytesIO

import requests
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="مترجم المانهوا",
    page_icon="📚"
)

st.title("📚 مترجم المانهوا")
st.write("ارفع صورة مانهوا لاستخراج الحوارات وترجمتها إلى العربية.")

uploaded_file = st.file_uploader(
    "اختر صورة",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="الصورة المختارة", use_container_width=True)

        if st.button("🌐 ترجمة إلى العربية", type="primary"):
            api_key = st.secrets["GEMINI_API_KEY"]

            # تجهيز الصورة وتحويلها إلى Base64
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # رابط Interactions API الجديد
            url = "https://generativelanguage.googleapis.com/v1beta/interactions"

            headers = {
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            }

            prompt_text = (
                "أنت مساعد لترجمة المانهوا. اقرأ النصوص "
                "المطبوعة داخل فقاعات الكلام في الصورة. "
                "رتبها بحسب ترتيب القراءة الظاهر. "
                "ترجم كل فقاعة إلى العربية الفصحى بأسلوب "
                "طبيعي، وضع كل فقاعة في سطر مستقل. "
                "لا تخمّن الكلمات غير الواضحة، بل اذكر "
                "أن النص غير واضح. لا تضف حوارًا غير موجود."
            )

            # الهيكل الصحيح الخاص بـ Interactions API ونموذج gemini-3.8-flash
            payload = {
                "model": "gemini-3.8-flash",
                "store": False,
                "input": [
                    {
                        "type": "text",
                        "text": prompt_text,
                    },
                    {
                        "type": "image",
                        "mime_type": "image/jpeg",
                        "data": image_data,
                    },
                ],
            }

            with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=120,
                )

                if response.ok:
                result = response.json()
                
                # استخراج الترجمة مرونة لدعم كافة إصدارات الـ API
                translation = ""
                
                # 1. التجربة من حقول Interactions API المركبة
                if "output_text" in result and result["output_text"]:
                    translation = result["output_text"]
                elif "outputs" in result and len(result["outputs"]) > 0:
                    first_output = result["outputs"][0]
                    if isinstance(first_output, dict):
                        translation = first_output.get("text", "") or first_output.get("content", "")
                
                # 2. التجربة من هيكل candidates التقليدي الاحتياطي
                elif "candidates" in result and len(result["candidates"]) > 0:
                    try:
                        parts = result["candidates"][0]["content"]["parts"]
                        translation = "".join([part.get("text", "") for part in parts])
                    except (KeyError, IndexError):
                        pass

                if translation:
                    st.subheader("📝 الترجمة العربية")
                    st.markdown(translation)

                    st.download_button(
                        "⬇️ تنزيل الترجمة",
                        data=translation,
                        file_name="manhwa_translation.txt",
                        mime="text/plain",
                    )
                else:
                    st.error("وصل الرد من الذكاء الاصطناعي، لكن لم يتم استخلاص النص منه.")
                    st.write("🔍 **هيكل الرد المحصل من الخادم (debug):**")
                    st.json(result)
