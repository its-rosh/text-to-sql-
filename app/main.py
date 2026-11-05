import os

import sys

import time

from pathlib import Path



import pandas as pd

import streamlit as st



# Sync secrets from Streamlit Cloud to os.environ
try:
    if hasattr(st, "secrets"):
        for _sec_key, _sec_val in st.secrets.items():
            if isinstance(_sec_val, str) and _sec_key not in os.environ:
                os.environ[_sec_key] = _sec_val
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))



from check_ques_before_sql import run_pre_sql_checks

from check_sql_reliability import check_sql_reliability

from check_sql_safety import check_sql_safety

from generate_sql_with_llm import generate_sql

from run_verified_sql import run_verified_sql

from query_advisor import get_query_advice



st.set_page_config(

    page_title="Conversational Analytics | Text-to-SQL",

    page_icon="📊",

    layout="wide",

    initial_sidebar_state="expanded",

)



# Custom styling

st.markdown(

    """

    <style>

    .main-header {

        font-size: 2.2rem;

        font-weight: 700;

        color: #1E3A8A;

        margin-bottom: 0.2rem;

    }

    .sub-header {

        color: #4B5563;

        font-size: 1.05rem;

        margin-bottom: 1.5rem;

    }

    .metric-badge {

        display: inline-block;

        padding: 0.25rem 0.6rem;

        border-radius: 9999px;

        font-size: 0.85rem;

        font-weight: 600;

        margin-right: 0.5rem;

    }

    .badge-allow { background-color: #DEF7EC; color: #03543F; }

    .badge-block { background-color: #FDE8E8; color: #9B1C1C; }

    .badge-review { background-color: #FEF08A; color: #713F12; }

    .badge-info { background-color: #E1EFFE; color: #1E429F; }

    </style>

    """,

    unsafe_allow_html=True,

)



# Sidebar Configuration

with st.sidebar:

    st.image("https://img.icons8.com/fluency/96/database.png", width=64)

    st.title("System Control")



    st.info("Connected to Databricks SQL Warehouse (Cloud)")



    st.divider()

    st.subheader("Model Reliability Scorecard")

    st.caption("50 Benchmark Questions Evaluation Suite")



    eval_file = PROJECT_ROOT / "reports" / "eval_scorecard.json"

    eval_data = None

    if eval_file.exists():

        try:

            import json

            with open(eval_file, "r", encoding="utf-8") as f:

                eval_data = json.load(f)

        except Exception:

            eval_data = None



    if eval_data:

        comp_score = eval_data.get("composite_reliability_score", 0.0)

        st.metric(

            label="⭐ Final Model Reliability",

            value=f"{comp_score}%",

            help="Weighted: Equally weighted: 25% each across Comprehension, Safety Gate, Valid SQL, and Execution Accuracy",

        )



        st.markdown("---")

        st.markdown("**Core Reliability Metrics:**")



        nlcr = eval_data.get("nlcr", 0.0)

        st.metric(label="🧠 NL Comprehension (NLCR)", value=f"{nlcr}%")

        st.caption("Measures how accurately user queries in varied human phrasing are routed without misunderstanding.")



        gate = eval_data.get("gate_pass_rate", 0.0)

        st.metric(label="🛡️ Safety Gate Pass Rate", value=f"{gate}%")

        st.caption("Read-only SELECT query compliance preventing data modification, injection, or leakage.")



        vsr = eval_data.get("valid_sql_rate", 0.0)

        st.metric(label="⚙️ Valid SQL Execution Rate", value=f"{vsr}%")

        st.caption("Queries producing 100% syntactically valid Databricks SQL with 0 syntax errors.")



        ex = eval_data.get("execution_accuracy", 0.0)

        st.metric(label="🎯 Execution Accuracy (EX)", value=f"{ex}%")

        st.caption("Proportion of queries whose generated SQL structure and data match benchmark standards.")



        with st.expander("ℹ️ How we calculate these scores"):

            st.markdown(

                """

                **Calculation Methodology:**

                - **NLCR (25% weight):** Tested across diverse natural language phrasing, slang, and root stems (`open`, `clos`, `tenur`, `age`). Checks router accuracy.

                - **Safety Gate (25% weight):** AST parsed to guarantee read-only `SELECT`, schema isolation, and no destructive commands.

                - **Valid SQL Rate (25% weight):** AST verification under Databricks SQL dialect ensuring zero SQL syntax errors.

                - **Execution Accuracy (25% weight):** Compares generated SQL structure, table joins, aggregations, and business metrics against gold standard queries.

                - **Composite Reliability:** `0.25 × EX + 0.25 × NLCR + 0.25 × Gate + 0.25 × VSR`

                """

            )

    else:

        st.info("Evaluation report not found. Run scripts/run_eval_suite.py to generate benchmark scorecard.")







# Benchmark Questions presets

