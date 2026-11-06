import streamlit as st
from data_loader import load_all, check_data

st.set_page_config(page_title="Dada Group Academy", page_icon="🎓", layout="wide")

data = load_all()

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
    st.write("Coming in Steps 3-6: ask questions and get answers with sources.")

    # Which track did the user choose? (Sales or Delivery)
    role = st.session_state.role

    # Count the rows for that track in each file
    n_scenarios = (data["scenarios"]["department"] == role).sum()
    n_milestones = (data["plan"]["department"] == role).sum()

    st.write(
        f"Your {role} track has **{n_scenarios}** practice scenarios "
        f"and **{n_milestones}** learning milestones."
    )

def scenarios_page():
    st.header("🎭 Practice scenarios")
    st.write("Coming in Step 7.")


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