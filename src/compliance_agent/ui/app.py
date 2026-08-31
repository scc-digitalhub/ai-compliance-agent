"""
AI Compliance Agent — Streamlit UI

Run with:
    streamlit run src/main/python/compliance_agent/ui/app.py
"""
from __future__ import annotations

import json
import textwrap
from typing import Any

import httpx
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Compliance Agent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚖️ AI Compliance Agent")
    st.markdown("---")
    api_url = st.text_input("API Base URL", value="http://localhost:8000")
    with st.expander("⚙️ LLM Provider", expanded=False):
        st.caption(
            "Set the provider on the API server via `.env`. "
            "This panel shows the current selection read from the API."
        )
        try:
            import httpx as _hx
            cfg = _hx.get(f"{api_url.rstrip('/')}/health", timeout=2).json()
            st.success(f"API reachable — {cfg.get('status', '?')}")
        except Exception:
            st.warning("API unreachable")
    st.markdown("---")
    st.markdown(
        "**About**\n\n"
        "This agent navigates the OKF compliance bundle to help you:\n\n"
        "1. Define a **ComplianceContext** for your project\n"
        "2. Analyse **dataset** compliance\n"
        "3. Analyse **model** compliance"
    )


# ── HTTP helper ───────────────────────────────────────────────────────────────
def post(endpoint: str, payload: dict) -> dict:
    url = f"{api_url.rstrip('/')}{endpoint}"
    with httpx.Client(timeout=300.0) as client:
        resp = client.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()


# ── Rendering helpers ─────────────────────────────────────────────────────────
def _card(title: str, body: str) -> None:
    st.markdown(
        f"""<div style="border:1px solid #ddd; border-radius:8px; padding:12px; margin:8px 0">
        <strong>{title}</strong><br><small>{body}</small></div>""",
        unsafe_allow_html=True,
    )


def _json_expander(label: str, data: Any) -> None:
    with st.expander(f"📄 {label} (JSON)", expanded=False):
        st.code(json.dumps(data, indent=2, default=str), language="json")


def _section(title: str, text: str) -> None:
    if text:
        st.subheader(title)
        st.markdown(text)


def _render_requirements(reqs: list[dict]) -> None:
    if not reqs:
        return
    st.subheader("📋 Applicable Requirements")
    for r in reqs:
        src = r.get("source", {})
        label = f"**{r.get('name', r.get('id', '?'))}** — {src.get('framework', '')} {src.get('article', '')}"
        with st.expander(label):
            st.write(r.get("summary") or r.get("requirement_text", ""))
            badge = r.get("applicability_status", "APPLICABLE")
            st.caption(f"Kind: `{r.get('kind', '?')}` | Status: `{badge}`")


def _render_groups(groups: list[dict], title: str = "Groups") -> None:
    if not groups:
        return
    st.subheader(f"👥 {title}")
    cols = st.columns(min(len(groups), 3))
    for i, g in enumerate(groups):
        with cols[i % 3]:
            _card(g.get("name", "?"), g.get("rationale") or g.get("description") or "")


def _render_attributes(attrs: list[dict]) -> None:
    if not attrs:
        return
    st.subheader("🔒 Protected Attributes")
    rows = [[
        a.get("name", "?"),
        a.get("semantic_type", "?"),
        a.get("attribute_role", "?"),
        ", ".join(a.get("use_permissions", [])),
    ] for a in attrs]
    st.table(
        {"Name": [r[0] for r in rows],
         "Semantic Type": [r[1] for r in rows],
         "Role": [r[2] for r in rows],
         "Permitted Uses": [r[3] for r in rows]}
    )


