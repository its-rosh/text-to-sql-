import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from generate_sql_with_llm import generate_sql
from check_sql_safety import check_sql_safety
from check_sql_reliability import check_sql_reliability
from run_verified_sql import run_verified_sql

st.set_page_config(page_title="Conversational Analytics", layout="wide")
st.title("Conversational Analytics")
st.caption("Dummy-data prototype")

with st.form("question_form"):
    question = st.text_area("Your question", height=120)
    submitted = st.form_submit_button("Generate SQL", type="primary")

if submitted:
    st.session_state.pop("proposal", None)
    question = question.strip()

    if not question:
        st.warning("Enter a question.")
    else:
        try:
            with st.spinner("Generating SQL..."):
                sql_text = generate_sql(question)

            if sql_text == "Not under my knowledge.":
                st.warning(sql_text)
            else:
                safety = check_sql_safety(sql_text)
                reliability = None

                if safety["decision"] == "ALLOW":
                    reliability = check_sql_reliability(question, sql_text)

                st.session_state["proposal"] = {
                    "question": question,
                    "sql": sql_text,
                    "safety": safety,
                    "reliability": reliability,
                }
        except Exception:
            st.error("Generation or checking failed. No query was executed.")

proposal = st.session_state.get("proposal")
if proposal:
    st.subheader("Submitted question")
    st.write(proposal["question"])
    st.subheader("Proposed SQL")
    st.code(proposal["sql"], language="sql")

    safety = proposal["safety"]
    st.write(f"Safety: {safety['decision']}")
    st.write(safety["reason"])

    reliability = proposal["reliability"]
    if reliability:
        st.write(f"Reliability: {reliability['decision']}")
        st.write(reliability["reason"])

    st.caption("Checks are limited. Review the submitted question and SQL.")

    can_execute = (
        safety["decision"] == "ALLOW"
        and reliability is not None
        and reliability["decision"] == "PASS"
    )

    if st.button("Run reviewed SQL", disabled=not can_execute):
        proposal.pop("execution", None)

        try:
            with st.spinner("Running query in Databricks..."):
                result = run_verified_sql(
                    proposal["question"],
                    proposal["sql"],
                )

            proposal["execution"] = result
        except Exception:
            st.error(
                "The query could not be completed. "
                "Check the connection and SQL before retrying."
            )

    execution = proposal.get("execution")
    if execution is not None:
        if execution["decision"] != "ALLOW":
            st.warning(execution["reason"])
        else:
            st.subheader("Database results")
            rows = execution["rows"]

            if rows:
                st.dataframe(
                    [row.asDict() for row in rows],
                    hide_index=True,
                )
                st.caption("Showing up to 20 rows; results may be incomplete.")
            else:
                st.info("The query returned no rows.")