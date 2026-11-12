import datetime
import glob
import html
import os
import re

import pandas as pd
import streamlit as st

from data_loader import load_all, check_data
from i18n import TEXT, ROLE_TEXT, SUGGESTIONS, EXAMPLES
from progress import MILESTONE_AR, milestone_key, get_activities, completion_percent
from qa import REFUSAL, answer_question, get_client
from retrieval import KeywordRetriever, SemanticRetriever, load_model
from router import detect_intent, mentioned_role, pick_scenario
from scenarios import evaluate_response, value_info

st.set_page_config(page_title="Dada Group Academy", page_icon="🎓", layout="wide")

data = load_all()


# =====================================================================
# Models and AI client (loaded once, kept in memory)
# =====================================================================
@st.cache_resource
def get_model():
    return load_model()


@st.cache_resource
def get_retrievers(kb):
    return {
        "Keyword": KeywordRetriever(kb),
        "AI (meaning)": SemanticRetriever(kb, get_model()),
    }


@st.cache_resource
def get_llm_client():
    return get_client()


retrievers = get_retrievers(data["kb"])
client = get_llm_client()


# =====================================================================
# Remembered between reruns
# =====================================================================
DEFAULTS = {
    "role": None,               # Sales or Delivery
    "name": "",                 # optional first name
    "lang": "en",               # interface language: en or ar
    "messages": [],             # chat history
    "queued": None,             # example question clicked, waiting to be sent
    "feedback": {},             # scenario id -> feedback
    "done_scenarios": set(),    # scenario ids completed
    "done_milestones": set(),   # "Sales:Day 30", ...
    "quiz_score": {},           # role -> score (missing = not taken yet)
    "quiz_answers": {},         # role -> {quiz id: chosen option}
    "quiz_retry": {},           # role -> True while the retry form is open
    "quiz_attempts": {},        # role -> number of retries started
    "quiz_last_gain": {},       # role -> points gained in the last retry
    "pending_scenario": None,   # scenario id waiting for the user's response
    "text_size": "normal",      # normal, large or xlarge
    "start_date": None,         # optional first working day, for the 90-day marker
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================================
# Language helpers
# =====================================================================
ARABIC_RE = re.compile(r"[؀-ۿ]")
ROLE_ICON = {"Sales": "🛒", "Delivery": "🚚"}
LANG_LABELS = {"en": "English", "ar": "العربية"}
TEXT_SIZES = {"normal": 16, "large": 18, "xlarge": 20}          # base font size in pixels
SIZE_LABELS = {"normal": "A", "large": "A+\u200e", "xlarge": "A++\u200e"}   # \u200e keeps "A+" in order in Arabic


def is_ar():
    return st.session_state.lang == "ar"


def t(key, **kwargs):
    """Interface text in the current language."""
    text = TEXT[key][st.session_state.lang]
    return text.format(**kwargs) if kwargs else text


def role_name(role):
    return ROLE_TEXT[role][st.session_state.lang]["name"]


def milestone_name(milestone):
    return MILESTONE_AR.get(milestone, milestone) if is_ar() else milestone


def value_name(value):
    return value["name_ar"] if is_ar() else value["name_en"]


# =====================================================================
# Look and feel
# =====================================================================
def load_css():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');

    .stApp, .stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp label,
    .stApp button, .stApp input, .stApp textarea, .stApp td, .stApp th {
        font-family: 'IBM Plex Sans Arabic', 'Segoe UI', Tahoma, sans-serif;
    }
    footer, [data-testid="stDecoration"] {display: none !important;}
    header[data-testid="stHeader"] {background: transparent;}
    .block-container {padding-top: 2.2rem; max-width: 1180px;}

    /* Header bar */
    .app-header {display:flex; justify-content:space-between; align-items:center; gap:12px;
        background:#2B1D14; color:#FAF6F0; border-radius:14px; padding:14px 22px; margin-bottom:22px;}
    .app-title {font-weight:700; font-size:1.15rem; letter-spacing:.2px;}
    .app-meta {display:flex; gap:8px; flex-wrap:wrap;}
    .badge {background:#6F4E37; color:#FAF6F0; border-radius:999px; padding:4px 12px;
        font-size:.85rem; white-space:nowrap;}
    .badge-soft {background:#4A3527;}
    .page-title {font-size:2.1rem; font-weight:700; color:#2B1D14; margin:0 0 4px 0; padding:0;}
    .page-sub {color:#6B5644; font-size:1.02rem; margin:0 0 18px 0;}

    /* Cards: any container whose key starts with "card" */
    div[class*="st-key-card"] {background:#FFFDF9; border:1px solid #E3D6C6; border-radius:14px;
        padding:18px 20px; box-shadow:0 1px 3px rgba(43,29,20,.06);}
    div[class*="st-key-cardaccent"] {background:#F3EADF; border-color:#D8C7B2;}

    /* KPI tiles */
    .kpi {background:#FFFDF9; border:1px solid #E3D6C6; border-radius:14px; padding:16px 20px;
        box-shadow:0 1px 3px rgba(43,29,20,.06);}
    .kpi-label {color:#6B5644; font-size:.9rem;}
    .kpi-value {color:#2B1D14; font-size:2.1rem; font-weight:700; line-height:1.2;}
    .kpi-sub {color:#8A7563; font-size:.85rem;}

    /* Answer status and source badges */
    .status {display:inline-block; border-radius:999px; padding:3px 12px; font-size:.82rem;
        font-weight:600; margin-bottom:6px;}
    .status-answered {background:#E3EFE3; color:#2E5E33;}
    .status-partial {background:#F7EBD3; color:#7A5413;}
    .status-refused {background:#F0E3E0; color:#7D3B2F;}
    .src-row {display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;}
    .src {background:#EFE6DA; color:#4A3527; border-radius:8px; padding:3px 10px; font-size:.82rem;}

    .txt {line-height:1.65;}
    .muted {color:#6B5644;}

    /* Waiting-for-response bar and the 90-day timeline */
    .st-key-cardaccent_waiting {padding:10px 16px;}
    .tl-wrap {padding:6px 14px 0 14px;}
    .tl {position:relative; height:10px; background:#E9DDCD; border-radius:999px; margin-top:26px;}
    .tl-fill {position:absolute; top:0; bottom:0; inset-inline-start:0; background:#6F4E37; border-radius:999px;}
    .tl-tick {position:absolute; top:-4px; width:2px; height:18px; background:#B9A48D;}
    .tl-dot {position:absolute; top:-6px; width:22px; height:22px; margin-inline-start:-11px;
        background:#FFFDF9; border:5px solid #6F4E37; border-radius:50%; box-shadow:0 1px 4px rgba(43,29,20,.3);}
    .tl-here {position:absolute; top:-32px; white-space:nowrap; font-size:.8rem; font-weight:600; color:#6F4E37;}
    .tl-labels {position:relative; height:26px; margin-top:8px; color:#6B5644; font-size:.82rem;}
    .tl-labels span {position:absolute; white-space:nowrap;}
    .ms-badge {display:inline-block; border-radius:999px; padding:2px 12px; font-size:.8rem; font-weight:600;
        background:#EFE6DA; color:#4A3527;}
    .ms-badge-now {background:#6F4E37; color:#FAF6F0;}
    .ms-badge-passed {background:#F0EBE4; color:#8A7563;}

    /* Typed text follows its own direction; quiz options right to left */
    textarea, input[type='text'] {unicode-bidi: plaintext; text-align: start;}
    .st-key-quiz_box div[role='radiogroup'], .st-key-quiz_box_retry div[role='radiogroup'] {direction: rtl;}
    """
    css += "html {font-size: %dpx !important;}" % TEXT_SIZES[st.session_state.text_size]
    if is_ar():
        css += """
        .stApp, [data-testid="stSidebar"] {direction: rtl;}
        .stApp p, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp label {text-align: right;}
        """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def show_text(text, cls=""):
    """Show text in its own direction: right to left if it contains Arabic."""
    text = str(text)
    safe = html.escape(text).replace("\n", "<br>")
    rtl = bool(ARABIC_RE.search(text))
    align = "right" if rtl else "left"
    st.markdown(
        f'<div dir="{"rtl" if rtl else "ltr"}" class="txt {cls}" style="text-align:{align}">{safe}</div>',
        unsafe_allow_html=True,
    )


def page_header(title, subtitle=None):
    """Dark header bar with the app name and track, then the page title."""
    meta = ""
    role = st.session_state.role
    if role:
        pct = completion_percent(get_activities(data, role, st.session_state))
        meta = (f'<span class="badge">{ROLE_ICON[role]} {html.escape(role_name(role))}</span>'
                f'<span class="badge badge-soft">{html.escape(t("progress_short", pct=pct))}</span>')
    st.markdown(
        f'<div class="app-header"><div class="app-title">🎓 {html.escape(t("app_name"))}</div>'
        f'<div class="app-meta">{meta}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-title">{html.escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<p class="page-sub">{html.escape(subtitle)}</p>', unsafe_allow_html=True)


def kpi(column, label, value, sub):
    column.markdown(
        f'<div class="kpi"><div class="kpi-label">{html.escape(label)}</div>'
        f'<div class="kpi-value">{html.escape(value)}</div>'
        f'<div class="kpi-sub">{html.escape(sub)}</div></div>',
        unsafe_allow_html=True,
    )


def _on_lang_change():
    choice = st.session_state.get("lang_widget")
    if choice:                         # None if the user un-selects the current option
        st.session_state.lang = choice


def language_switch():
    st.segmented_control(
        t("language"), options=["en", "ar"], format_func=LANG_LABELS.get,
        default=st.session_state.lang, key="lang_widget", on_change=_on_lang_change,
    )


def _on_size_change():
    choice = st.session_state.get("size_widget")
    if choice:
        st.session_state.text_size = choice


def text_size_switch():
    st.segmented_control(
        t("text_size"), options=list(TEXT_SIZES), format_func=SIZE_LABELS.get,
        default=st.session_state.text_size, key="size_widget", on_change=_on_size_change,
    )


# =====================================================================
# The 90-day plan: which day is the employee on?
# =====================================================================
PLAN_DAYS = 90
MILESTONE_DAY = {"Days 1-7": 7, "Day 30": 30, "Day 60": 60, "Day 90": 90}


def plan_day():
    """Day number in the plan (1 = the start date), or None if no date was given."""
    start = st.session_state.start_date
    if not start:
        return None
    return (datetime.date.today() - start).days + 1


def days_text(n):
    """'in 3 days', with the correct Arabic plural."""
    if not is_ar():
        return "in 1 day" if n == 1 else f"in {n} days"
    if n == 1:
        return "بعد يوم واحد"
    if n == 2:
        return "بعد يومين"
    return f"بعد {n} أيام" if n <= 10 else f"بعد {n} يوماً"


def milestone_timing(milestone, day):
    """Where a milestone is compared with today. Returns (kind, text)."""
    target = MILESTONE_DAY[milestone]
    if milestone == "Days 1-7" and day <= 7:
        return "now", t("ms_now")
    if day == target:
        return "now", t("ms_today")
    if day < target:
        return "soon", days_text(target - day)
    return "passed", t("ms_passed")


def next_milestone(day):
    """The first milestone that has not passed yet: (name, text), or None."""
    for name in MILESTONE_DAY:
        kind, text = milestone_timing(name, day)
        if kind != "passed":
            return name, text
    return None


def show_timeline(day):
    """A bar for the 90 days with a marker on today."""
    pos = min(max(day, 1), PLAN_DAYS) / PLAN_DAYS * 100
    shift = "50%" if is_ar() else "-50%"            # centre labels in both directions
    ticks = "".join(f'<span class="tl-tick" style="inset-inline-start:{d / PLAN_DAYS * 100:.1f}%"></span>'
                    for d in (7, 30, 60))
    labels = "".join(
        f'<span style="inset-inline-start:{d / PLAN_DAYS * 100:.1f}%; transform:translateX({shift})">'
        f'{html.escape(t("day_n", n=d))}</span>' for d in (7, 30, 60))
    labels += f'<span style="inset-inline-end:0">{html.escape(t("day_n", n=90))}</span>'
    here = (f'<span class="tl-here" style="inset-inline-start:{pos:.1f}%; transform:translateX({shift})">'
            f'{html.escape(t("you_are_here"))}</span>') if 12 < pos < 88 else ""
    st.markdown(
        f'<div class="tl-wrap"><div class="tl">{here}<div class="tl-fill" style="width:{pos:.1f}%"></div>{ticks}'
        f'<span class="tl-dot" style="inset-inline-start:{pos:.1f}%"></span></div>'
        f'<div class="tl-labels">{labels}</div></div>',
        unsafe_allow_html=True,
    )


# =====================================================================
# Showing answers and feedback
# =====================================================================
STATUS_TEXT = {"answered": "st_answered", "partial": "st_partial", "refused": "st_refused"}


def show_answer(out):
    status = out["status"] if out["status"] in STATUS_TEXT else "refused"
    st.markdown(f'<span class="status status-{status}">{html.escape(t(STATUS_TEXT[status]))}</span>',
                unsafe_allow_html=True)

    answer = out["answer"]
    if answer == REFUSAL:              # the fixed bilingual refusal: show one language
        parts = REFUSAL.split("\n\n")
        answer = parts[0] if is_ar() else parts[-1]
    show_text(answer)

    facts_by_id = {f["id"]: f for f in out["facts"]}
    badges = "".join(
        f'<span class="src">📄 {html.escape(k)} · {html.escape(facts_by_id[k]["source"])}</span>'
        for k in out["used_ids"] if k in facts_by_id
    )
    if badges:
        st.markdown(f'<div class="src-row">{badges}</div>', unsafe_allow_html=True)

    if out.get("guard") == "contact":
        st.caption("🛡️ " + t("guard_contact"))

    if out["mode"] == "fallback":
        st.warning(t("fallback_warn"))
        if out.get("error"):
            st.caption(f"{t('tech_detail')}: {out['error'][:300]}")

    with st.expander(t("why")):
        if out.get("model"):
            st.caption(t("written_by", model=out["model"]))
        for err in out.get("errors", []):
            st.caption(f"⚠️ {t('tried_first')}: {err[:150]}")
        st.caption(t("facts_found"))
        for f in out["facts"]:
            used = f" ← {t('used')}" if f["id"] in out["used_ids"] else ""
            st.markdown(f"**{f['id']}** · {f['score']:.2f}{used}")
            show_text(f["text"], "muted")


def safe_score(value):
    """Turn the AI's score into a whole number from 0 to 5, whatever shape it came in."""
    found = re.search(r"\d+", str(value))          # 4, "4", 4.0 and "4/5" all give 4
    return max(0, min(5, int(found.group()))) if found else 0


def save_feedback(sid, fb):
    fb["score"] = safe_score(fb.get("score"))
    st.session_state.feedback[sid] = fb
    st.session_state.done_scenarios.add(sid)


def show_feedback(fb, sc):
    score = safe_score(fb.get("score"))
    st.markdown(f"#### {t('feedback')}: {'★' * score}{'☆' * (5 - score)} ({score}/5)")
    if fb["mode"] == "fallback":
        st.warning(t("fb_fallback"))
    if fb.get("strengths"):
        st.markdown(f"**{t('did_well')}**")
        show_text(fb["strengths"])
    if fb.get("improve"):
        st.markdown(f"**{t('improve')}**")
        show_text(fb["improve"])
    v = fb["value"]
    st.info(f"💎 {t('company_value', name=value_name(v), id=v['id'])}")
    if fb.get("value_link"):
        show_text(fb["value_link"])
    with st.expander(t("suggested_response")):
        show_text(sc["suggested_good_response_ar"])
        if fb.get("model"):
            st.caption(t("feedback_by", model=fb["model"]))


def scenario_by_id(sid):
    return data["scenarios"][data["scenarios"]["id"] == sid].iloc[0]


def activity_label(item):
    if item["type"] == "milestone":
        return milestone_name(item["milestone"])
    if item["type"] == "scenario":
        return f"{item['sid']} · {value_name(value_info(data['kb'], item['value']))}"
    return t("quiz_title")


# =====================================================================
# The chat router
# =====================================================================
NO_ANSWER_INTRO = {
    "ar": "لا تجيب مصادري عن هذا السؤال مباشرة، لكن يمكنك التدرّب عليه في موقف تدريبي:",
    "en": "My sources don't answer this question directly, but you can practise it as a scenario:",
}
CANCELLED = {"ar": ["تم إلغاء الموقف. يمكنك طرح سؤال أو بدء موقف آخر."],
             "en": ["Scenario cancelled. You can ask a question or start another scenario."]}


def start_scenario(message, role, intro=None):
    """Pick the closest scenario and wait for the user's response."""
    sc_role = mentioned_role(message) or role
    options = data["scenarios"][data["scenarios"]["department"] == sc_role]
    sc = pick_scenario(message, options, get_model())
    st.session_state.pending_scenario = sc["id"]
    v = value_info(data["kb"], sc["company_value"])
    content = {
        "ar": [f"🎭 موقف تدريبي {sc['id']} · {ROLE_TEXT[sc_role]['ar']['name']} · القيمة: {v['name_ar']}",
               sc["scenario_ar"],
               "كيف سترد؟ اكتب ردك في رسالتك التالية، أو اضغط «إلغاء الموقف»."],
        "en": [f"🎭 Practice scenario {sc['id']} · {sc_role} · value: {v['name_en']}",
               sc["scenario_ar"],
               "How would you respond? Type your answer in your next message, or press Cancel scenario."],
    }
    if intro:
        for lang in content:
            content[lang].insert(0, intro[lang])
    return {"kind": "text", "content": content}


def cancel_scenario():
    """Cancel button: stop waiting for a response."""
    st.session_state.pending_scenario = None
    st.session_state.messages.append({"role": "assistant", "kind": "text", "content": CANCELLED})


def handle_message(message, role):
    """Decide what to do with a chat message. Returns the assistant's reply."""

    # 1. A scenario is waiting: this message is the user's response
    if st.session_state.pending_scenario:
        sid = st.session_state.pending_scenario
        st.session_state.pending_scenario = None
        if message.strip().lower() in ("إلغاء", "الغاء", "cancel"):
            return {"kind": "text", "content": CANCELLED}
        sc = scenario_by_id(sid)
        fb = evaluate_response(sc, message, data["kb"], client, get_model())
        save_feedback(sid, fb)
        return {"kind": "feedback", "content": fb, "scenario_id": sid}

    intent = detect_intent(message)

    # 2. Progress update
    if intent["intent"] == "progress":
        ms = intent["milestone"]
        if ms is None:
            return {"kind": "text", "content": {
                "ar": ["أي مرحلة أكملت؟ الأيام من 1 إلى 7، اليوم 30، اليوم 60 أو اليوم 90."],
                "en": ["Which milestone did you complete: Days 1-7, Day 30, Day 60 or Day 90?"],
            }}
        st.session_state.done_milestones.add(milestone_key(role, ms))
        pct = completion_percent(get_activities(data, role, st.session_state))
        return {"kind": "text", "content": {
            "ar": [f"✅ تم تسجيل إنجاز {MILESTONE_AR[ms]} في مسار {ROLE_TEXT[role]['ar']['name']}. "
                   f"نسبة التقدم الآن {pct}%."],
            "en": [f"✅ Marked {ms} as done for the {role} track. Your progress is now {pct}%."],
        }}

    # 3. Start a scenario
    if intent["intent"] == "scenario":
        return start_scenario(message, role)

    # 4. A question: answer it from the knowledge base
    out = answer_question(message, role, retrievers["AI (meaning)"], data["kb"], client)

    # A question about a customer situation that the sources can't answer
    # becomes a practice scenario instead of a dead end
    if intent.get("scenario_if_unanswered") and out["status"] == "refused":
        return start_scenario(message, role, intro=NO_ANSWER_INTRO)
    return {"kind": "answer", "content": out}


def queue_message(text):
    """Example button clicked: send this text on the next run."""
    st.session_state.queued = text


# =====================================================================
# Pages
# =====================================================================
def welcome_page():
    top = st.columns([4, 1, 1])
    with top[1]:
        text_size_switch()
    with top[2]:
        language_switch()
    st.markdown(
        f'<div class="app-header"><div class="app-title">🎓 {html.escape(t("app_name"))}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="page-title">{html.escape(t("welcome_title"))}</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="page-sub">{html.escape(t("welcome_sub"))}</p>', unsafe_allow_html=True)

    name = st.text_input(t("name_label"), value=st.session_state.name, help=t("name_help"))

    st.markdown(f"### {t('choose_track')}")
    cols = st.columns(2)
    for col, role in zip(cols, ["Sales", "Delivery"]):
        info = ROLE_TEXT[role][st.session_state.lang]
        with col, st.container(key=f"card_role_{role}"):
            st.markdown(f"## {ROLE_ICON[role]} {info['name']}")
            show_text(info["desc"], "muted")
            if st.button(t("start_as", role=info["name"]), key=f"start_{role}",
                         type="primary", width="stretch"):
                st.session_state.role = role
                st.session_state.name = name.strip()
                st.rerun()

    st.caption(t("tracks_fictional"))
    st.info(t("disclaimer"))


def next_step(role):
    """Suggest one next activity. Returns (text, page key or None)."""
    items = get_activities(data, role, st.session_state)
    if not any(m["role"] == "user" for m in st.session_state.messages):
        return t("next_ask"), "assistant"
    if not any(i["done"] for i in items if i["type"] == "scenario"):
        return t("next_scenario"), "scenarios"
    if role not in st.session_state.quiz_score:
        return t("next_quiz"), "plan"
    for i in items:
        if i["type"] == "milestone" and not i["done"]:
            return t("next_milestone", milestone=milestone_name(i["milestone"])), "plan"
    return t("next_done"), "progress"


def home_page():
    role = st.session_state.role
    name = st.session_state.name
    title = t("home_title_name", name=name) if name else t("home_title")
    page_header(title, t("home_sub", track=role_name(role)))

    items = get_activities(data, role, st.session_state)
    n_done = sum(i["done"] for i in items)
    scen = [i for i in items if i["type"] == "scenario"]
    score = st.session_state.quiz_score.get(role)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1, t("kpi_completion"), f"{completion_percent(items)}%",
        t("kpi_completion_sub", done=n_done, total=len(items)))
    kpi(c2, t("kpi_scenarios"), f"{sum(i['done'] for i in scen)}/{len(scen)}", t("kpi_scenarios_sub"))
    kpi(c3, t("kpi_quiz"), f"{score}/{len(data['quiz'])}" if score is not None else "—",
        t("kpi_quiz_done") if score is not None else t("kpi_quiz_none"))
    day = plan_day()
    if day is None:
        kpi(c4, t("kpi_day"), "—", t("kpi_day_none"))
    elif day > PLAN_DAYS:
        kpi(c4, t("kpi_day"), "90+", t("kpi_day_over"))
    else:
        name, when = next_milestone(day)
        kpi(c4, t("kpi_day"), f"{day}/{PLAN_DAYS}", f"{milestone_name(name)}: {when}")

    st.write("")
    text, target = next_step(role)
    with st.container(key="cardaccent_next"):
        st.markdown(f"**{t('next_step')}**")
        show_text(text)
        if target:
            st.page_link(PAGES[target], label=t("go"), icon=":material/arrow_forward:")

    st.markdown(f"#### {t('quick_actions')}")
    actions = [("assistant", "qa_ask", "qa_ask_sub", ":material/chat:"),
               ("scenarios", "qa_practise", "qa_practise_sub", ":material/theater_comedy:"),
               ("plan", "qa_plan", "qa_plan_sub", ":material/calendar_month:")]
    for col, (target, label, sub, icon) in zip(st.columns(3), actions):
        with col, st.container(key=f"card_action_{target}"):
            st.page_link(PAGES[target], label=t(label), icon=icon)
            st.caption(t(sub))


def assistant_page():
    role = st.session_state.role
    page_header(t("nav_assistant"), t("assistant_sub"))
    if client is None:
        st.warning(t("no_key"))

    # Example questions
    st.caption(t("try"))
    for col, example in zip(st.columns(len(EXAMPLES["en"])), EXAMPLES[st.session_state.lang]):
        col.button(example, key=f"ex_{example}", width="stretch",
                   on_click=queue_message, args=(example,))

    # The conversation so far
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🎓" if m["role"] == "assistant" else None):
            kind = m.get("kind", "text")
            if kind == "answer":
                show_answer(m["content"])
            elif kind == "feedback":
                show_feedback(m["content"], scenario_by_id(m["scenario_id"]))
            elif isinstance(m["content"], dict):
                for paragraph in m["content"][st.session_state.lang]:
                    show_text(paragraph)
            else:
                show_text(m["content"])

    if st.session_state.pending_scenario:
        with st.container(key="cardaccent_waiting"):
            cols = st.columns([4, 1], vertical_alignment="center")
            cols[0].markdown("🎭 " + t("waiting", sid=st.session_state.pending_scenario))
            cols[1].button(t("cancel_scenario"), on_click=cancel_scenario,
                           icon=":material/close:", width="stretch")

    # A new message: typed, or an example button clicked
    message = st.chat_input(t("chat_placeholder"))
    if st.session_state.queued:
        message = message or st.session_state.queued
        st.session_state.queued = None
    if message:
        st.session_state.messages.append({"role": "user", "kind": "text", "content": message})
        with st.spinner(t("thinking")):
            reply = handle_message(message, role)
        st.session_state.messages.append({"role": "assistant", **reply})
        st.rerun()

    if st.session_state.messages and st.button(t("clear_chat"), icon=":material/delete:"):
        st.session_state.messages = []
        st.session_state.pending_scenario = None
        st.rerun()


def scenarios_page():
    page_header(t("nav_scenarios"), t("scenarios_sub"))
    role = st.session_state.role
    role_sc = data["scenarios"][data["scenarios"]["department"] == role].reset_index(drop=True)

    labels = []
    for _, r in role_sc.iterrows():
        tick = "✅ " if r["id"] in st.session_state.done_scenarios else ""
        labels.append(f"{tick}{r['id']} · {value_name(value_info(data['kb'], r['company_value']))}")
    choice = st.radio(t("choose_scenario"), labels, horizontal=True)
    sc = role_sc.iloc[labels.index(choice)]
    v = value_info(data["kb"], sc["company_value"])

    with st.container(key=f"card_situation_{sc['id']}"):
        st.markdown(f"**{t('situation')}** · {t('practises', value=value_name(v))}")
        show_text(sc["scenario_ar"])

    answer = st.text_area(t("your_response"), key=f"resp_{sc['id']}")
    if st.button(t("get_feedback"), type="primary", disabled=not answer.strip()):
        with st.spinner(t("reviewing")):
            fb = evaluate_response(sc, answer, data["kb"], client, get_model())
        save_feedback(sc["id"], fb)

    fb = st.session_state.feedback.get(sc["id"])
    if fb:
        with st.container(key=f"card_feedback_{sc['id']}"):
            show_feedback(fb, sc)


def toggle_milestone(key):
    """Called when a milestone checkbox is clicked."""
    if key in st.session_state.done_milestones:
        st.session_state.done_milestones.discard(key)
    else:
        st.session_state.done_milestones.add(key)


def _on_start_change():
    st.session_state.start_date = st.session_state.get("start_widget")


def plan_page():
    page_header(t("nav_plan"), t("plan_sub"))

    # Where am I in the 90 days? Needs only an optional start date.
    with st.container(key="card_day"):
        cols = st.columns([1, 2], vertical_alignment="center")
        cols[0].date_input(t("start_date"), value=st.session_state.start_date, key="start_widget",
                           max_value=datetime.date.today(), format="DD/MM/YYYY",
                           help=t("start_date_help"), on_change=_on_start_change)
        day = plan_day()
        with cols[1]:
            if day is None:
                show_text(t("day_none"), "muted")
            elif day > PLAN_DAYS:
                show_text(t("day_over"))
            else:
                name, when = next_milestone(day)
                show_text(t("day_status", day=day) + " " +
                          t("day_next", milestone=milestone_name(name), when=when))
        if day is not None:
            show_timeline(day)

    st.caption(t("probation_note"))

    role = st.session_state.role
    plan = data["plan"][data["plan"]["department"] == role]
    for _, r in plan.iterrows():
        key = milestone_key(role, r["milestone"])
        done = key in st.session_state.done_milestones
        cb_key = f"cb_{key}"
        st.session_state[cb_key] = done
        with st.container(key=f"card_ms_{role}_{r['milestone'].replace(' ', '_')}"):
            st.markdown(f"### {'✅' if done else '○'} {milestone_name(r['milestone'])}")
            if day is not None and r["milestone"] in MILESTONE_DAY:
                kind, when = milestone_timing(r["milestone"], day)
                st.markdown(f'<span class="ms-badge ms-badge-{kind}">{html.escape(when)}</span>',
                            unsafe_allow_html=True)
            show_text(r["learning_goal_ar"])
            st.caption(f"{t('suggested_activity')}: {SUGGESTIONS[r['milestone']][st.session_state.lang]}")
            st.checkbox(t("mark_done", milestone=milestone_name(r["milestone"])), key=cb_key,
                        on_change=toggle_milestone, args=(key,))

    st.divider()
    quiz_section()


def quiz_section():
    st.markdown(f"### 📝 {t('quiz_title')}")
    st.caption(t("quiz_sub"))
    role = st.session_state.role
    quiz = data["quiz"]

    # 1. The full quiz
    with st.container(key="quiz_box"), st.form(f"quiz_form_{role}"):
        answers = {}
        for _, q in quiz.iterrows():
            st.markdown(f"**{q['id']}**")
            show_text(q["question_ar"])
            answers[q["id"]] = st.radio(
                "answer", ["A", "B", "C"],
                format_func=lambda o, q=q: q[f"option_{o.lower()}"],
                index=None, key=f"quiz_{role}_{q['id']}", label_visibility="collapsed",
            )
        submitted = st.form_submit_button(t("submit_quiz"), type="primary")

    if submitted:
        if None in answers.values():
            st.warning(t("answer_all"))
        else:
            save_quiz_answers(role, answers)
            st.session_state.quiz_retry[role] = False

    if role not in st.session_state.quiz_score:
        return

    # 2. Score and results
    given = st.session_state.quiz_answers[role]
    missed = quiz[[given.get(q["id"]) != q["correct_option"] for _, q in quiz.iterrows()]]
    score = st.session_state.quiz_score[role]
    st.success(t("your_score", score=score, total=len(quiz)))
    gain = st.session_state.quiz_last_gain.pop(role, None)
    if gain:
        st.info("📈 " + t("improved", n=gain))
    direction = "rtl" if is_ar() else "ltr"
    for _, q in quiz.iterrows():
        mark = "✅" if given.get(q["id"]) == q["correct_option"] else "❌"
        correct_text = html.escape(q[f"option_{q['correct_option'].lower()}"])
        # <bdi> keeps the Arabic answer in its own direction inside an English line
        st.markdown(
            f'<div dir="{direction}" class="txt">{mark} <b>{q["id"]}</b> · '
            f'{t("correct_label")}: <bdi>{correct_text}</bdi> · '
            f'{t("source_word")} {q["source_knowledge_id"]}</div>',
            unsafe_allow_html=True,
        )

    if missed.empty:
        st.info("🎉 " + t("all_correct"))
        return

    # 3. Adaptive part: review each missed question
    st.markdown(f"#### 🔁 {t('review_title')}")
    st.caption(t("review_intro", n=len(missed)))
    for _, q in missed.iterrows():
        fact = data["kb"][data["kb"]["id"] == q["source_knowledge_id"]].iloc[0]
        with st.container(key=f"card_review_{role}_{q['id']}"):
            show_text(f"{q['id']} · {q['question_ar']}")
            st.caption(f"📄 {t('fact_label')} {fact['id']} · {fact['source_document']}, p. {fact['source_page']}")
            show_text(fact["answer_ar"])
            cols = st.columns(2)
            if cols[0].button(t("ask_about"), key=f"ask_{role}_{q['id']}",
                              icon=":material/chat:", width="stretch"):
                st.session_state.queued = q["question_ar"]
                st.switch_page(PAGES["assistant"])
            related = related_scenario(fact, role)
            if related is not None:
                cols[1].page_link(PAGES["scenarios"], icon=":material/theater_comedy:",
                                  label=t("practise_related", sid=related["id"],
                                          value=value_name(value_info(data["kb"], related["company_value"]))))

    # 4. Retry only the missed questions
    if not st.session_state.quiz_retry.get(role):
        if st.button(t("retry_btn", n=len(missed)), type="primary", icon=":material/replay:"):
            st.session_state.quiz_retry[role] = True
            st.session_state.quiz_attempts[role] = st.session_state.quiz_attempts.get(role, 0) + 1
            st.rerun()
        return

    attempt = st.session_state.quiz_attempts.get(role, 1)
    st.markdown(f"#### {t('retry_title')}")
    with st.container(key="quiz_box_retry"), st.form(f"quiz_retry_{role}_{attempt}"):
        retry = {}
        for _, q in missed.iterrows():
            st.markdown(f"**{q['id']}**")
            show_text(q["question_ar"])
            retry[q["id"]] = st.radio(
                "answer", ["A", "B", "C"],
                format_func=lambda o, q=q: q[f"option_{o.lower()}"],
                index=None, key=f"retry_{role}_{attempt}_{q['id']}", label_visibility="collapsed",
            )
        retry_submitted = st.form_submit_button(t("retry_submit"), type="primary")

    if retry_submitted:
        if None in retry.values():
            st.warning(t("answer_all"))
        else:
            before = st.session_state.quiz_score[role]
            save_quiz_answers(role, {**given, **retry})
            st.session_state.quiz_retry[role] = False
            st.session_state.quiz_last_gain[role] = st.session_state.quiz_score[role] - before
            st.rerun()


def save_quiz_answers(role, answers):
    """Store a full set of answers and recompute the score."""
    quiz = data["quiz"]
    st.session_state.quiz_answers[role] = answers
    st.session_state.quiz_score[role] = sum(
        answers.get(q["id"]) == q["correct_option"] for _, q in quiz.iterrows()
    )


def related_scenario(fact, role):
    """If a fact is a company value, return this track's scenario that practises it."""
    if fact["topic"] != "Values":
        return None
    sc = data["scenarios"]
    match = sc[(sc["department"] == role) & (sc["company_value"] == fact["keyword_en"])]
    return None if match.empty else match.iloc[0]


def progress_page():
    role = st.session_state.role
    page_header(t("nav_progress"), t("progress_sub", track=role_name(role)))
    items = get_activities(data, role, st.session_state)
    pct = completion_percent(items)
    n_done = sum(i["done"] for i in items)

    c1, c2 = st.columns([1, 2])
    kpi(c1, t("kpi_completion"), f"{pct}%", t("kpi_completion_sub", done=n_done, total=len(items)))
    with c2:
        st.write("")
        st.progress(pct / 100)

    st.markdown(f"#### {t('activities')}")
    table = pd.DataFrame([{
        t("col_type"): t(f"type_{i['type']}"),
        t("col_activity"): activity_label(i),
        t("col_done"): "✅" if i["done"] else "○",
    } for i in items])
    st.dataframe(table, hide_index=True, width="stretch")

    role_ids = set(data["scenarios"].loc[data["scenarios"]["department"] == role, "id"])
    role_scores = {sid: fb["score"] for sid, fb in st.session_state.feedback.items() if sid in role_ids}
    if role_scores:
        st.markdown(f"#### {t('practice_scores')}")
        for sid, s in role_scores.items():
            st.write(f"**{sid}:** {s}/5")

    st.markdown(f"#### {t('summary')}")
    st.caption(t("summary_sub"))
    lines = [t("summary_head", track=role_name(role)),
             t("summary_completion", pct=pct, done=n_done, total=len(items)), ""]
    lines += [f"[{'x' if i['done'] else ' '}] {t('type_' + i['type'])}: {activity_label(i)}" for i in items]
    if role in st.session_state.quiz_score:
        lines.append("\n" + t("summary_quiz", score=st.session_state.quiz_score[role], total=len(data["quiz"])))
    for sid, s in role_scores.items():
        lines.append(t("summary_scenario", sid=sid, score=s))
    lines.append("\n" + t("summary_note"))
    st.download_button(t("download_summary"), "\n".join(lines), file_name="learning_summary.txt",
                       icon=":material/download:")


def data_page():
    page_header(t("nav_data"), t("data_sub"))
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
    st.subheader("🧪 Automatic test results")
    files = sorted(glob.glob("results/test_results_*.csv"))
    if not files:
        st.info("No test results yet. Run `python run_tests.py` in the terminal.")
    else:
        latest = files[-1]
        results = pd.read_csv(latest, encoding="utf-8-sig").fillna("")
        n_pass = (results["result"] == "PASS").sum()
        st.write(f"Latest run: `{os.path.basename(latest)}` · "
                 f"**{n_pass} of {len(results)}** tests passed")
        by_type = results.groupby("type")["result"].apply(
            lambda s: f"{(s == 'PASS').sum()} of {len(s)}")
        st.dataframe(by_type.rename("passed"))
        failed = results[results["result"] != "PASS"]
        if len(failed):
            st.warning(f"{len(failed)} tests did not pass:")
            st.dataframe(failed[["test_id", "input", "expected", "got", "result"]], hide_index=True)
        with st.expander("All test results"):
            st.dataframe(results, hide_index=True)

    extra = sorted(glob.glob("results/extra_results_*.csv"))
    if extra:
        st.subheader("🧪 Extra tests: dialect, trick questions and routing")
        results = pd.read_csv(extra[-1], encoding="utf-8-sig").fillna("")
        n_pass = (results["result"] == "PASS").sum()
        st.write(f"Latest run: `{os.path.basename(extra[-1])}` · "
                 f"**{n_pass} of {len(results)}** tests passed")
        by_type = results.groupby("type")["result"].apply(
            lambda s: f"{(s == 'PASS').sum()} of {len(s)}")
        st.dataframe(by_type.rename("passed"))
        with st.expander("All extra test results"):
            st.dataframe(results, hide_index=True)

    st.divider()
    st.subheader("Retrieval comparison on the sample FAQ")
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
    st.dataframe(pd.DataFrame(rows), hide_index=True)


# =====================================================================
# Sidebar and navigation
# =====================================================================
def change_track():
    st.session_state.role = None


def render_sidebar():
    role = st.session_state.role
    with st.sidebar:
        name = st.session_state.name
        st.markdown(f"### {t('hi_name', name=name) if name else t('hi')}")
        st.markdown(f"{ROLE_ICON[role]} **{role_name(role)}**")
        pct = completion_percent(get_activities(data, role, st.session_state))
        st.progress(pct / 100, text=t("progress_short", pct=pct))
        st.button(t("change_track"), on_click=change_track, icon=":material/swap_horiz:",
                  width="stretch")
        st.divider()
        language_switch()
        text_size_switch()
        st.divider()
        st.caption(t("disclaimer"))


load_css()

if st.session_state.role is None:
    navigation = st.navigation(
        [st.Page(welcome_page, title=t("nav_welcome"), icon=":material/waving_hand:", default=True)],
        position="hidden",
    )
else:
    PAGES = {
        "home": st.Page(home_page, title=t("nav_home"), icon=":material/home:", default=True),
        "assistant": st.Page(assistant_page, title=t("nav_assistant"), icon=":material/chat:"),
        "scenarios": st.Page(scenarios_page, title=t("nav_scenarios"), icon=":material/theater_comedy:"),
        "plan": st.Page(plan_page, title=t("nav_plan"), icon=":material/calendar_month:"),
        "progress": st.Page(progress_page, title=t("nav_progress"), icon=":material/insights:"),
        "data": st.Page(data_page, title=t("nav_data"), icon=":material/database:"),
    }
    navigation = st.navigation(list(PAGES.values()))
    render_sidebar()

navigation.run()
