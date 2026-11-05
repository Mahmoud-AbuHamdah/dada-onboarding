import streamlit as st
from data_loader import load_all, check_data

st.set_page_config(page_title="Dada Group Academy", page_icon="🎓")
st.title("Dada Group Academy")

data = load_all()

# Data health check
problems = check_data(data)
if problems:
    st.error("Data problems found:")
    for p in problems:
        st.write("- " + p)
else:
    st.success("All data files loaded and links checked: no problems found.")

# Show each file in its own tab
tabs = st.tabs(["Knowledge", "FAQ", "Scenarios", "Learning plan", "Quiz", "Jury tests"])
for tab, key in zip(tabs, ["kb", "faq", "scenarios", "plan", "quiz", "jury"]):
    with tab:
        st.write(f"{len(data[key])} rows")
        st.dataframe(data[key], hide_index=True)