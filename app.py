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

            url = (
                "https://generativelanguage.googleapis.com/"
                "v1beta/models/gemini-2.5-flash:generateContent"
            )

            payload = {
                "contents": [{
                    "parts": [
                        {
                            "text": (
                                "حلل صورة المانهوا واقرأ النصوص المطبوعة "
                                "داخل فقاعات الكلام والمؤثرات النصية. "
                                "رتب الحوارات حسب ترتيب القراءة المناسب. "
                                "ترجمها إلى العربية الفصحى بأسلوب طبيعي "
                                "يحافظ على المعنى والشخصيات. "
                                "اعرض كل نص في سطر منفصل مع رقم، "
                                "ثم ترجمته العربية. لا تخمّن النص "
                                "غير المقروء؛ اذكر أنه غير واضح."
                            )
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "maxOutputTokens": 2048,
                    "temperature": 0.2
                }
            }

            with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                response = requests.post(
                    url,
                    params={"key": api_key},
                    json=payload,
                    timeout=120
                )

            if response.ok:
                data = response.json()
                parts = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [])
                )
                translation = "\n".join(
                    part["text"]
                    for part in parts
                    if "text" in part
                )

                if translation:
                    st.subheader("📝 الترجمة العربية")
                    st.markdown(translation)
                    st.download_button(
                        "⬇️ تنزيل الترجمة النصية",
                        data=translation,
                        file_name="manhwa_translation.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(
                        "لم يُرجع النموذج ترجمة نصية. "
                        "جرّب صورة أخرى."
                    )
            else:
                st.error(
                    f"تعذر إكمال الترجمة ({response.status_code})."
                )
                st.caption(response.text[:800])

        except KeyError:
            st.error(
                "لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets."
            )
        except Exception as error:
            st.error("حدث خطأ أثناء معالجة الصورة.")
            st.caption(str(error))
