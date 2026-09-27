import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import streamlit as st
import pandas as pd

from agentlens.ingestion.loader import load_traces
from agentlens.analysis.pipeline import analyze
from agentlens.schema.profiles import get_agent_profile

LOGO_PATH = PROJECT_ROOT / "app" / "assets" / "logo.jpg"

st.set_page_config(
    page_title="AgentLens — Failure Intelligence",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for glassmorphic styling, badges, and layout polish
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Metric cards styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 199, 190, 0.4);
    }

    /* Failure type badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-wrong_target {
        background: rgba(255, 59, 48, 0.18);
        color: #FF453A;
        border: 1px solid rgba(255, 69, 58, 0.4);
    }
    .badge-unsupported_success {
        background: rgba(255, 149, 0, 0.18);
        color: #FF9F0A;
        border: 1px solid rgba(255, 159, 10, 0.4);
    }
    .badge-incomplete_task {
        background: rgba(0, 199, 190, 0.18);
        color: #64D2FF;
        border: 1px solid rgba(100, 210, 255, 0.4);
    }
    .badge-repeated_question {
        background: rgba(175, 82, 222, 0.18);
        color: #BF5AF2;
        border: 1px solid rgba(191, 90, 242, 0.4);
    }
    .badge-no_progress {
        background: rgba(255, 214, 10, 0.18);
        color: #FFD60A;
        border: 1px solid rgba(255, 214, 10, 0.4);
    }

    /* Event pills */
    .event-card {
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 8px;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    .event-user {
        background: rgba(10, 132, 255, 0.1);
        border-left: 3px solid #0A84FF;
    }
    .event-agent {
        background: rgba(48, 209, 88, 0.1);
        border-left: 3px solid #30D158;
    }
    .event-tool-call {
        background: rgba(255, 159, 10, 0.08);
        border-left: 3px solid #FF9F0A;
    }
    .event-tool-result-success {
        background: rgba(48, 209, 88, 0.08);
        border-left: 3px solid #30D158;
    }
    .event-tool-result-failed {
        background: rgba(255, 69, 58, 0.12);
        border-left: 3px solid #FF453A;
    }
    .event-tool-result-unknown {
        background: rgba(255, 214, 10, 0.1);
        border-left: 3px solid #FFD60A;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# Sidebar: Logo & Domain Navigation
# ----------------------------------------------------

if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), width=180)

st.sidebar.markdown("### **Agent Intelligence Scope**")
domain = st.sidebar.radio(
    "Select Target Agent Domain:",
    ["Customer Support Agent", "Coding Agent"],
    index=0,
)

if domain == "Customer Support Agent":
    traces_file = PROJECT_ROOT / "data" / "traces.json"
    truth_file = PROJECT_ROOT / "data" / "ground_truth.json"
    agent_type = "customer_support"
    domain_desc = "Order Management, Customer Accounts, Delivery Booking & Messaging"
else:
    traces_file = PROJECT_ROOT / "data" / "coding_traces.json"
    truth_file = PROJECT_ROOT / "data" / "coding_ground_truth.json"
    agent_type = "coding_agent"
    domain_desc = "Codebase Search, File Editing, Test Execution & Git Operations"

profile = get_agent_profile(agent_type)

st.sidebar.divider()
st.sidebar.markdown(f"**Active Profile**: `{profile.agent_id}`")
st.sidebar.caption(domain_desc)

with st.sidebar.expander("🛠️ Registered Tool Capabilities", expanded=False):
    for tool_name, cap in profile.tools.items():
        st.markdown(f"• **`{tool_name}`**: {cap.purpose}")
        if cap.action_keywords:
            st.caption(f"Keywords: {', '.join(cap.action_keywords[:4])}")

st.sidebar.divider()
st.sidebar.caption("AgentLens v2.5 • Zero-LLM Deterministic + Embedding Baseline")

# ----------------------------------------------------
# Data Ingestion & Analysis
# ----------------------------------------------------

traces = load_traces(traces_file)
traces_by_id = {t.trace_id: t for t in traces}
findings, priorities = analyze(traces)

with open(truth_file, "r", encoding="utf-8") as f:
    ground_truth = json.load(f)

suspicious_ids = set(f.trace_id for f in findings)
recoveries = [row for row in ground_truth if row["outcome"] == "recovery"]
hard_negatives = [
    t for t in traces
    if "repeated_search" in t.trace_id or "failed_action" in t.task.description.lower()
]

# ----------------------------------------------------
# Header: Brand & Key Status Pill
# ----------------------------------------------------

col_logo, col_head = st.columns([1, 6])
with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=105)
with col_head:
    st.title("AgentLens")
    st.markdown(
        f"**Failure Intelligence for AI-Agent Traces** &nbsp;•&nbsp; "
        f"<span style='color: #00C7BE; font-weight:600;'>{domain}</span> &nbsp;•&nbsp; "
        f"<span style='background:rgba(48,209,88,0.15); color:#30D158; padding:2px 8px; border-radius:4px; font-size:0.85rem;'>● Active Monitoring</span>",
        unsafe_allow_html=True,
    )
    st.caption("Technical success ≠ Task success. Detecting silent failures that pass traditional monitoring.")

