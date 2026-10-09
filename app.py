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

            # ضغط أبعاد الصورة
            max_size = (1000, 1000)
            image_resized = image.copy()
            image_resized.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffer = BytesIO()
            image_resized.save(buffer, format="JPEG", quality=80)
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            prompt_text = (
                "أنت مساعد لترجمة المانهوا. اقرأ النصوص "
                "المطبوعة داخل فقاعات الكلام في الصورة. "
                "رتبها بحسب ترتيب القراءة الظاهر. "
                "ترجم كل فقاعة إلى العربية الفصحى بأسلوب "
                "طبيعي، وضع كل فقاعة في سطر مستقل. "
                "لا تخمّن الكلمات غير الواضحة، بل اذكر "
                "أن النص غير واضح. لا تضف حوارًا غير موجود."
            )

            # الرابط المباشر بطلب REST قياسي
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt_text},
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            }

            with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.ok:
                result = response.json()
                try:
                    translation = result["candidates"][0]["content"]["parts"][0]["text"]
                    st.subheader("📝 الترجمة العربية")
                    st.markdown(translation)

                    st.download_button(
                        "⬇️ تنزيل الترجمة",
                        data=translation,
                        file_name="manhwa_translation.txt",
                        mime="text/plain",
                    )
                except (KeyError, IndexError):
                    st.error("تم استلام الاستجابة ولكن لم يتم العثور على نص الترجمة.")
                    st.json(result)
            else:
                st.error(f"حدث خطأ من الخادم (رمز الحالة: {response.status_code})")
                st.code(response.text)

    except KeyError:
        st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
    except Exception as error:
        st.error("حدث خطأ أثناء معالجة الصورة.")
        st.caption(str(error))
