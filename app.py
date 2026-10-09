import base64
from io import BytesIO

import requests
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="مترجم المانهوا",
    page_icon="📚",
    layout="centered"
)

# --- تحسين التمرير بالماوس وإلغاء قيود الحاوية ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        overflow-y: auto !important;
        scroll-behavior: smooth !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 800px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
""", unsafe_allow_html=True)

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

            # تصغير أبعاد الصورة لسرعة الأداء
            max_size = (800, 800)
            image_resized = image.copy()
            image_resized.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffer = BytesIO()
            image_resized.save(buffer, format="JPEG", quality=75)
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

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
                    timeout=60,
                )

            if response.ok:
                result = response.json()
                translation = ""

                # 1. الاستخراج من steps (طريقة Interactions API)
                if "steps" in result and isinstance(result["steps"], list):
                    for step in result["steps"]:
                        if step.get("type") == "model_output" and "content" in step:
                            for content_item in step["content"]:
                                if content_item.get("type") == "text" and "text" in content_item:
                                    translation += content_item["text"] + "\n"

                # 2. الاستخراج المباشر
                if not translation and "output_text" in result and result["output_text"]:
                    translation = result["output_text"]

                # 3. الاستخراج الاحتياطي من candidates
                if not translation and "candidates" in result and len(result["candidates"]) > 0:
                    try:
                        parts = result["candidates"][0]["content"]["parts"]
                        translation = "".join([p.get("text", "") for p in parts])
                    except (KeyError, IndexError):
                        pass

                if translation.strip():
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
                    st.json(result)
            else:
                st.error(f"تعذر إكمال الترجمة (رمز الحالة: {response.status_code}).")
                st.code(response.text)

    except KeyError:
        st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
    except Exception as error:
        st.error("حدث خطأ أثناء معالجة الصورة.")
        st.caption(str(error))
