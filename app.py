import streamlit as st
import pandas as pd

st.title("Dada Group Academy")
st.write("Welcome! This is my first Streamlit page.")

# Load the knowledge base. "utf-8-sig" removes the hidden BOM character
# at the start of the file, which would otherwise break the "id" column name.
kb = pd.read_csv("data/knowledge_base.csv", encoding="utf-8-sig")

st.write(f"The knowledge base has {len(kb)} facts.")
st.dataframe(kb)

st.subheader("Facts per topic")
topic_counts = kb["topic"].value_counts()
st.write(topic_counts)
st.bar_chart(topic_counts)