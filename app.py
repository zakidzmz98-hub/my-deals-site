import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="مترجم المانهوا", page_icon="📚")

st.title("📚 مترجم المانهوا")
st.write("ارفع صورة، وسأحاول قراءة فقاعات الكلام وترجمتها إلى العربية.")

uploaded_file = st.file_uploader(
    "اختر صورة المانهوا",
    type=["png", "jpg", "jpeg", "webp"]
)

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="الصورة المختارة", use_container_width=True)

    if st.button("🌐 ترجمة إلى العربية", type="primary"):
        try:
            token = st.secrets["HF_TOKEN"]

            # تجهيز الصورة للإرسال
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=90)
            image_data = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")

            api_url = (
                "https://router.huggingface.co/v1/chat/completions"
            )

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "zai-org/GLM-4.5V:baseten",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "اقرأ النصوص المطبوعة داخل فقاعات "
                                    "الكلام في صورة المانهوا. "
                                    "رتب الحوارات حسب ترتيب القراءة "
                                    "المناسب للصورة. ترجمها إلى العربية "
                                    "الفصحى بأسلوب طبيعي، وحافظ على "
                                    "معنى كل جملة. لا تخترع نصوصًا "
                                    "غير واضحة. اعرض الترجمة فقط، "
                                    "مع ترقيم كل فقاعة، واذكر "
                                    "إذا تعذر قراءة جزء من النص."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        "data:image/jpeg;base64,"
                                        + image_data
                                    )
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1200,
                "stream": False
            }

            with st.spinner("يجري تحليل الصورة وترجمتها..."):
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=120
                )

            if response.ok:
                result = response.json()
                translation = result["choices"][0]["message"]["content"]

                st.subheader("📝 الترجمة العربية")
                st.markdown(translation)
            else:
                st.error(
                    f"تعذر إكمال الترجمة ({response.status_code})."
                )
                st.write(response.text[:1000])

        except KeyError:
            st.error("لم يتم العثور على HF_TOKEN في إعدادات Secrets.")
        except Exception as error:
            st.error("حدث خطأ أثناء الترجمة.")
            st.caption(str(error))
