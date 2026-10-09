import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

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
            api_key = st.secrets.get("GEMINI_API_KEY")

            if not api_key:
                st.error("لم يتم العثور على GEMINI_API_KEY في إعدادات Secrets.")
            else:
                # إنشاء العميل باستخدام المكتبة الرسمية
                client = genai.Client(api_key=api_key)

                prompt_text = (
                    "أنت مساعد لترجمة المانهوا. اقرأ النصوص "
                    "المطبوعة داخل فقاعات الكلام في الصورة. "
                    "رتبها بحسب ترتيب القراءة الظاهر. "
                    "ترجم كل فقاعة إلى العربية الفصحى بأسلوب "
                    "طبيعي، وضع كل فقاعة في سطر مستقل. "
                    "لا تخمّن الكلمات غير الواضحة، بل اذكر "
                    "أن النص غير واضح. لا تضف حوارًا غير موجود."
                )

                with st.spinner("🤖 يجري تحليل الصورة وترجمتها..."):
                    # استخدام النموذج الأحدث gemini-2.5-flash
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[image, prompt_text]
                    )

                translation = response.text

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
                    st.error("وصل الرد، لكن لم أجد نص الترجمة فيه.")

    except Exception as error:
        st.error("حدث خطأ أثناء معالجة الصورة.")
        st.caption(str(error))
