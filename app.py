import base64
import time
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

            # --- ضغط وتقليل أبعاد الصورة لضمان السرعة وتفادي الـ Timeout ---
            max_size = (1024, 1024)
            image_resized = image.copy()
            image_resized.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffer = BytesIO()
            image_resized.save(buffer, format="JPEG", quality=75)
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

            translation = ""
            success = False

            with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                
                # --- المسار الأول: Interactions API مع timeout مناسب ---
                interactions_url = "https://generativelanguage.googleapis.com/v1beta/interactions"
                interactions_headers = {
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                }
                interactions_payload = {
                    "model": "gemini-3.8-flash",
                    "store": False,
                    "input": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image", "mime_type": "image/jpeg", "data": image_data},
                    ],
                }

                try:
                    res = requests.post(
                        interactions_url,
                        headers=interactions_headers,
                        json=interactions_payload,
                        timeout=45
                    )
                    if res.ok:
                        result = res.json()
                        if "output_text" in result and result["output_text"]:
                            translation = result["output_text"]
                            success = True
                        elif "outputs" in result and len(result["outputs"]) > 0:
                            first_out = result["outputs"][0]
                            if isinstance(first_out, dict):
                                translation = first_out.get("text", "") or first_out.get("content", "")
                                if translation:
                                    success = True
                except (requests.exceptions.Timeout, requests.exceptions.RequestException):
                    pass

                # --- المسار الاحتياطي: REST API التقليدي في حال الانتهاء أو التأخير ---
                if not success:
                    fallback_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    fallback_headers = {"Content-Type": "application/json"}
                    fallback_payload = {
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

                    try:
                        res_fb = requests.post(
                            fallback_url,
                            headers=fallback_headers,
                            json=fallback_payload,
                            timeout=45
                        )
                        if res_fb.ok:
                            fb_data = res_fb.json()
                            if "candidates" in fb_data and len(fb_data["candidates"]) > 0:
                                parts = fb_data["candidates"][0]["content"]["parts"]
                                translation = "".join([p.get("text", "") for p in parts])
                                if translation:
                                    success = True
                    except Exception:
                        pass

            if success and translation:
                st.subheader("📝 الترجمة العربية")
                st.markdown(translation)

                st.download_button(
                    "⬇️ تنزيل الترجمة",
                    data=translation,
                    file_name="manhwa_translation.txt",
                    mime="text/plain",
                )
            else:
                st.error("استغرق الخادم وقتاً طويلاً في المعالجة. يرجى تجربة إعادة الضغط أو رفع صورة بحجم أصغر.")

    except KeyError:
        st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
    except Exception as error:
        st.error("حدث خطأ أثناء معالجة الصورة.")
        st.caption(str(error))