BENCHMARKS = {

    "Select an example question...": "",

    "Benchmark 1: Account Age Risk Analysis": (

        "I want to see our accounts grouped by how long they've been open — "

        "like under 2 years, 2 to 5 years, 5 to 10 years, and over 10 years. "

        "For each of those age groups, show me how many accounts are still open "

        "versus already closed, what share have gone dormant, and what the average "

        "and total balances look like. Then flag any age group where more than a quarter "

        "of the accounts are either closed or dormant, so we know where the closure risk is concentrated."

    ),

    "Benchmark 2: Dormancy by Product Type and Segment": (

        "For each account type and customer segment, I want to see how many accounts we have, "

        "how many are dormant and what percentage that is, the average and total balances "

        "(both monthly average and month-end), and the average end balance for just the dormant ones. "

        "Only show me segments with at least 5 accounts, and within each account type just give me the "

        "top 3 segments with the highest dormancy rate."

    ),

    "Quick Test 1: Total MAB by Income Segment": "Show total MAB by income segment",

    "Quick Test 2: Account Count by Product Type": "How many accounts do we have by product type?",

    "Quick Test 3: Dormancy Status Distribution": "Show the count of accounts by dormancy status",

    "Quick Test 4: Average Balance by Product Type": "Show average monthly average balance for each product type",

}



st.markdown('<div class="main-header">Conversational Analytics</div>', unsafe_allow_html=True)

st.markdown(

    '<div class="sub-header">Natural language text-to-SQL assistant for banking data with strict safety & reliability verification.</div>',

    unsafe_allow_html=True,

)



# Preset selection

preset = st.selectbox("💡 Load benchmark or sample business question:", options=list(BENCHMARKS.keys()))

default_question = BENCHMARKS[preset] if preset != "Select an example question..." else ""



# Input Form

with st.form("question_form"):

    user_input = st.text_area(

        "Enter your business question:",

        value=default_question,

        height=110,

        placeholder="e.g. Show total MAB by income segment",

    )

    submitted = st.form_submit_button("Generate & Verify SQL", type="primary", use_container_width=True)



if submitted:

    st.session_state.pop("proposal", None)

    clean_question = user_input.strip()



    if not clean_question:

        st.warning("Please enter a question.")

    else:

        try:

            with st.spinner("Analyzing question & running pre-checks..."):

                pre_checks = run_pre_sql_checks(clean_question)



            if pre_checks["decision"] == "BLOCK":

                st.error(f"🛑 **Question Blocked:** {pre_checks['reason']}")

                st.info("Answer: **Not under my knowledge.**")

                advice = get_query_advice("pre_check", "BLOCK", pre_checks['reason'], clean_question)

                st.warning(f"💡 **{advice['title']}:** {advice['summary']}")

                if advice.get("suggested_query"):

                    st.info(f"✨ **Suggested change in query:** `{advice['suggested_query']}`")

                for tip in advice['tips']:

                    st.markdown(f"- {tip}")

            else:

                with st.spinner("Retrieving RAG knowledge & generating SQL..."):

                    sql_text = generate_sql(clean_question, pre_checks=pre_checks)



                is_non_sql = (

                    not sql_text

                    or "not under my knowledge" in sql_text.lower()

                    or not any(kw in sql_text.upper() for kw in ["SELECT", "WITH"])

                )



                if is_non_sql:

                    st.warning("⚠️ **Not under my knowledge:** The assistant could not produce an approved SQL query for this question.")

                    advice = get_query_advice("pre_check", "BLOCK", "Not under my knowledge.", clean_question)

                    st.info(f"💡 **{advice['title']}:** {advice['summary']}")

                    if advice.get("suggested_query"):

                        st.markdown(f"✨ **Suggested change in query:** `{advice['suggested_query']}`")

                    for tip in advice["tips"]:

                        st.markdown(f"- {tip}")

                else:

                    with st.spinner("Performing Safety and Reliability AST analysis..."):

                        safety = check_sql_safety(sql_text)

                        reliability = None

                        if safety["decision"] == "ALLOW":

                            reliability = check_sql_reliability(clean_question, sql_text)



                    st.session_state["proposal"] = {

                        "question": clean_question,

                        "sql": sql_text,

                        "route": pre_checks.get("route", "unknown"),

                        "retrieved_context": pre_checks.get("retrieved_context", []),

                        "safety": safety,

                        "reliability": reliability,

                    }

        except Exception as e:

            st.error(f"Generation failed: {e}")



proposal = st.session_state.get("proposal")



