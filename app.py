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

            # تجهيز الصورة وترميزها بـ Base64
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

            # قائمة النماذج المتاحة بالترتيب (إذا كان الأول مشغولاً يتم الانتقال للثاني)
            models_to_try = [
                "gemini-1.5-flash",
                "gemini-2.5-flash",
                "gemini-1.5-pro"
            ]

            headers = {
                "Content-Type": "application/json"
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

            translation = ""
            success = False

            with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                for model_name in models_to_try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                    
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=120
                    )

                    if response.ok:
                        result = response.json()
                        try:
                            translation = result["candidates"][0]["content"]["parts"][0]["text"]
                            success = True
                            break  # تم الحصول على النتيجة بنجاح، نخرج من الحلقة
                        except (KeyError, IndexError):
                            continue
                    elif response.status_code == 503:
                        # في حال وجود ضغط على النموذج الحالي، ننتقل للنموذج التالي
                        continue
                    else:
                        st.warning(f"تنبيه من النموذج {model_name}: {response.status_code}")
                        st.code(response.text[:500])

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
                st.error("جميع خوادم الترجمة مشغولة حالياً لارتفاع الضغط. يرجى المحاولة بعد بضع ثوانٍ.")

    except KeyError:
        st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
    except Exception as error:
        st.error("حدث خطأ أثناء معالجة الصورة.")
        st.caption(str(error))