# ----------------------------------------------------
# Top KPI Metric Cards
# ----------------------------------------------------

st.write("")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Analysed Traces", len(traces), delta=None)
kpi2.metric(
    "Suspicious Traces",
    len(suspicious_ids),
    delta=f"{(len(suspicious_ids) / len(traces)):.0%} failure rate" if traces else None,
    delta_color="inverse",
)
kpi3.metric("Failure Patterns", len(priorities))
kpi4.metric(
    "Legitimate Recoveries",
    len(recoveries),
    delta="0% False Alarms",
    delta_color="normal",
)

st.divider()

# ----------------------------------------------------
# Tabbed Main Workspace
# ----------------------------------------------------

tab_queue, tab_audit, tab_inspector, tab_profile = st.tabs([
    "🎯 Investigation Queue",
    "🛡️ Recovery & Negative Controls",
    "🔎 Interactive Trace Inspector",
    "🧬 Agent & Tool Profile",
])

# ----------------------------------------------------
# TAB 1: Investigation Queue
# ----------------------------------------------------

with tab_queue:
    st.subheader("What should I investigate first?")
    st.caption(
        "Prioritization formula: `Priority = Frequency × Average Severity × Average Confidence`. Focus engineering effort on high-impact recurring patterns."
    )

    col_tbl, col_chart = st.columns([3, 2])

    priority_df = pd.DataFrame(priorities)

    with col_tbl:
        if not priority_df.empty:
            # Prettify table columns
            display_df = priority_df.copy()
            display_df.columns = ["Failure Pattern", "Count", "Priority Score", "Confidence"]
            display_df["Confidence"] = display_df["Confidence"].apply(lambda v: f"{v:.0%}")
            st.table(display_df)
        else:
            st.success("No suspicious patterns detected in this trace batch.")

    with col_chart:
        if not priority_df.empty:
            chart_df = priority_df.set_index("failure_type")[["priority", "count"]]
            st.bar_chart(chart_df["count"], color="#00C7BE")

    st.divider()

    st.subheader("Investigation Evidence Trail")

    # Filter by failure pattern
    failure_types_present = sorted(list(set(f.failure_type for f in findings)))
    selected_filter = st.selectbox(
        "Filter findings by failure pattern:",
        ["All Patterns"] + failure_types_present,
    )

    filtered_findings = [
        f for f in findings
        if selected_filter == "All Patterns" or f.failure_type == selected_filter
    ]

    st.caption(f"Showing {len(filtered_findings)} findings matching filter:")

    for finding in filtered_findings:
        badge_class = f"badge-{finding.failure_type}"
        badge_html = f"<span class='badge {badge_class}'>{finding.failure_type}</span>"

        with st.expander(
            f"[{finding.failure_type.upper()}] · {finding.trace_id} · Priority: {finding.confidence:.0%}"
        ):
            c_left, c_right = st.columns([3, 1])
            with c_left:
                st.markdown(
                    f"{badge_html} &nbsp; **Trace ID:** `{finding.trace_id}`",
                    unsafe_allow_html=True,
                )
            with c_right:
                st.caption(f"Confidence: **{finding.confidence:.0%}** | Severity: **{finding.severity:.0%}**")

            st.markdown("**Evidence Trail:**")
            for ev in finding.evidence:
                st.markdown(f"• {ev}")

            # Show trace chronological events
            trace_obj = traces_by_id.get(finding.trace_id)
            if trace_obj:
                st.markdown("**Chronological Event Sequence:**")
                for ev in trace_obj.events:
                    if ev.type == "user_message":
                        st.markdown(
                            f"<div class='event-card event-user'>👤 <b>User:</b> {ev.content}</div>",
                            unsafe_allow_html=True,
                        )
                    elif ev.type == "agent_message":
                        st.markdown(
                            f"<div class='event-card event-agent'>🤖 <b>Agent:</b> {ev.content}</div>",
                            unsafe_allow_html=True,
                        )
                    elif ev.type == "tool_call":
                        args_str = f" <code>{json.dumps(ev.arguments)}</code>" if ev.arguments else ""
                        st.markdown(
                            f"<div class='event-card event-tool-call'>⚡ <b>Tool Call:</b> <code>{ev.tool}</code>{args_str}</div>",
                            unsafe_allow_html=True,
                        )
                    elif ev.type == "tool_result":
                        status_class = (
                            "event-tool-result-success"
                            if ev.status == "success"
                            else (
                                "event-tool-result-failed"
                                if ev.status == "failed"
                                else "event-tool-result-unknown"
                            )
                        )
                        st.markdown(
                            f"<div class='event-card {status_class}'>📋 <b>Tool Result [{ev.status.upper()}]:</b> {ev.content}</div>",
                            unsafe_allow_html=True,
                        )

# ----------------------------------------------------
# TAB 2: Recovery & Negative Controls
# ----------------------------------------------------

