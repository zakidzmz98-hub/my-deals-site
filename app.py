import os
import time

import streamlit as st
from google import genai
from google.genai import types

# -----------------------------
# إعدادات التطبيق
# -----------------------------
st.set_page_config(
    page_title="وكيل الذكاء الاصطناعي",
    page_icon="🤖",
    layout="centered",
)

# استخدام اسم الموديل المستقر الموصى به
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """
أنت وكيل ذكاء اصطناعي متعدد المهام.
أجب باللغة التي يحددها المستخدم.
ساعد في البرمجة، والتفسير، والترجمة، والتلخيص،
والتخطيط، وتحليل النصوص وتوليد الأفكار.
كن واضحًا ودقيقًا، ولا تدّعِ أنك نفذت مهمة
خارج المحادثة أو أنك بحثت في الإنترنت إذا لم تفعل ذلك.
إذا كان الطلب غير واضح، فاطلب توضيحًا مناسبًا.
"""


def get_api_key():
    """قراءة المفتاح من أسرار Streamlit أو متغير البيئة."""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY", "").strip()


def create_client(api_key):
    return genai.Client(api_key=api_key)


def ask_gemini(client, messages, task, language):
    """إرسال سياق المحادثة إلى Gemini مع إعادة محاولة محدودة."""
    task_instructions = {
        "مساعد عام": "ساعد المستخدم في المهمة التي يطلبها.",
        "البرمجة وإصلاح الأخطاء": (
            "حلل الأكواد والأخطاء بعناية. قدم كودًا كاملًا "
            "عند الحاجة، واشرح مكان وضعه."
        ),
        "الترجمة": (
            "ترجم النص بدقة وحافظ على المعنى والتنسيق."
        ),
        "التلخيص": (
            "استخرج الأفكار الرئيسية وقدم ملخصًا منظمًا."
        ),
        "التحليل والبحث": (
            "حلل المعلومات المتاحة، وميز بين الحقائق "
            "والاستنتاجات. لا تدّعِ البحث المباشر في الويب."
        ),
        "التخطيط وتوليد الأفكار": (
            "اقترح خطة عملية وخطوات واضحة."
        ),
    }

    instruction = (
        SYSTEM_INSTRUCTION
        + "\nالمهمة: "
        + task_instructions.get(task, task_instructions["مساعد عام"])
        + "\nلغة الإجابة المطلوبة: "
        + language
    )

    contents = []
    for item in messages:
        role = "model" if item["role"] == "assistant" else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=item["content"])],
            )
        )

    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=instruction,
                    temperature=0.5,
                    max_output_tokens=4096,
                ),
            )

            answer = response.text
            if not answer or not answer.strip():
                raise RuntimeError(
                    "وصل رد فارغ من النموذج. جرّب صياغة الطلب مجددًا."
                )

            return answer.strip()

        except Exception as exc:
            last_error = exc
            error_text = str(exc).lower()

            retryable = any(
                marker in error_text
                for marker in (
                    "503", "429", "500", "502",
                    "504", "unavailable", "overloaded",
                    "resource_exhausted", "timeout",
                    "temporarily",
                )
            )

            if retryable and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue

            break

    error_text = str(last_error).lower()

    if "429" in error_text or "resource_exhausted" in error_text:
        message = (
            "تم بلوغ حد الطلبات أو الحصة المتاحة. "
            "انتظر قليلًا ثم أعد المحاولة."
        )
    elif any(code in error_text for code in ("503", "502", "504")):
        message = (
            "خدمة Gemini غير متاحة مؤقتًا. "
            "أعد المحاولة بعد قليل."
        )
    elif "403" in error_text or "permission" in error_text:
        message = (
            "تعذر الوصول إلى الخدمة. تحقق من صلاحية المفتاح "
            "وإعدادات المشروع والحصة المتاحة."
        )
    elif "401" in error_text or "api key" in error_text:
        message = (
            "تعذر التحقق من مفتاح API. تأكد من إضافته "
            "في إعدادات Secrets."
        )
    else:
        message = (
            "حدث خطأ أثناء الاتصال بـ Gemini. "
            "راجع سجلات التطبيق في منصة الاستضافة "
            "وتحقق من إعدادات المفتاح."
        )

 details = f"{type(last_error).__name__}: {last_error}"
raise RuntimeError(f"{message}\nالتفاصيل التقنية: {details}") from last_error


# -----------------------------
# الواجهة
# -----------------------------
st.title("🤖 وكيل الذكاء الاصطناعي")
st.caption("مساعد متعدد المهام يعمل عبر الإنترنت")

with st.sidebar:
    st.header("الإعدادات")

    task = st.selectbox(
        "نوع المهمة",
        [
            "مساعد عام",
            "البرمجة وإصلاح الأخطاء",
            "الترجمة",
            "التلخيص",
            "التحليل والبحث",
            "التخطيط وتوليد الأفكار",
        ],
    )

    language = st.selectbox(
        "لغة الإجابة",
        ["العربية", "إنجليزية", "فرنسية"],
    )

    st.caption(f"النموذج: {MODEL_NAME}")

    if st.button("محادثة جديدة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("اكتب ما تريد من الوكيل...")

if prompt:
    api_key = get_api_key()

    if not api_key:
        st.error(
            "لم يتم العثور على GEMINI_API_KEY. "
            "أضفه إلى Secrets في إعدادات التطبيق."
        )
        st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("يفكر الوكيل..."):
                client = create_client(api_key)
                answer = ask_gemini(
                    client=client,
                    messages=st.session_state.messages,
                    task=task,
                    language=language,
                )

            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as exc:
            st.error(str(exc))
