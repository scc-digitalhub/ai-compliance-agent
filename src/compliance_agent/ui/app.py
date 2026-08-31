"""
AI Compliance Agent — Streamlit UI

Run with:
    streamlit run src/compliance_agent/ui/app.py
"""
from __future__ import annotations

import json
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
    try:
        cfg = httpx.get(f"{api_url.rstrip('/')}/health", timeout=2).json()
        st.success(f"API reachable — {cfg.get('status', '?')}")
    except Exception:
        st.warning("API unreachable")
    st.markdown("---")
    st.markdown(
        "**About**\n\n"
        "This agent navigates the OKF compliance bundle to help you:\n\n"
        "1. Define a **ComplianceContext** for your project\n"
        "2. Analyse **dataset** compliance\n"
        "3. Analyse **model** compliance\n\n"
        "Manage entities via the [Swagger UI](%s/docs)." % api_url.rstrip("/")
    )


# ── HTTP helpers ──────────────────────────────────────────────────────────────
def _get(endpoint: str) -> Any:
    url = f"{api_url.rstrip('/')}{endpoint}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url)
    resp.raise_for_status()
    return resp.json()


def _post(endpoint: str) -> dict:
    url = f"{api_url.rstrip('/')}{endpoint}"
    with httpx.Client(timeout=300.0) as client:
        resp = client.post(url)
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
        metric  = obj.get("metric", {})
        cond    = obj.get("condition", {})
        cond_str = ""
        if cond.get("threshold"):
            t = cond["threshold"]
            cond_str = f"{t.get('operator', '?')} {t.get('value', '?')} {(metric.get('unit') or {}).get('symbol', '')}"
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


def _entity_selector(kind: str, label: str) -> dict | None:
    """Fetch entities of *kind* from the API and return the selected one, or None."""
    try:
        entities = _get(f"/entities/{kind}")
    except Exception as exc:
        st.error(f"Could not load {kind}: {exc}")
        return None
    if not entities:
        st.info(
            f"No {kind} found. Add JSON files to `data/{kind}/` or use the "
            f"[Swagger UI]({api_url.rstrip('/')}/docs) to create one."
        )
        return None
    options = {f"{e['name']}  ({e['id'][:8]}…)": e for e in entities}
    choice = st.selectbox(f"Select {label}", list(options.keys()), key=f"sel_{kind}")
    entity = options[choice]
    _json_expander(f"{label} details", entity)
    return entity


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
        "Select a project and the agent will identify the applicable regulations, "
        "requirements, affected groups, protected attributes, and risk level."
    )

    project = _entity_selector("projects", "Project")

    if project and st.button("🔍 Analyse Compliance Context", type="primary", key="btn_ctx"):
        with st.spinner("🔎 Agent is navigating the OKF bundle…"):
            try:
                result = _post(f"/compliance/context/{project['id']}")
                st.session_state["ctx_result"] = result
                st.session_state["ctx_project_id"] = project["id"]
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
                with st.expander(
                    f"**{m.get('name', '?')}** — "
                    f"Likelihood: `{m.get('likelihood', '?')}` Impact: `{m.get('impact', '?')}`"
                ):
                    st.write(m.get("rationale", ""))

        _json_expander("Full ComplianceContext", ctx)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Dataset Compliance
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.header("Dataset Compliance Analyser")
    st.markdown(
        "Select a dataset and the agent will identify protected attributes "
        "and propose concrete compliance objectives with metric thresholds."
    )

    dataset = _entity_selector("datasets", "Dataset")

    if dataset and st.button("🔍 Analyse Dataset Compliance", type="primary", key="btn_ds"):
        with st.spinner("🔎 Agent is analysing dataset compliance…"):
            try:
                result2 = _post(f"/compliance/dataset/{dataset['id']}")
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
        "Select a model and the agent will propose compliance objectives "
        "covering fairness, robustness, transparency, calibration, and privacy."
    )

    model = _entity_selector("models", "Model")

    st.markdown("**Optional: link a project** to provide prior regulatory context.")
    use_project = st.checkbox("Use project context from Tab 1", value=True, key="chk_proj")
    project_id_for_model: str | None = None
    if use_project and "ctx_project_id" in st.session_state:
        project_id_for_model = st.session_state["ctx_project_id"]
        st.caption(f"Will use project `{project_id_for_model[:8]}…` from Tab 1 analysis.")
    elif use_project:
        st.caption("Run Tab 1 first to load project context, or select a project below.")
        try:
            projs = _get("/entities/projects")
        except Exception:
            projs = []
        if projs:
            proj_opts = {"(none)": None} | {f"{p['name']}  ({p['id'][:8]}…)": p["id"] for p in projs}
            proj_choice = st.selectbox("Project for context", list(proj_opts.keys()), key="sel_proj_mdl")
            project_id_for_model = proj_opts[proj_choice]

    if model and st.button("🔍 Analyse Model Compliance", type="primary", key="btn_mdl"):
        endpoint = f"/compliance/model/{model['id']}"
        if project_id_for_model:
            endpoint += f"?project_id={project_id_for_model}"
        with st.spinner("🔎 Agent is analysing model compliance…"):
            try:
                result3 = _post(endpoint)
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