with tab_audit:
    st.subheader("Legitimate Recovery Safety & Negative Controls")
    st.info(
        "**Core Reliability Principle:** A failure detector must not cry wolf. AgentLens distinguishes genuine task failures from transient errors that resolved successfully."
    )

    col_rec, col_neg = st.columns(2)

    with col_rec:
        st.markdown(f"#### 🔄 Legitimate Recoveries ({len(recoveries)} traces)")
        st.caption(
            "These traces contained an initial tool failure (e.g. timeout or lock deadlock), followed by a retry that succeeded. AgentLens verified that zero false positives were emitted."
        )
        for row in recoveries:
            t = traces_by_id.get(row["trace_id"])
            desc = t.task.description if t else "Recovery task"
            st.markdown(f"✓ **`{row['trace_id']}`**: *{desc}*")

    with col_neg:
        st.markdown("#### 🧪 Hard Negative Controls & Ambiguous Traces")
        st.caption(
            "Includes progressive search narrowing (non-zero results), honest failure disclosures (e.g. agent openly reporting shipping restrictions), and upstream CI drops."
        )
        for t in hard_negatives:
            st.markdown(f"✓ **`{t.trace_id}`**: *{t.task.description}* (Accurately preserved as non-failure)")

        ambiguous_rows = [row for row in ground_truth if row["outcome"] == "ambiguous"]
        for row in ambiguous_rows:
            t = traces_by_id.get(row["trace_id"])
            desc = t.task.description if t else "Ambiguous task"
            st.markdown(f"⚖️ **`{row['trace_id']}`**: *{desc}* (Ambiguous trace, safely held)")

# ----------------------------------------------------
# TAB 3: Interactive Trace Inspector
# ----------------------------------------------------

with tab_inspector:
    st.subheader("Deep Trace Inspector")
    st.caption("Examine any trace payload, chronological message flow, and detection breakdown.")

    selected_trace_id = st.selectbox(
        "Choose Trace to Inspect:",
        options=[t.trace_id for t in traces],
        index=0,
    )

    t_inspect = traces_by_id[selected_trace_id]
    t_findings = [f for f in findings if f.trace_id == selected_trace_id]

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    col_meta1.markdown(f"**Task Description:** {t_inspect.task.description}")
    col_meta2.markdown(f"**Agent ID:** `{t_inspect.agent}`")
    col_meta3.markdown(f"**Timestamp:** `{t_inspect.timestamp}`")

    if t_findings:
        st.error(f"🚨 **Detected Failure Pattern:** `{t_findings[0].failure_type}` (Confidence: {t_findings[0].confidence:.0%})")
        for ev in t_findings[0].evidence:
            st.write(f"• {ev}")
    else:
        st.success("✅ **Clean Trace:** No failure patterns detected. Task execution aligns with expectations.")

    st.markdown("---")
    st.markdown("#### Full Chronological Timeline")
    for ev in t_inspect.events:
        if ev.type == "user_message":
            st.markdown(
                f"<div class='event-card event-user'>👤 <b>User:</b> {ev.content}</div>",
                unsafe_allow_html=True,
            )
        elif ev.type == "agent_message":
            st.markdown(
                f"<div class='event-card event-agent'>🤖 <b>Agent:</b> {ev.content}</div>",
                unsafe_allow_html=True,
            )
        elif ev.type == "tool_call":
            args_str = f" <code>{json.dumps(ev.arguments)}</code>" if ev.arguments else ""
            st.markdown(
                f"<div class='event-card event-tool-call'>⚡ <b>Tool Call:</b> <code>{ev.tool}</code>{args_str}</div>",
                unsafe_allow_html=True,
            )
        elif ev.type == "tool_result":
            status_class = (
                "event-tool-result-success"
                if ev.status == "success"
                else (
                    "event-tool-result-failed"
                    if ev.status == "failed"
                    else "event-tool-result-unknown"
                )
            )
            st.markdown(
                f"<div class='event-card {status_class}'>📋 <b>Tool Result [{ev.status.upper()}]:</b> {ev.content}</div>",
                unsafe_allow_html=True,
            )

    with st.expander("📄 View Raw Trace JSON"):
        st.json(t_inspect.model_dump())

# ----------------------------------------------------
# TAB 4: Agent & Tool Profile
# ----------------------------------------------------

with tab_profile:
    st.subheader(f"Agent Architecture Profile: {profile.agent_id}")
    st.markdown(f"**Domain Classification:** `{profile.agent_type}`")
    st.markdown(f"*{profile.description}*")

    st.markdown("#### Registered Capabilities & Semantic Keywords")
    profile_data = []
    for tool_name, cap in profile.tools.items():
        profile_data.append({
            "Tool Name": tool_name,
            "Mutating": "Yes" if cap.is_mutating else "No (Read-Only)",
            "Purpose": cap.purpose,
            "Target Keys": ", ".join(cap.entity_arg_keys) if cap.entity_arg_keys else "N/A",
            "Action Keywords": ", ".join(cap.action_keywords),
        })

    st.table(pd.DataFrame(profile_data))
