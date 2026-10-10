
import os
import re
import time
import streamlit.components.v1 as components
import json


from urllib.parse import quote

import streamlit as st
from google import genai


# ---------------------------------
# إعداد التطبيق
# ---------------------------------
st.set_page_config(
    page_title="Gemini AI Agent",
    page_icon="🤖",
    layout="wide",
)

MODEL_NAME = "gemini-3.8-flash"

st.title("🤖 وكيل Gemini الذكي")
st.caption("محادثة، إنشاء مشاريع، ومعاينة مباشرة")


# ---------------------------------
# إعداد مفتاح API
# ---------------------------------
def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.environ.get("GEMINI_API_KEY", "").strip()


# ---------------------------------
# الاتصال بـ Gemini
# ---------------------------------
def call_gemini(prompt, mode, history):
    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "لم يتم العثور على GEMINI_API_KEY. "
            "أضفه في إعدادات Secrets في Streamlit."
        )

    client = genai.Client(api_key=api_key)

    if mode == "إنشاء مشروع":
        instructions = """
أنت مطور ويب خبير.
أنشئ مشروعًا كاملًا ذاتيًا في ملف HTML واحد.
يجب أن يحتوي الملف على HTML وCSS وJavaScript عند الحاجة.
اجعل الواجهة جميلة ومتجاوبة مع الهاتف والحاسوب.
في الألعاب، أضف طريقة لعب واضحة وأزرارًا قابلة للاستخدام.
لا تستخدم مكتبات خارجية أو صورًا خارجية إلا عند الضرورة.
استخدم رسومات CSS أو SVG داخلية عندما يكون ذلك مناسبًا.
أعد ملف HTML فقط، دون Markdown أو شروحات خارجه.
لا تضع أسرارًا أو مفاتيح API داخل الملف.
"""
    else:
        instructions = """
أنت وكيل ذكاء اصطناعي مساعد.
ساعد المستخدم في البرمجة والترجمة والتلخيص والتخطيط
وتحليل المعلومات. كن واضحًا وصريحًا بشأن ما تستطيع فعله.
لا تدّعِ أنك فتحت متصفحًا أو نفذت إجراءً لم تنفذه.
أجب باللغة المناسبة لطلب المستخدم.
"""

    transcript = []
    for item in history[-12:]:
        role = "المستخدم" if item["role"] == "user" else "المساعد"
        transcript.append(f"{role}: {item['content']}")

    full_input = (
        instructions
        + "\n\nسجل المحادثة:\n"
        + "\n\n".join(transcript)
        + "\n\nطلب المستخدم الحالي:\n"
        + prompt
    )

    last_error = None

    for attempt in range(3):
        try:
            result = client.interactions.create(
                model=MODEL_NAME,
                input=full_input,
                generation_config={"thinking_level": "low"},
            )

            answer = result.output_text

            if not answer or not answer.strip():
                raise RuntimeError("أعاد النموذج إجابة فارغة.")

            return answer.strip()

        except Exception as exc:
            last_error = exc
            error = str(exc).lower()

            temporary = any(
                token in error
                for token in (
                    "429", "500", "502", "503", "504",
                    "timeout", "unavailable", "overloaded",
                )
            )

            if temporary and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue

            break

    raise RuntimeError(
        f"تعذر الاتصال بـ Gemini: "
        f"{type(last_error).__name__}: {last_error}"
    ) from last_error


