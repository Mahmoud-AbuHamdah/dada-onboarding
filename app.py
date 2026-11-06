import streamlit as st
from data_loader import load_all, check_data
import pandas as pd
from retrieval import KeywordRetriever, SemanticRetriever, load_model
import html
import re
from qa import answer_question, get_client
from scenarios import evaluate_response

st.set_page_config(page_title="Dada Group Academy", page_icon="🎓", layout="wide")
st.markdown(
    "<style>textarea, input[type='text'] {unicode-bidi: plaintext; text-align: start;}</style>",
    unsafe_allow_html=True,
)

data = load_all()

@st.cache_resource
def get_model():
    return load_model()          # loaded once, kept in memory


@st.cache_resource
def get_retrievers(kb):
    return {
        "Keyword": KeywordRetriever(kb),
        "AI (meaning)": SemanticRetriever(kb, get_model()),
    }

retrievers = get_retrievers(data["kb"])

@st.cache_resource
def get_llm_client():
    return get_client()

client = get_llm_client()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "feedback" not in st.session_state:
    st.session_state.feedback = {}          # scenario id -> feedback
if "done_scenarios" not in st.session_state:
    st.session_state.done_scenarios = set() # scenario ids completed    

# ---------- Remembered between reruns ----------
if "role" not in st.session_state:
    st.session_state.role = None
if "name" not in st.session_state:
    st.session_state.name = ""

# ---------- Fixed text ----------
ROLES = {
    "Sales": {
        "ar": "المبيعات",
        "icon": "🛒",
        "desc": "Help customers in the showroom: understand their needs, "
                "give honest product information, and coordinate with delivery.",
    },
    "Delivery": {
        "ar": "التوصيل",
        "icon": "🚚",
        "desc": "Get orders to customers: handle products carefully, "
                "give accurate updates, and coordinate with other teams.",
    },
}

DISCLAIMER = (
    "ℹ️ This is a learning assistant for a student competition. "
    "Company facts are paraphrased from supplied materials. Scenarios and the "
    "learning plan are fictional training examples, not official Dada Group "
    "procedures. For official policy, always confirm with HR. "
    "This tool does not make any employment decisions."
)

