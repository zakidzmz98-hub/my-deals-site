import os
import time
import base64
import re
import streamlit as st
import streamlit.components.v1 as components
from google import genai

# -----------------------------
# إعداد الصفحة
# -----------------------------
st.set_page_config(
    page_title="مساعد الذكاء الاصطناعي",
    page_icon="🤖",
    layout="wide",
)

MODEL_NAME = "gemini-3.8-flash"

st.title("🤖 مساعد الذكاء الاصطناعي")
st.caption("محادثة ذكية، بحث عبر Google، وإنشاء مشاريع HTML")

# -----------------------------
# التحقق من مفتاح API
# -----------------------------
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error(
        "لم يتم العثور على GEMINI_API_KEY. "
        "أضف المفتاح في إعدادات Secrets في Streamlit."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)

# -----------------------------
# الذاكرة داخل الجلسة
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "project_html" not in st.session_state:
    st.session_state.project_html = ""

if "project_prompt" not in st.session_state:
    st.session_state.project_prompt = ""

# -----------------------------
# استخراج HTML من الإجابة
# -----------------------------
def extract_html(answer):
    answer = answer.strip()
    match = re.search(
        r"```(?:html)?\s*(.*?)```",
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        answer = match.group(1).strip()
    return answer

# -----------------------------
# الاتصال بـ Gemini
# -----------------------------
def ask_gemini(prompt, history="", use_search=False):
    full_input = ""
    if history:
        full_input += (
            "هذه أجزاء من المحادثة السابقة للاستفادة منها:\n"
            + history
            + "\n\n"
        )
    full_input += prompt

    arguments = {
        "model": MODEL_NAME,
        "input": full_input,
        "generation_config": {
            "thinking_level": "low"
        },
    }

    if use_search:
        arguments["tools"] = [
            {"type": "google_search"}
        ]

    response = client.interactions.create(**arguments)
    answer = getattr(response, "output_text", None)

    if not answer:
        return "لم يرجع النموذج نصًا. حاول مرة أخرى."

    return answer

# -----------------------------
# الشريط الجانبي
# -----------------------------
with st.sidebar:
    st.header("⚙️ الإعدادات")

    mode = st.radio(
        "اختر وضع العمل",
        [
            "💬 محادثة وبحث",
            "💻 إنشاء مشروع",
        ],
    )

    st.divider()

    st.write("**النموذج:**")
    st.code(MODEL_NAME)

    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        st.session_state.project_html = ""
        st.session_state.project_prompt = ""
        st.rerun()

# -----------------------------
# تبويبات التطبيق
# -----------------------------
tab_chat, tab_project = st.tabs(
    [
        "💬 المحادثة",
        "🖥️ المشروع والمعاينة",
    ]
)

# -----------------------------
# تبويب المحادثة
# -----------------------------
with tab_chat:
    st.subheader("تحدث مع المساعد")

    if mode == "💻 إنشاء مشروع":
        st.info(
            "اكتب وصف الموقع أو اللعبة التي تريد إنشاءها. "
            "سيحاول المساعد إنشاء ملف HTML كامل."
        )
    else:
        st.info(
            "يمكنك طرح الأسئلة وطلب المساعدة. "
            "البحث عبر Google مفعّل في هذا الوضع."
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("اكتب رسالتك هنا...")

    if user_prompt:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_prompt)

        history = "\n".join(
            f'{item["role"]}: {item["content"]}'
            for item in st.session_state.messages[:-1][-10:]
        )

        with st.chat_message("assistant"):
            with st.spinner("جاري التفكير..."):
                try:
                    if mode == "💻 إنشاء مشروع":
                        project_request = (
                            "أنشئ مشروع ويب كاملًا في ملف HTML واحد. "
                            "أعد كود HTML النهائي فقط، دون Markdown "
                            "أو شرح خارج الكود. ضمّن CSS وJavaScript "
                            "داخل الملف نفسه عند الحاجة. "
                            "اجعل التصميم متجاوبًا مع الهاتف والحاسوب.\n\n"
                            "وصف المشروع:\n"
                            + user_prompt
                        )

                        answer = ask_gemini(
                            project_request,
                            history=history,
                            use_search=False,
                        )

                        html_code = extract_html(answer)

                        if (
                            "<html" not in html_code.lower()
                            and "<!doctype html" not in html_code.lower()
                        ):
                            st.warning(
                                "لم يرجع النموذج ملف HTML واضحًا. "
                                "راجع الإجابة أو اطلب منه إعادة إنشاء المشروع."
                            )
                            st.markdown(answer)
                        else:
                            st.session_state.project_html = html_code
                            st.session_state.project_prompt = user_prompt

                            answer = (
                                "✅ تم إنشاء المشروع. "
                                "افتح تبويب «المشروع والمعاينة» "
                                "لمشاهدة النتيجة ونسخ الكود أو تنزيله."
                            )
                            st.success(answer)

                    else:
                        answer = ask_gemini(
                            user_prompt,
                            history=history,
                            use_search=True,
                        )
                        st.markdown(answer)

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer,
                        }
                    )

                except Exception as error:
                    st.error(
                        "حدث خطأ أثناء الاتصال بالنموذج. "
                        "تحقق من إعدادات API ثم حاول مجددًا."
                    )
                    st.code(str(error))

