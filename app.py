import base64
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

import requests
import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="مترجم المانهوا",
    page_icon="📚",
    layout="centered"
)

# --- تحسين التمرير بالماوس وتنسيق البطاقات ---
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        overflow-y: auto !important;
        scroll-behavior: smooth !important;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    .manhwa-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 25px;
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

st.title("📚 مترجم المانهوا المتعدد")
st.write("ارفع صورة أو عدة صور مانهوا لترجمتها جميعاً في نفس الوقت بأسلوب متوازٍ وسريع.")

uploaded_files = st.file_uploader(
    "اختر صورة أو عدة صور",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)


def process_single_image(file_obj, api_key):
    """دالة معالجة وترجمة صورة واحدة"""
    try:
        image = Image.open(file_obj).convert("RGB")
        
        # تصغير سريع جداً لتقليل زمن النقل
        max_size = (800, 800)
        image_resized = image.copy()
        image_resized.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        image_resized.save(buffer, format="JPEG", quality=70)
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
                {"type": "text", "text": prompt_text},
                {"type": "image", "mime_type": "image/jpeg", "data": image_data},
            ],
        }

        translation = ""
        last_error = ""

        # محاولة الطلب حتى مرتين للتعامل مع الضغط اللحظي 503
        for attempt in range(2):
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.ok:
                result = response.json()
                
                # 1. الاستخراج من steps
                if "steps" in result and isinstance(result["steps"], list):
                    for step in result["steps"]:
                        if step.get("type") == "model_output" and "content" in step:
                            for content_item in step["content"]:
                                if content_item.get("type") == "text" and "text" in content_item:
                                    translation += content_item["text"] + "\n"

                # 2. الاستخراج المباشر
                if not translation and "output_text" in result and result["output_text"]:
                    translation = result["output_text"]

                # 3. الاستخراج من candidates
                if not translation and "candidates" in result and len(result["candidates"]) > 0:
                    try:
                        parts = result["candidates"][0]["content"]["parts"]
                        translation = "".join([p.get("text", "") for p in parts])
                    except (KeyError, IndexError):
                        pass

                if translation.strip():
                    return True, image, translation.strip(), file_obj.name
            elif response.status_code in [503, 429]:
                time.sleep(1.5)
            else:
                last_error = f"رمز الحالة: {response.status_code}"
                break

        return False, image, f"تعذر الترجمة: {last_error}", file_obj.name

    except Exception as e:
        return False, None, f"خطأ في المعالجة: {str(e)}", file_obj.name


if uploaded_files:
    st.info(f"تم رفع {len(uploaded_files)} صورة/صور.")

    if st.button("🌐 ترجمة جميع الصور الآن", type="primary"):
        try:
            api_key = st.secrets["GEMINI_API_KEY"]

            with st.spinner(f"🚀 يجري ترجمة {len(uploaded_files)} صورة بشكل متوازٍ وسريع..."):
                # استخدام ThreadPoolExecutor للاتصال المتوازي مع API
                with ThreadPoolExecutor(max_workers=len(uploaded_files)) as executor:
                    futures = [
                        executor.submit(process_single_image, file_item, api_key)
                        for file_item in uploaded_files
                    ]
                    results = [f.result() for f in futures]

            st.success("✨ اكتملت الترجمة!")

            full_combined_translation = ""

            for idx, (success, img, text_result, filename) in enumerate(results, start=1):
                st.markdown("---")
                st.subheader(f"📄 الصفحات ({idx}/{len(results)}): {filename}")

                col1, col2 = st.columns([1, 1])

                with col1:
                    if img:
                        st.image(img, caption=filename, use_container_width=True)

                with col2:
                    if success:
                        st.markdown("**📝 الترجمة:**")
                        st.markdown(text_result)
                        full_combined_translation += f"=== الصفحة {idx}: {filename} ===\n{text_result}\n\n"

                        st.download_button(
                            f"⬇️ تنزيل ترجمة هذه الصفحة",
                            data=text_result,
                            file_name=f"translation_page_{idx}.txt",
                            mime="text/plain",
                            key=f"dl_{idx}"
                        )
                    else:
                        st.error(text_result)

            if full_combined_translation:
                st.markdown("---")
                st.download_button(
                    "📦 تنزيل جميع الترجمات في ملف واحد",
                    data=full_combined_translation,
                    file_name="all_manhwa_translations.txt",
                    mime="text/plain",
                    type="primary"
                )

        except KeyError:
            st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
        except Exception as error:
            st.error("حدث خطأ غير متوقع.")
            st.caption(str(error))