def show_text(text):
    """Show text right-to-left if it contains Arabic."""
    safe = html.escape(text).replace("\n", "<br>")
    if re.search(r"[\u0600-\u06FF]", text):
        st.markdown(f'<div dir="rtl" style="text-align:right">{safe}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(safe, unsafe_allow_html=True)


def show_answer(out):
    """Show one assistant answer with its status, sources and explanation."""
    badges = {"answered": "✅ Answered from sources",
              "partial": "⚠️ Partly answered",
              "refused": "🚫 Not in my sources"}
    st.caption(badges.get(out["status"], out["status"]))
    show_text(out["answer"])

    facts_by_id = {f["id"]: f for f in out["facts"]}
    for kid in out["used_ids"]:
        st.caption(f"📄 Source: **{kid}** · {facts_by_id[kid]['source']}")

    if out["mode"] == "fallback":
        st.warning("AI is unavailable right now, so this shows the closest fact directly.")
        if out.get("error"):
            st.caption(f"Technical detail: {out['error']}")

    with st.expander("🔍 Why this answer?"):        
        if out.get("model"):
            st.caption(f"Answer written by: {out['model']}")
        for err in out.get("errors", []):
            st.caption(f"⚠️ Tried first: {err[:150]}")
        st.write("Facts found by the AI search, most related first:")
        for f in out["facts"]:
            used = " ← used" if f["id"] in out["used_ids"] else ""
            st.write(f"**{f['id']}** · score {f['score']:.2f}{used}")
            show_text(f["text"])

def show_feedback(fb, sc):
    """Show the feedback for one scenario response."""
    score = int(fb.get("score", 0))
    st.subheader(f"Feedback: {'★' * score}{'☆' * (5 - score)} ({score}/5)")

    if fb["mode"] == "fallback":
        st.warning("AI feedback is unavailable, so this is a rough comparison "
                   "with the suggested response.")

    if fb.get("strengths"):
        st.markdown("**What you did well**")
        show_text(fb["strengths"])
    if fb.get("improve"):
        st.markdown("**What to improve**")
        show_text(fb["improve"])

    v = fb["value"]
    st.info(f"💎 Company value: **{v['name_en']}** ({v['name_ar']}) · source {v['id']}")
    show_text(fb["value_link"])

    with st.expander("Suggested good response"):
        show_text(sc["suggested_good_response_ar"])
        if fb.get("model"):
            st.caption(f"Feedback written by: {fb['model']}")

# ---------- Pages ----------
def welcome_page():
    st.title("🎓 Dada Group Academy")
    st.subheader("أهلاً بك في مجموعة الدادا — Welcome to Dada Group")
    st.write(
        "This assistant supports you during your first 90 days. You can ask "
        "questions about the company, practise real workplace situations, "
        "and follow a suggested learning plan."
    )

    name = st.text_input(
        "Your first name (optional)",
        value=st.session_state.name,
        help="Only used to greet you. It is never saved or sent anywhere.",
    )

    st.write("### Choose your training track")
    col1, col2 = st.columns(2)
    for col, role in zip([col1, col2], ROLES):
        info = ROLES[role]
        with col:
            with st.container(border=True):
                st.markdown(f"## {info['icon']} {role} — {info['ar']}")
                st.write(info["desc"])
                if st.button(f"Start as {role}", key=f"start_{role}",
                             use_container_width=True, type="primary"):
                    st.session_state.role = role
                    st.session_state.name = name.strip()
                    st.rerun()

    st.caption("Sales and Delivery are fictional training tracks for this competition.")
    st.info(DISCLAIMER)


def assistant_page():
    st.header("💬 Assistant")

    role = st.session_state.role
    n_scenarios = (data["scenarios"]["department"] == role).sum()
    n_milestones = (data["plan"]["department"] == role).sum()
    st.write(
        f"Your {role} track has **{n_scenarios}** practice scenarios "
        f"and **{n_milestones}** learning milestones."
    )
    if client is None:
        st.warning("No Gemini API key found. Answers will use the fallback mode.")

    # Show the conversation so far
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if m["role"] == "user":
                show_text(m["content"])
            else:
                show_answer(m["content"])

    # New question
    question = st.chat_input("Ask about Dada Group (Arabic or English)...")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.spinner("Looking in the knowledge base..."):
            out = answer_question(question, role, retrievers["AI (meaning)"],
                                  data["kb"], client)
        st.session_state.messages.append({"role": "assistant", "content": out})
        st.rerun()

    if st.session_state.messages and st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()

def scenarios_page():
    st.header("🎭 Practice scenarios")
    st.caption("These are fictional training examples, not official Dada Group "
               "procedures. Feedback is for practice only, not an evaluation.")

    role = st.session_state.role
    role_sc = data["scenarios"][data["scenarios"]["department"] == role].reset_index(drop=True)

    # Choose a scenario
    labels = []
    for _, r in role_sc.iterrows():
        tick = "✅ " if r["id"] in st.session_state.done_scenarios else ""
        labels.append(f"{tick}{r['id']} · {r['company_value']}")
    choice = st.radio("Choose a scenario", labels, horizontal=True)
    sc = role_sc.iloc[labels.index(choice)]

    # Show the situation
    with st.container(border=True):
        st.markdown(f"**Situation** · practises: {sc['company_value']}")
        show_text(sc["scenario_ar"])

    # The user's response
    answer = st.text_area("What would you do or say? (Arabic or English)",
                          key=f"resp_{sc['id']}")
    if st.button("Get feedback", type="primary", disabled=not answer.strip()):
        with st.spinner("Reviewing your response..."):
            fb = evaluate_response(sc, answer, data["kb"], client, get_model())
        st.session_state.feedback[sc["id"]] = fb
        st.session_state.done_scenarios.add(sc["id"])

    # Feedback, if there is any for this scenario
    fb = st.session_state.feedback.get(sc["id"])
    if fb:
        show_feedback(fb, sc)


def plan_page():
    st.header("🗓️ Suggested learning plan")
    st.write("Coming in Step 8.")


def progress_page():
    st.header("📊 My progress")
    st.write("Coming in Step 8.")


def data_page():
    st.header("📁 Data & sources")
    problems = check_data(data)
    if problems:
        st.error("Data problems found:")
        for p in problems:
            st.write("- " + p)
    else:
        st.success("All data files loaded and links checked: no problems found.")

    tabs = st.tabs(["Knowledge", "FAQ", "Scenarios", "Learning plan", "Quiz", "Jury tests"])
    for tab, key in zip(tabs, ["kb", "faq", "scenarios", "plan", "quiz", "jury"]):
        with tab:
            st.write(f"{len(data[key])} rows")
            st.dataframe(data[key], hide_index=True)

    st.divider()
    st.subheader("Retrieval test on the sample FAQ")
    rows = []
    for _, r in data["faq"].iterrows():
        expected = str(r["expected_knowledge_ids"]).split(";")
        row = {"FAQ": r["id"], "Question": r["employee_question_ar"],
               "Expected": r["expected_knowledge_ids"]}
        for name, retr in retrievers.items():
            top = retr.search(r["employee_question_ar"], top_k=1)[0]
            row[f"{name} found"] = top["id"]
            row[f"{name} score"] = round(top["score"], 2)
            row[f"{name} ✓"] = "✅" if top["id"] in expected else "❌"
        rows.append(row)
    results_df = pd.DataFrame(rows)
    for name in retrievers:
        n_ok = (results_df[f"{name} ✓"] == "✅").sum()
        st.write(f"**{name}:** top result correct for **{n_ok} of {len(results_df)}**")
    st.dataframe(results_df, hide_index=True)

    st.subheader("Questions that should be refused")
    st.caption("None of these are answered in the knowledge base. "
               "Their scores show how high a 'wrong' match can get.")
    unanswerable = [
        "ما رقم مدير الموارد البشرية؟",
        "كم راتبي؟",
        "ما الطقس اليوم؟",
        "أين أركن سيارتي؟",
        "من هو المدير العام؟",
        "كم يوم إجازة سنوية لي؟",
    ]
    rows = []
    for q in unanswerable:
        row = {"Question": q}
        for name, retr in retrievers.items():
            top = retr.search(q, top_k=1)[0]
            row[f"{name} found"] = top["id"]
            row[f"{name} score"] = round(top["score"], 2)
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True)


# ---------- Main flow ----------
if st.session_state.role is None:
    welcome_page()
else:
    role = st.session_state.role
    info = ROLES[role]

    with st.sidebar:
        greeting = f"Hi {st.session_state.name}!" if st.session_state.name else "Hi!"
        st.markdown(f"### {greeting}")
        st.write(f"Track: **{info['icon']} {role}** ({info['ar']})")
        if st.button("Change track"):
            st.session_state.role = None
            st.rerun()

        st.divider()
        page = st.radio(
            "Go to",
            ["💬 Assistant", "🎭 Scenarios", "🗓️ Learning plan", "📊 Progress", "📁 Data & sources"],
        )
        st.divider()
        st.caption(DISCLAIMER)

    pages = {
        "💬 Assistant": assistant_page,
        "🎭 Scenarios": scenarios_page,
        "🗓️ Learning plan": plan_page,
        "📊 Progress": progress_page,
        "📁 Data & sources": data_page,
    }
    pages[page]()