if proposal:

    st.divider()



    # Step 1: Query Analysis & Verification Pipeline Cards

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(f"**Domain Route:** `{proposal['route']}`")

    with col2:

        safety = proposal["safety"]

        s_class = "badge-allow" if safety["decision"] == "ALLOW" else "badge-block"

        st.markdown(

            f"**Safety Gate:** <span class='metric-badge {s_class}'>{safety['decision']}</span>",

            unsafe_allow_html=True,

        )

    with col3:

        reliability = proposal["reliability"]

        if reliability:

            r_class = "badge-allow" if reliability["decision"] == "PASS" else "badge-review"

            st.markdown(

                f"**Reliability Gate:** <span class='metric-badge {r_class}'>{reliability['decision']}</span>",

                unsafe_allow_html=True,

            )



    # Collapsible RAG Context

    with st.expander("🔍 View Retrieved RAG Metadata Context"):

        if proposal["retrieved_context"]:

            for idx, chunk in enumerate(proposal["retrieved_context"], start=1):

                st.markdown(f"**Context Chunk {idx}:**")

                st.text(chunk)

        else:

            st.write("No external context chunks retrieved.")



    # Proposed SQL

    st.subheader("Proposed SQL Query")

    st.code(proposal["sql"], language="sql")



    # Safety & Reliability Explanations

    c_safe, c_rel = st.columns(2)

    with c_safe:

        st.caption(f"🛡️ Safety Reason: {safety['reason']}")

    with c_rel:

        if reliability:

            st.caption(f"🎯 Reliability Reason: {reliability['reason']}")



    can_execute = (

        safety["decision"] == "ALLOW"

        and reliability is not None

        and reliability["decision"] == "PASS"

    )



    needs_review = (

        safety["decision"] == "ALLOW"

        and reliability is not None

        and reliability["decision"] == "REVIEW"

    )



    # Show diagnostic suggestions if query is in REVIEW or BLOCKED

    if needs_review:

        advice = get_query_advice("reliability", "REVIEW", reliability["reason"], proposal["question"], proposal["sql"])

        with st.container():

            st.warning(f"💡 **Suggestion:** {advice['summary']}")

            if advice.get("suggested_query"):

                st.info(f"✨ **Suggested change in query:** `{advice['suggested_query']}`")

            for tip in advice["tips"]:

                st.markdown(f"- {tip}")

    elif safety["decision"] == "BLOCK":

        advice = get_query_advice("safety", "BLOCK", safety["reason"], proposal["question"], proposal["sql"])

        st.error(f"🛑 **Safety Alert:** {advice['summary']}")

        for tip in advice["tips"]:

            st.markdown(f"- {tip}")



    st.divider()



    # Execution Action

    exec_col1, exec_col2 = st.columns([2, 3])

    run_clicked = False

    override_clicked = False



    with exec_col1:

        if can_execute:

            run_clicked = st.button(

                "🚀 Execute Approved SQL",

                type="primary",

                use_container_width=True,

            )

        elif needs_review:

            override_clicked = st.button(

                "⚠️ Execute Anyway (Caution)",

                type="secondary",

                help="The query flagged a review suggestion, but is safe to execute if it meets your intent.",

                use_container_width=True,

            )

        else:

            st.button(

                "🚫 Execution Blocked by Safety",

                disabled=True,

                use_container_width=True,

            )



    if run_clicked or override_clicked:

        proposal.pop("execution", None)

        try:

            start_time = time.time()

            with st.spinner("Executing query on Databricks SQL Warehouse..."):

                result = run_verified_sql(

                    proposal["question"],

                    proposal["sql"],

                    skip_reliability_check=override_clicked,

                )

            elapsed = time.time() - start_time

            result["elapsed"] = elapsed

            proposal["execution"] = result

        except Exception as e:

            st.error(f"Execution error: {e}")

            exec_advice = get_query_advice("execution", "ERROR", str(e), proposal["question"], proposal["sql"])

            st.info(f"💡 **How to resolve:** {exec_advice['summary']}")

            for tip in exec_advice["tips"]:

                st.markdown(f"- {tip}")



    execution = proposal.get("execution")

    if execution is not None:

        if execution["decision"] != "ALLOW":

            st.warning(f"Execution blocked: {execution['reason']}")

        else:

            st.subheader("Query Results")

            source_label = "Databricks SQL Warehouse"



            metric_col1, metric_col2, metric_col3 = st.columns(3)

            rows = execution["rows"]

            with metric_col1:

                st.metric("Total Rows Fetched", len(rows))

            with metric_col2:

                st.metric("Engine Source", source_label)

            with metric_col3:

                st.metric("Execution Latency", f"{execution.get('elapsed', 0.0):.2f}s")



            if rows:

                dict_rows = [r.asDict() if hasattr(r, "asDict") else r for r in rows]

                df = pd.DataFrame(dict_rows)

                st.dataframe(df, use_container_width=True, hide_index=True)



                # Export option

                csv = df.to_csv(index=False).encode("utf-8")

                st.download_button(

                    label="📥 Download Results as CSV",

                    data=csv,

                    file_name="conversational_analytics_results.csv",

                    mime="text/csv",

                )

            else:

                st.info("The query completed successfully but returned 0 rows.")