def _render_objectives(objectives: list[dict]) -> None:
    if not objectives:
        return
    st.subheader("🎯 Compliance Objectives")
    for obj in objectives:
        metric = obj.get("metric", {})
        cond   = obj.get("condition", {})
        cond_str = ""
        if cond.get("threshold"):
            t = cond["threshold"]
            cond_str = f"{t.get('operator', '?')} {t.get('value', '?')} {metric.get('unit', {}).get('symbol', '')}"
        elif cond.get("range"):
            r = cond["range"]
            cond_str = f"[{r.get('lower', '?')}, {r.get('upper', '?')}]"

        with st.expander(
            f"**{obj.get('name', '?')}** — "
            f"`{obj.get('priority', '?')}` | `{obj.get('severity', '?')}`"
        ):
            st.write(obj.get("description", ""))
            col1, col2 = st.columns(2)
            col1.metric("Metric", metric.get("name", "?"))
            col2.metric("Condition", cond_str or "—")
            if obj.get("rationale"):
                st.caption(obj["rationale"])
            if obj.get("requirements"):
                st.caption("Linked requirements: " + ", ".join(f"`{r}`" for r in obj["requirements"]))


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "1️⃣  Project Compliance Context",
    "2️⃣  Dataset Compliance",
    "3️⃣  Model Compliance",
])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Project Compliance Context
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.header("Project Compliance Context Builder")
    st.markdown(
        "Fill in the project details and the agent will identify the applicable "
        "regulations, requirements, affected groups, protected attributes, and risk level."
    )

    with st.form("project_form"):
        col1, col2 = st.columns(2)
        with col1:
            p_name   = st.text_input("Project Name", value="AI Loan Approval System")
            p_domain = st.text_input("Domain", value="finance")
            p_task   = st.selectbox(
                "AI Task",
                ["CLASSIFICATION", "REGRESSION", "GENERATION", "DETECTION",
                 "RANKING", "RECOMMENDATION", "FORECASTING", "DECISION_SUPPORT"],
                index=0,
            )
            p_goal = st.text_area(
                "Goal",
                value="Automate creditworthiness assessment for retail loan applications.",
                height=80,
            )
        with col2:
            p_purpose  = st.text_input("Purpose", value="Streamline credit decision-making for loan officers")
            p_audience = st.text_input("Audience", value="Retail banking customers and loan officers")
            p_deploy   = st.selectbox("Deployment", ["CLOUD", "EDGE", "EMBEDDED", "PREMISE"], index=0)
            p_env      = st.selectbox("Environment", ["PRODUCTION", "SANDBOX", "PILOT"], index=0)
            p_geo      = st.text_input("Geographies (comma-separated)", value="IT, EU")

        p_scope_in  = st.text_area("In-scope capabilities", value="Credit scoring, application screening", height=60)
        p_scope_out = st.text_area("Out-of-scope capabilities", value="Final lending decision, fraud investigation", height=60)

        submitted = st.form_submit_button("🔍 Analyse Compliance Context", type="primary")

    if submitted:
        payload = {
            "name": p_name, "domain": p_domain, "ai_task": p_task,
            "goal": p_goal, "purpose": p_purpose, "audience": p_audience,
            "deployment": p_deploy, "environment": p_env,
            "geography": [g.strip() for g in p_geo.split(",") if g.strip()],
            "scope_in":  [s.strip() for s in p_scope_in.split(",") if s.strip()],
            "scope_out": [s.strip() for s in p_scope_out.split(",") if s.strip()],
        }
        with st.spinner("🔎 Agent is navigating the OKF bundle…"):
            try:
                result = post("/compliance/context", payload)
                st.session_state["ctx_result"] = result
            except Exception as e:
                st.error(f"API error: {e}")

    if "ctx_result" in st.session_state:
        result = st.session_state["ctx_result"]
        st.success("✅ Compliance Context generated")

        _section("📝 Summary", result.get("narrative_summary", ""))
        _section("⚖️ Regulatory Analysis", result.get("regulatory_analysis", ""))
        _section("⚠️ Risk Analysis", result.get("risk_analysis", ""))
        _section("👁️ Oversight Analysis", result.get("oversight_analysis", ""))

        ctx = result.get("compliance_context", {})

        col1, col2, col3 = st.columns(3)
        rc = ctx.get("risk_classification") or {}
        col1.metric("Risk Level", rc.get("risk_level", "—"))
        col2.metric("Actor Role", ctx.get("actor_role", "—"))
        col3.metric("Environment", ctx.get("environment", "—"))

        regs = ctx.get("regulations", [])
        if regs:
            st.subheader("📚 Applicable Regulations")
            for reg in regs:
                st.badge(f"{reg.get('framework', '?')} {reg.get('article', '')}".strip())

        _render_requirements(ctx.get("requirements", []))
        _render_groups(ctx.get("affected_groups", []), "Affected Groups")
        _render_groups(ctx.get("vulnerable_groups", []), "Vulnerable Groups")
        _render_attributes(ctx.get("protected_attributes", []))

        misuse = ctx.get("foreseeable_misuse", [])
        if misuse:
            st.subheader("🚨 Foreseeable Misuse Scenarios")
            for m in misuse:
                with st.expander(f"**{m.get('name', '?')}** — Likelihood: `{m.get('likelihood', '?')}` Impact: `{m.get('impact', '?')}`"):
                    st.write(m.get("rationale", ""))

        _json_expander("Full ComplianceContext", ctx)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Dataset Compliance
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.header("Dataset Compliance Analyser")
    st.markdown(
        "Describe your dataset and the agent will identify protected attributes "
        "and propose concrete compliance objectives with metric thresholds."
    )

    with st.form("dataset_form"):
        col1, col2 = st.columns(2)
        with col1:
            d_name   = st.text_input("Dataset Name", value="loan_applications_2023")
            d_scope  = st.selectbox("Dataset Scope", ["TRAINING", "VALIDATION", "SUPPORT"], index=0)
            d_domain = st.text_input("Domain", value="finance")
            d_sens   = st.selectbox(
                "Sensitivity",
                ["NONE", "PII", "SENSITIVE", "RESTRICTED", "PROHIBITED"],
                index=1,
            )
            d_n      = st.number_input("Number of Records", value=120000, step=1000)
        with col2:
            d_desc = st.text_area(
                "Description",
                value="Historical retail loan application records with applicant demographics and credit outcomes.",
                height=80,
            )
            d_known_attrs = st.text_input(
                "Known Protected Attribute Fields (comma-separated)",
                value="gender, nationality, age, marital_status",
            )

        st.markdown("**Schema Fields** (name, dtype, sensitivity — one per line, tab/comma-separated)")
        d_schema_raw = st.text_area(
            "Schema",
            value=textwrap.dedent("""\
                applicant_id, STRING, NONE
                age, INT, PII
                gender, STRING, SENSITIVE
                nationality, STRING, SENSITIVE
                marital_status, STRING, PII
                income_annual, FLOAT, PII
                credit_score, INT, PII
                loan_amount, FLOAT, NONE
                loan_purpose, STRING, NONE
                outcome, INT, NONE
            """),
            height=160,
        )

        d_sample_raw = st.text_area(
            "Sample Records (JSON array of objects, optional)",
            value=json.dumps([
                {"applicant_id": "X001", "age": 34, "gender": "F", "nationality": "IT",
                 "income_annual": 38000, "credit_score": 680, "outcome": 1},
            ], indent=2),
            height=80,
        )

        submitted2 = st.form_submit_button("🔍 Analyse Dataset Compliance", type="primary")

    if submitted2:
        # Parse schema
        fields = []
        for line in d_schema_raw.strip().splitlines():
            parts = [p.strip() for p in line.replace("\t", ",").split(",")]
            if len(parts) >= 2:
                fields.append({
                    "name": parts[0], "dtype": parts[1],
                    "sensitivity": parts[2] if len(parts) > 2 else "NONE",
                    "nullable": True,
                })
        try:
            samples = json.loads(d_sample_raw) if d_sample_raw.strip() else []
        except Exception:
            samples = []

        payload = {
            "name": d_name, "description": d_desc, "scope": d_scope,
            "domain": d_domain, "sensitivity": d_sens, "n_records": int(d_n),
            "schema_fields": fields, "sample_records": samples,
            "known_protected_attributes": [
                a.strip() for a in d_known_attrs.split(",") if a.strip()
            ],
        }
        with st.spinner("🔎 Agent is analysing dataset compliance…"):
            try:
                result2 = post("/compliance/dataset", payload)
                st.session_state["ds_result"] = result2
            except Exception as e:
                st.error(f"API error: {e}")

    if "ds_result" in st.session_state:
        result2 = st.session_state["ds_result"]
        st.success("✅ Dataset compliance analysis complete")

        _section("📝 Summary", result2.get("narrative_summary", ""))
        _section("📊 Data Quality Analysis", result2.get("data_quality_analysis", ""))
        _section("🔒 Privacy Analysis", result2.get("privacy_analysis", ""))
        _section("⚖️ Fairness Analysis", result2.get("fairness_analysis", ""))

        _render_attributes(result2.get("protected_attributes", []))
        _render_objectives(result2.get("objectives", []))
        _json_expander("Full DataComplianceResponse", result2)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Model Compliance
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.header("Model Compliance Analyser")
    st.markdown(
        "Describe your model and the agent will propose compliance objectives "
        "covering fairness, robustness, transparency, calibration, and privacy."
    )

    with st.form("model_form"):
        col1, col2 = st.columns(2)
        with col1:
            m_name    = st.text_input("Model Name", value="credit_xgboost_v2")
            m_task    = st.selectbox(
                "AI Task",
                ["CLASSIFICATION", "REGRESSION", "GENERATION", "DETECTION",
                 "RANKING", "RECOMMENDATION", "DECISION_SUPPORT"],
                index=0,
            )
            m_fw      = st.selectbox(
                "Framework",
                ["SKLEARN", "PYTORCH", "TENSORFLOW", "XGBOOST", "HUGGINGFACE", "OTHER"],
                index=0,
            )
            m_domain  = st.text_input("Domain", value="finance")
        with col2:
            m_output  = st.selectbox(
                "Output Type",
                ["BINARY_CLASSIFICATION", "MULTI_CLASS", "REGRESSION",
                 "GENERATION", "RANKING"],
                index=0,
            )
            m_prob = st.checkbox("Produces Probabilities / Scores", value=True)
            m_sens = st.checkbox("Trained on Sensitive / Personal Data", value=True)
            m_groups = st.text_input(
                "Affected Groups (comma-separated)",
                value="retail banking customers, loan applicants",
            )

        m_desc = st.text_area(
            "Model Description",
            value="XGBoost binary classifier predicting loan approval probability from applicant financial profile.",
            height=80,
        )

        use_ctx = st.checkbox("Import requirements from Tab 1 analysis", value=True)
        submitted3 = st.form_submit_button("🔍 Analyse Model Compliance", type="primary")

    if submitted3:
        prior_reqs: list[dict] = []
        if use_ctx and "ctx_result" in st.session_state:
            ctx = st.session_state["ctx_result"].get("compliance_context", {})
            prior_reqs = ctx.get("requirements", [])

        payload = {
            "name": m_name, "description": m_desc,
            "ai_task": m_task, "domain": m_domain,
            "framework": m_fw, "output_type": m_output,
            "produces_probabilities": m_prob,
            "trained_on_sensitive_data": m_sens,
            "known_affected_groups": [g.strip() for g in m_groups.split(",") if g.strip()],
            "prior_requirements": prior_reqs,
        }
        with st.spinner("🔎 Agent is analysing model compliance…"):
            try:
                result3 = post("/compliance/model", payload)
                st.session_state["mdl_result"] = result3
            except Exception as e:
                st.error(f"API error: {e}")

    if "mdl_result" in st.session_state:
        result3 = st.session_state["mdl_result"]
        st.success("✅ Model compliance analysis complete")

        _section("📝 Summary", result3.get("narrative_summary", ""))
        _section("⚖️ Fairness Analysis", result3.get("fairness_analysis", ""))
        _section("🛡️ Robustness Analysis", result3.get("robustness_analysis", ""))
        _section("🔍 Transparency Analysis", result3.get("transparency_analysis", ""))

        _render_objectives(result3.get("objectives", []))
        _json_expander("Full ModelComplianceResponse", result3)