# ---------------------------------
# استخراج HTML من الإجابة
# ---------------------------------
def extract_html(answer):
    match = re.search(
        r"```(?:html)?\s*(.*?)```",
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    html = match.group(1).strip() if match else answer.strip()

    start = html.lower().find("<!doctype html")
    if start == -1:
        start = html.lower().find("<html")

    if start > 0:
        html = html[start:]

    if "<html" not in html.lower():
        raise ValueError(
            "لم يُنشئ النموذج ملف HTML صالحًا. "
            "أعد المحاولة واطلب منه إنشاء المشروع في ملف HTML واحد."
        )

    return html


# ---------------------------------
# الحالة
# ---------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "project_html" not in st.session_state:
    st.session_state.project_html = ""

if "project_prompt" not in st.session_state:
    st.session_state.project_prompt = ""


# ---------------------------------
# الشريط الجانبي
# ---------------------------------
with st.sidebar:
    st.header("إعدادات الوكيل")

    mode = st.radio(
        "ماذا تريد أن يفعل الوكيل؟",
        ["محادثة", "إنشاء مشروع"],
    )

    st.caption(f"النموذج: {MODEL_NAME}")

    if st.button("بدء محادثة جديدة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("مسح المشروع الحالي", use_container_width=True):
        st.session_state.project_html = ""
        st.session_state.project_prompt = ""
        st.rerun()


# ---------------------------------
# الواجهة الرئيسية
# ---------------------------------
chat_tab, project_tab = st.tabs(
    ["💬 المحادثة", "🛠️ مساحة المشاريع"]
)

with chat_tab:
    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])

    prompt = st.chat_input(
        "مثال: اشرح لي كيف تعمل لعبة الديناصور..."
    )

    if prompt:
        st.session_state.messages.append(
            {"role": "user", "content": prompt}
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                with st.status(
                    "يعمل الوكيل على طلبك...",
                    expanded=True,
                ) as status:
                    st.write("1. تجهيز الطلب وسياق المحادثة")

                    answer = call_gemini(
                        prompt=prompt,
                        mode=mode,
                        history=st.session_state.messages,
                    )

                    st.write("2. استلام النتيجة من Gemini")

                    if mode == "إنشاء مشروع":
                        st.write("3. تجهيز ملف المشروع للمعاينة")
                        html = extract_html(answer)

                        st.session_state.project_html = html
                        st.session_state.project_prompt = prompt

                        answer = (
                            "تم إنشاء ملف المشروع. "
                            "افتح تبويب «مساحة المشاريع» "
                            "لمعاينته وتنزيل الكود."
                        )

                    status.update(
                        label="اكتملت المهمة",
                        state="complete",
                        expanded=False,
                    )

                st.markdown(answer)

                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

            except Exception as exc:
                st.error(str(exc))


with project_tab:
    st.subheader("مساحة المشاريع")

    st.write(
        "اختر «إنشاء مشروع» من الشريط الجانبي، "
        "ثم اطلب إنشاء لعبة أو صفحة ويب."
    )

    if st.session_state.project_html:
        st.success(
            f"المشروع الحالي: {st.session_state.project_prompt}"
        )

        preview_url = (
            "data:text/html;charset=utf-8,"
            + quote(st.session_state.project_html, safe="")
        )

        st.markdown("### معاينة المشروع")

        st.warning(
            "تُعرض المعاينة في إطار منفصل. "
            "لا تدخل كلمات مرور أو أسرارًا في المشاريع المولدة، "
            "ولا تستخدم كودًا غير موثوق."
        )

     
components.html(
    st.session_state.project_html,
    height=650,
    scrolling=True,
)


        st.markdown("### الكود المصدري")

      
st.code(
    st.session_state.project_html,
    language="html",
)

components.html(
    f"""
    <button id="copy-code"
        style="
            background:#2563eb;
            color:white;
            border:0;
            border-radius:8px;
            padding:10px 18px;
            font-size:15px;
            cursor:pointer;
        ">
        📋 نسخ الكود كاملًا
    </button>

    <span id="copy-status"
        style="margin-left:12px;font-size:14px;">
    </span>

    <script>
    const code = {json.dumps(st.session_state.project_html)};

    document.getElementById("copy-code").onclick = async () => {{
        const status = document.getElementById("copy-status");

        try {{
            await navigator.clipboard.writeText(code);
            status.textContent = "تم النسخ بنجاح ✓";
            status.style.color = "green";
        }} catch (error) {{
            const area = document.createElement("textarea");
            area.value = code;
            area.style.position = "fixed";
            area.style.left = "0";
            area.style.top = "0";
            document.body.appendChild(area);
            area.select();

            const copied = document.execCommand("copy");
            area.remove();

            status.textContent = copied
                ? "تم النسخ بنجاح ✓"
                : "تعذر النسخ. استخدم زر النسخ في مربع الكود.";
        }}
    }};
    </script>
    """,
    height=65,
    scrolling=False,
)

st.download_button(
    "⬇️ تنزيل المشروع بصيغة HTML",
    data=st.session_state.project_html,
    file_name="my_ai_project.html",
    mime="text/html",
    use_container_width=True,
)


        st.download_button(
            "تنزيل المشروع بصيغة HTML",
            data=st.session_state.project_html,
            file_name="my_ai_project.html",
            mime="text/html",
            use_container_width=True,
        )

    else:
        st.info(
            "لم يتم إنشاء مشروع بعد. "
            "اختر «إنشاء مشروع» واطلب مثلًا: "
            "اصنع لعبة ديناصور أستطيع لعبها."
        )
