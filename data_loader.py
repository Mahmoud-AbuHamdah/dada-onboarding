import os
import pandas as pd
import streamlit as st

DATA_DIR = "data"


def _data_version():
    """Return the last-modified time of every CSV file.
    If any file is edited, this value changes."""
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".csv"))
    return tuple(os.path.getmtime(os.path.join(DATA_DIR, f)) for f in files)


@st.cache_data
def _load_all_cached(version):
    """Load all CSV files. 'version' is only used so the cache
    refreshes when a file changes."""

    def read(filename):
        # utf-8-sig removes the hidden BOM character at the start of each file
        return pd.read_csv(f"{DATA_DIR}/{filename}", encoding="utf-8-sig")

    return {
        "kb": read("knowledge_base.csv"),
        "faq": read("sample_faq.csv"),
        "scenarios": read("role_scenarios.csv"),
        "plan": read("suggested_learning_plan.csv"),
        "quiz": read("sample_quiz.csv"),
        "jury": read("JURY_TEST_CASES.csv"),
    }


def load_all():
    """Load all data. Reloads automatically when any CSV file changes."""
    return _load_all_cached(_data_version())


def check_data(data):
    """Look for broken links between files. Returns a list of problems."""
    problems = []
    kb_ids = set(data["kb"]["id"])

    # 1. Every fact ID mentioned in the FAQ must exist in the knowledge base
    for _, row in data["faq"].iterrows():
        for kid in str(row["expected_knowledge_ids"]).split(";"):
            if kid.startswith("K") and kid not in kb_ids:
                problems.append(f"FAQ {row['id']} points to missing fact {kid}")

    # 2. Every quiz question's source must exist
    for _, row in data["quiz"].iterrows():
        if row["source_knowledge_id"] not in kb_ids:
            problems.append(
                f"Quiz {row['id']} points to missing fact {row['source_knowledge_id']}"
            )

    # 3. Each department needs at least one scenario and exactly 4 milestones
    for dept in ["Sales", "Delivery"]:
        n_scenarios = (data["scenarios"]["department"] == dept).sum()
        if n_scenarios == 0:
            problems.append(f"No scenarios for {dept}")

        n_milestones = (data["plan"]["department"] == dept).sum()
        if n_milestones != 4:
            problems.append(f"{dept} has {n_milestones} milestones, expected 4")

        # 4. Every scenario's company_value must be one of the five values
    values_rows = data["kb"][data["kb"]["topic"] == "Values"]
    valid_values = set(values_rows["keyword_en"])
    for _, row in data["scenarios"].iterrows():
        if row["company_value"] not in valid_values:
            problems.append(
                f"Scenario {row['id']} uses unknown value '{row['company_value']}'"
            )

    return problems