# -----------------------------
# تبويب المشروع والمعاينة
# -----------------------------
with tab_project:
    st.subheader("🖥️ معاينة المشروع")

    if st.session_state.project_html:
        st.caption(
            f"المشروع الحالي: {st.session_state.project_prompt}"
        )

        st.markdown("### المعاينة")

        components.html(
            st.session_state.project_html,
            height=650,
            scrolling=True,
        )

        st.divider()

        st.markdown("### الكود المصدري")

        # عرض الكود مع إمكانية التمرير بالماوس
        st.code(
            st.session_state.project_html,
            language="html",
        )

        # ترميز الكود لتجنب مشاكل علامات الاقتباس وJavaScript
        encoded_code = base64.b64encode(
            st.session_state.project_html.encode("utf-8")
        ).decode("ascii")

        copy_component = f"""
        <div style="font-family: sans-serif; direction: rtl;">
            <button id="copy-code"
                style="
                    background: #2563eb;
                    color: white;
                    border: 0;
                    border-radius: 8px;
                    padding: 11px 18px;
                    font-size: 15px;
                    cursor: pointer;
                ">
                📋 نسخ الكود كاملًا
            </button>

            <span id="copy-status"
                style="margin-right: 12px; font-size: 14px;">
            </span>
        </div>

        <script>
        const encoded = "{encoded_code}";

        function decodeCode() {{
            const binary = atob(encoded);
            const bytes = Uint8Array.from(
                binary,
                char => char.charCodeAt(0)
            );
            return new TextDecoder("utf-8").decode(bytes);
        }}

        document.getElementById("copy-code").onclick = async () => {{
            const status = document.getElementById("copy-status");
            const code = decodeCode();

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
                area.focus();
                area.select();

                const copied = document.execCommand("copy");
                area.remove();

                status.textContent = copied
                    ? "تم النسخ بنجاح ✓"
                    : "تعذر النسخ. استخدم زر النسخ في مربع الكود.";

                status.style.color = copied ? "green" : "red";
            }}
        }};
        </script>
        """

        components.html(
            copy_component,
            height=60,
            scrolling=False,
        )

        st.download_button(
            label="⬇️ تنزيل المشروع بصيغة HTML",
            data=st.session_state.project_html,
            file_name="my_ai_project.html",
            mime="text/html",
            use_container_width=True,
        )

    else:
        st.info(
            "لم يتم إنشاء مشروع بعد. "
            "انتقل إلى المحادثة، واختر «إنشاء مشروع»، "
            "ثم اكتب وصف المشروع الذي تريده."
        )
