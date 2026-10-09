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

            # تجهيز الصورة وتحويلها إلى Base64
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # قائمة النماذج لتجربتها بالترتيب عند وجود ضغط على السيرفر
            models_to_try = [
                "gemini-3.8-flash",
                "gemini-2.5-flash",
                "gemini-2.0-flash"
            ]

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

            translation = ""
            success = False
            last_error_msg = ""

            with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                for model_name in models_to_try:
                    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
                    
                    payload = {
                        "model": model_name,
                        "store": False,
                        "input": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image", "mime_type": "image/jpeg", "data": image_data},
                        ],
                    }

                    # محاولة الطلب حتى مرتين للنموذج الواحد عند حدوث 503
                    for attempt in range(2):
                        response = requests.post(
                            url,
                            headers=headers,
                            json=payload,
                            timeout=120,
                        )

                        if response.ok:
                            result = response.json()
                            
                            # 1. الاستخراج من Interactions API
                            if "output_text" in result and result["output_text"]:
                                translation = result["output_text"]
                            elif "outputs" in result and len(result["outputs"]) > 0:
                                first_output = result["outputs"][0]
                                if isinstance(first_output, dict):
                                    translation = first_output.get("text", "") or first_output.get("content", "")
                            
                            if translation:
                                success = True
                                break

                        elif response.status_code == 503:
                            # ضغط على السيرفر - ننتظر ثانية ونعيد المحاولة أو ننتقل للنموذج التالي
                            time.sleep(1.5)
                            continue
                        else:
                            last_error_msg = f"({response.status_code}) {response.text[:200]}"
                            break

                    if success:
                        break

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
                if last_error_msg:
                    st.error(f"تعذر إكمال الترجمة: {last_error_msg}")
                else:
                    st.error("جميع خوادم الذكاء الاصطناعي مشغولة حالياً بسبب الضغط العالي. يرجى الانتظار بضع ثوانٍ والإعادة.")

    except KeyError:
        st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
    except Exception as error:
        st.error("حدث خطأ أثناء معالجة الصورة.")
        st.caption(str(error))
