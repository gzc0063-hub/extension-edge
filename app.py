"""
app.py - Streamlit user interface.

Collects all grower inputs on one mobile-friendly page, dispatches to
validator -> engine -> scorer -> explainer -> pdf_report, and renders the
result. No decision logic lives in this module.
"""

from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

from validator import UserInput, validate, FORAGE_TYPES, LIVESTOCK
from engine import (
    load_database,
    filter_by_forage,
    apply_hard_filters,
    flag_unknowns,
    Result,
    Status,
    now_iso,
    ENGINE_VERSION,
    GUIDE_VERSION,
    MOWING_RULES,
)
from scorer import rank_by_efficacy, select_best
from explainer import render
from pdf_report import build as build_pdf
from report_store import save_report
from labels import (
    APP_NAME,
    FORAGE_LABELS,
    LIVESTOCK_LABELS,
    LEGUME_LABELS,
    RUP_LABELS,
    forage_label,
    legume_label,
    livestock_label,
    rup_label,
    title_case_code,
    weed_label,
)


st.set_page_config(
    page_title=APP_NAME,
    page_icon="A",
    layout="centered",
    initial_sidebar_state="collapsed",
)


AUBURN_BLUE = "#0C2340"
AUBURN_ORANGE = "#E87722"
ACES_GREEN = "#2F6B3F"
SOFT_BACKGROUND = "#F7F3EF"


def _new_field_id() -> str:
    return "AL-" + uuid.uuid4().hex[:8].upper()


if "field_id" not in st.session_state:
    st.session_state.field_id = _new_field_id()
if "ui_data" not in st.session_state:
    st.session_state.ui_data = {}
if "submitted_once" not in st.session_state:
    st.session_state.submitted_once = False
if "report_backup_saved" not in st.session_state:
    st.session_state.report_backup_saved = False


@st.cache_data(show_spinner=False)
def _db():
    return load_database()


try:
    db = _db()
    if db["herbicides"].empty:
        st.error(
            "No herbicide data loaded. Populate data/herbicides.csv, "
            "data/efficacy.csv, and data/restrictions.csv with the IPM-0028A data."
        )
        st.stop()
except FileNotFoundError as e:
    st.error(f"Missing data file: {e}")
    st.stop()


def _format_list(values: list[str], labeler) -> str:
    return ", ".join(labeler(value) for value in values) if values else "None selected"


def _save_form(data: dict[str, Any]) -> None:
    st.session_state.ui_data = data
    st.session_state.submitted_once = True
    st.session_state.report_backup_saved = False


ALL_WEED_OPTIONS = sorted(
    set(MOWING_RULES.keys()) - {"_default"} | {"bermudagrass", "marestail", "nutsedge", "ragweed"},
    key=weed_label,
)

ALABAMA_COUNTIES = [
    "Prefer not to say / outside Alabama",
    "Autauga", "Baldwin", "Barbour", "Bibb", "Blount", "Bullock", "Butler",
    "Calhoun", "Chambers", "Cherokee", "Chilton", "Choctaw", "Clarke", "Clay",
    "Cleburne", "Coffee", "Colbert", "Conecuh", "Coosa", "Covington",
    "Crenshaw", "Cullman", "Dale", "Dallas", "DeKalb", "Elmore", "Escambia",
    "Etowah", "Fayette", "Franklin", "Geneva", "Greene", "Hale", "Henry",
    "Houston", "Jackson", "Jefferson", "Lamar", "Lauderdale", "Lawrence",
    "Lee", "Limestone", "Lowndes", "Macon", "Madison", "Marengo", "Marion",
    "Marshall", "Mobile", "Monroe", "Montgomery", "Morgan", "Perry",
    "Pickens", "Pike", "Randolph", "Russell", "Shelby", "St. Clair",
    "Sumter", "Talladega", "Tallapoosa", "Tuscaloosa", "Walker",
    "Washington", "Wilcox", "Winston",
]


def _inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --auburn-blue: {AUBURN_BLUE};
            --auburn-orange: {AUBURN_ORANGE};
            --aces-green: {ACES_GREEN};
            --soft-background: {SOFT_BACKGROUND};
        }}
        .stApp {{
            background:
                linear-gradient(180deg, rgba(12, 35, 64, 0.06), rgba(255,255,255,0) 280px),
                #ffffff;
            color: var(--auburn-blue);
        }}
        .block-container {{
            max-width: 980px;
            padding: 1.5rem 1rem 3rem;
        }}
        h1, h2, h3 {{
            color: var(--auburn-blue);
            letter-spacing: 0;
        }}
        h1 {{
            font-size: 2.35rem;
            line-height: 1.1;
            margin-bottom: 0.35rem;
        }}
        h2 {{
            font-size: 1.25rem;
            margin-top: 1.2rem;
        }}
        h3 {{
            font-size: 1rem;
        }}
        [data-testid="stMarkdownContainer"] p {{
            line-height: 1.55;
        }}
        .hero-panel {{
            border-top: 6px solid var(--auburn-orange);
            background: var(--auburn-blue);
            color: #ffffff;
            padding: 1.2rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }}
        .hero-panel h1, .hero-panel p, .hero-panel strong {{
            color: #ffffff;
        }}
        .hero-panel .small {{
            color: rgba(255,255,255,0.84);
            font-size: 0.95rem;
        }}
        .source-strip {{
            background: #ffffff;
            border: 1px solid rgba(12, 35, 64, 0.14);
            border-left: 5px solid var(--aces-green);
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 1rem 0;
        }}
        .section-band {{
            background: var(--soft-background);
            border: 1px solid rgba(12, 35, 64, 0.10);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0 0.75rem;
        }}
        .rank-box {{
            background: #ffffff;
            border: 1px solid rgba(12, 35, 64, 0.12);
            border-radius: 8px;
            padding: 0.75rem 0.9rem;
            margin-top: 0.5rem;
        }}
        .rank-box ol {{
            margin: 0.35rem 0 0 1.2rem;
            padding: 0;
        }}
        .rank-box li {{
            margin: 0.25rem 0;
        }}
        div.stButton > button,
        div.stDownloadButton > button {{
            border-radius: 6px;
            min-height: 2.85rem;
            font-weight: 700;
        }}
        div.stButton > button[kind="primary"],
        div.stDownloadButton > button[kind="primary"] {{
            background: var(--auburn-orange);
            border-color: var(--auburn-orange);
            color: var(--auburn-blue);
        }}
        div.stButton > button[kind="primary"]:hover,
        div.stDownloadButton > button[kind="primary"]:hover {{
            background: #D96A1B;
            border-color: #D96A1B;
            color: var(--auburn-blue);
        }}
        button:focus-visible,
        input:focus-visible,
        textarea:focus-visible,
        [role="button"]:focus-visible,
        [role="combobox"]:focus-visible {{
            outline: 3px solid var(--aces-green) !important;
            outline-offset: 2px !important;
            box-shadow: none !important;
        }}
        div[data-baseweb="select"] > div:focus-within {{
            border-color: var(--aces-green) !important;
            box-shadow: 0 0 0 3px rgba(47, 107, 63, 0.28) !important;
        }}
        div[data-testid="stForm"] {{
            border: 0;
            padding: 0;
        }}
        @media (max-width: 640px) {{
            .block-container {{
                padding: 0.75rem 0.75rem 2rem;
            }}
            h1 {{
                font-size: 1.85rem;
            }}
            .hero-panel, .source-strip, .section-band {{
                border-radius: 6px;
                padding: 0.9rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _header() -> None:
    st.markdown(
        f"""
        <div class="hero-panel">
          <h1>{APP_NAME}</h1>
          <p><strong>A pasture and forage weed-control planning aid for Alabama growers.</strong></p>
          <p class="small">Use this tool to screen herbicide options while planning a weed-management strategy. Always read and follow the product label before purchase or final application.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="source-strip">
          <strong>Information source:</strong> Alabama Cooperative Extension System {GUIDE_VERSION},
          <em>Pasture &amp; Forage Crops Weed Control Recommendations for 2026</em>, revised by
          <strong>Dr. David Russell</strong>, Assistant Extension Professor (Weed Science),
          Department of Crop, Soil &amp; Environmental Sciences, Auburn University.
          Contact: 256-353-8702, dpr0013@auburn.edu.
          <br>
          <strong>Tool development:</strong> Developed by PhD student <strong>Gourav Chahal</strong>
          under the supervision of <strong>Dr. David Russell</strong> and
          <strong>Dr. Andrew Price</strong>, USDA ARS.
          <br>
          <strong>Audit:</strong> Engine v{ENGINE_VERSION} · Field ID {st.session_state.field_id}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _make_ui_from_data(d: dict[str, Any]) -> UserInput:
    return UserInput(
        field_id=st.session_state.field_id,
        forage=d.get("forage", ""),
        weeds=d.get("weeds", []),
        livestock=d.get("livestock", "NONE"),
        hold_days=d.get("hold_days"),
        legumes_present=d.get("legumes_present", False),
        legumes=d.get("legumes", []),
        next_cut_days=d.get("next_cut_days"),
        days_since_mow=d.get("days_since_mow"),
        slaughter_30d=d.get("slaughter_30d", False),
        hay_off_farm=d.get("hay_off_farm", False),
        manure_off=d.get("manure_off", False),
        sensitive_crops_nearby=d.get("sensitive_crops_nearby", False),
        rup_status=d.get("rup_status", "any"),
        farm_name=d.get("farm_name", ""),
        operator_name=d.get("operator_name", ""),
        location=d.get("location", ""),
    )


def run_pipeline() -> tuple[Result, UserInput, str]:
    ui = _make_ui_from_data(st.session_state.ui_data)

    errors = validate(ui)
    if errors:
        result = Result(status=Status.INVALID_INPUT, field_id=ui.field_id, timestamp=now_iso(), errors=errors)
        return result, ui, render(result, ui)

    candidates = filter_by_forage(db["herbicides"], ui.forage)
    if not candidates:
        result = Result(
            status=Status.NO_LEGAL_RECOMMENDATION,
            field_id=ui.field_id,
            timestamp=now_iso(),
            primary_reason=f"No products labeled for forage type '{forage_label(ui.forage)}' in IPM-0028A.",
        )
        return result, ui, render(result, ui)

    approved, rejected, review = apply_hard_filters(candidates, ui)
    safe, more_review = flag_unknowns(approved)
    review = review + more_review

    if not safe:
        if review and not rejected:
            result = Result(
                status=Status.MANUAL_REVIEW,
                field_id=ui.field_id,
                timestamp=now_iso(),
                review=review,
                rejected=rejected,
            )
        else:
            primary = rejected[0][1] if rejected else "No products survived hard filters."
            what_could_change = []
            if ui.legumes_present:
                what_could_change.append("Remove the legume protection requirement if the stand will be terminated.")
            if ui.livestock == "LACTATING_DAIRY":
                what_could_change.append("Increase the animal hold period beyond the current setting.")
            if ui.next_cut_days is not None:
                what_could_change.append("Delay the next hay cut to allow a longer pre-harvest interval.")
            if ui.rup_status == "no_unrestricted_only":
                what_could_change.append("Work with a certified applicator for Restricted Use Pesticide options.")
            result = Result(
                status=Status.NO_LEGAL_RECOMMENDATION,
                field_id=ui.field_id,
                timestamp=now_iso(),
                rejected=rejected,
                review=review,
                primary_reason=primary,
                what_could_change=what_could_change,
            )
        return result, ui, render(result, ui)

    ranked = rank_by_efficacy(safe, ui.weeds, db["efficacy"])
    best, backup, partial = select_best(ranked)

    if best is None:
        result = Result(
            status=Status.NO_SINGLE_PRODUCT,
            field_id=ui.field_id,
            timestamp=now_iso(),
            partial_options=partial,
            rejected=rejected,
            review=review,
        )
    else:
        warnings = []
        cmt = (best.get("comments_structured") or "").lower()
        for keyword in ("caution", "do not", "avoid", "may injure", "see label"):
            if keyword in cmt:
                warnings.append(f"Comment flag: '{keyword}' in product comments")
                break
        status = Status.RECOMMEND_WITH_WARNINGS if warnings else Status.RECOMMEND
        result = Result(
            status=status,
            field_id=ui.field_id,
            timestamp=now_iso(),
            best=best,
            backup=backup,
            approved=safe,
            rejected=rejected,
            review=review,
            warnings=warnings,
        )

    return result, ui, render(result, ui)


def _render_rank_explanation(selected_weeds: list[str]) -> None:
    st.markdown(
        """
        <div class="rank-box">
          <strong>How weed priority works:</strong> Pick up to three weeds. Weed 1 is the main target and has the strongest effect on ranking. Weed 2 is secondary. Weed 3 is still considered, but it will not outweigh poor control of Weed 1.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if selected_weeds:
        st.markdown("**Current priority order**")
        for idx, weed in enumerate(selected_weeds, start=1):
            if idx == 1:
                meaning = "highest priority"
            elif idx == 2:
                meaning = "second priority"
            else:
                meaning = "third priority"
            st.write(f"{idx}. {weed_label(weed)} - {meaning}")


def _render_input_form() -> None:
    d = st.session_state.ui_data
    forage_values = sorted(FORAGE_TYPES, key=forage_label)
    livestock_values = sorted(LIVESTOCK, key=livestock_label)

    with st.form("grower_inputs"):
        st.markdown('<div class="section-band"><h2>Field and crop</h2></div>', unsafe_allow_html=True)
        forage = st.selectbox(
            "Forage or crop situation",
            forage_values,
            index=forage_values.index(d.get("forage")) if d.get("forage") in forage_values else 0,
            format_func=forage_label,
            help="Choose the forage scenario that best matches the treated field.",
        )
        farm_name = st.text_input("Farm name, optional", value=d.get("farm_name", ""))
        operator_name = st.text_input("Operator name, optional", value=d.get("operator_name", ""))
        saved_county = d.get("location", "Prefer not to say / outside Alabama")
        county = st.selectbox(
            "County for usage reporting",
            ALABAMA_COUNTIES,
            index=ALABAMA_COUNTIES.index(saved_county) if saved_county in ALABAMA_COUNTIES else 0,
            help="Used only to summarize where the tool is being used. This also appears in the PDF record.",
        )

        st.markdown('<div class="section-band"><h2>Weeds of interest</h2></div>', unsafe_allow_html=True)
        weeds = st.multiselect(
            "Start typing or scroll to choose weeds, in priority order",
            ALL_WEED_OPTIONS,
            default=d.get("weeds", []),
            format_func=weed_label,
            max_selections=3,
            help="Options are alphabetized. The order you select becomes the priority ranking.",
        )
        _render_rank_explanation(weeds)

        st.markdown('<div class="section-band"><h2>Mowing and hay timing</h2></div>', unsafe_allow_html=True)
        days_since_enabled = st.checkbox(
            "This field has been mowed recently",
            value=d.get("days_since_mow") is not None,
        )
        days_since_mow = None
        if days_since_enabled:
            days_since_mow = int(
                st.number_input(
                    "Days since last mowing",
                    min_value=0,
                    max_value=365,
                    value=int(d.get("days_since_mow", 0) or 0),
                )
            )

        next_cut_enabled = st.checkbox(
            "A hay cut or harvest is planned",
            value=d.get("next_cut_days") is not None,
        )
        next_cut_days = None
        if next_cut_enabled:
            next_cut_days = int(
                st.number_input(
                    "Days until next hay cut or harvest",
                    min_value=0,
                    max_value=365,
                    value=int(d.get("next_cut_days", 30) or 30),
                )
            )

        st.markdown('<div class="section-band"><h2>Livestock and field conditions</h2></div>', unsafe_allow_html=True)
        livestock = st.selectbox(
            "Livestock situation",
            livestock_values,
            index=livestock_values.index(d.get("livestock", "NONE")) if d.get("livestock", "NONE") in livestock_values else 0,
            format_func=livestock_label,
        )
        hold_days = None
        if livestock == "LACTATING_DAIRY":
            hold_days = int(
                st.number_input(
                    "How many days can lactating dairy animals stay off the treated area?",
                    min_value=0,
                    max_value=180,
                    value=int(d.get("hold_days", 0) or 0),
                )
            )

        legumes_present = st.checkbox(
            "Legumes are present in this stand",
            value=d.get("legumes_present", False),
        )
        legumes = []
        if legumes_present:
            legume_values = sorted(LEGUME_LABELS, key=legume_label)
            legumes = st.multiselect(
                "Which legumes are present?",
                legume_values,
                default=d.get("legumes", []),
                format_func=legume_label,
            )

        hay_off_farm = st.checkbox("Hay from this field may leave the farm", value=d.get("hay_off_farm", False))
        manure_off = st.checkbox("Manure from animals on this field may leave the farm or be used on sensitive crops", value=d.get("manure_off", False))
        sensitive_crops_nearby = st.checkbox("Sensitive broadleaf crops are nearby", value=d.get("sensitive_crops_nearby", False))
        slaughter_30d = st.checkbox("Animals from this field may go to slaughter within 30 days", value=d.get("slaughter_30d", False))

        st.markdown('<div class="section-band"><h2>Applicator status</h2></div>', unsafe_allow_html=True)
        rup_options = ["any", "no_unrestricted_only"]
        rup_status = st.radio(
            "Restricted Use Pesticide access",
            rup_options,
            index=rup_options.index(d.get("rup_status", "any")) if d.get("rup_status", "any") in rup_options else 0,
            format_func=rup_label,
        )

        submitted = st.form_submit_button("Get recommendation", type="primary", use_container_width=True)

    if submitted:
        _save_form(
            {
                "forage": forage,
                "weeds": weeds,
                "days_since_mow": days_since_mow,
                "next_cut_days": next_cut_days,
                "livestock": livestock,
                "hold_days": hold_days,
                "legumes_present": legumes_present,
                "legumes": legumes,
                "hay_off_farm": hay_off_farm,
                "manure_off": manure_off,
                "sensitive_crops_nearby": sensitive_crops_nearby,
                "slaughter_30d": slaughter_30d,
                "rup_status": rup_status,
                "farm_name": farm_name,
                "operator_name": operator_name,
                "location": county,
            }
        )


def _display_product(product: dict[str, Any]) -> None:
    clean = {k: v for k, v in product.items() if not k.startswith("_")}
    rows = {
        "Product": clean.get("trade_name", "-"),
        "Active ingredient": clean.get("active_ingredient", "-"),
        "Rate": clean.get("rate_per_acre", "-"),
        "Timing": clean.get("timing_constraints", "-"),
        "Guide reference": clean.get("guide_page_ref", "-"),
    }
    st.table(rows)


def _show_mowing_advisory(ui: UserInput) -> None:
    if not ui.weeds:
        return
    weed = ui.weeds[0]
    top_rule = MOWING_RULES.get(weed, MOWING_RULES["_default"])
    before = top_rule["before_days"]
    after = top_rule["after_days"]
    category = title_case_code(top_rule.get("category", "unknown"))
    if before == "next_season":
        st.info(
            f"For {weed_label(weed)} ({category}), IPM-0028A indicates woody plants need enough regrowth after mowing. "
            f"Do not spray until the following growing season, and wait at least {after} days after treatment before mowing."
        )
    else:
        st.info(
            f"For {weed_label(weed)} ({category}), use at least {before} days between mowing and spraying, "
            f"and wait at least {after} days after spraying before cutting."
        )


def show_result() -> None:
    result, ui, narrative = run_pipeline()

    st.markdown("## Recommendation")
    banner = {
        Status.RECOMMEND: st.success,
        Status.RECOMMEND_WITH_WARNINGS: st.warning,
        Status.NO_SINGLE_PRODUCT: st.warning,
        Status.NO_LEGAL_RECOMMENDATION: st.error,
        Status.MANUAL_REVIEW: st.warning,
        Status.INVALID_INPUT: st.error,
    }.get(result.status, st.warning)
    banner(result.status.replace("_", " ").title())

    if result.status == Status.INVALID_INPUT:
        st.write(narrative)
        return

    _show_mowing_advisory(ui)

    tab_rec, tab_fail, tab_review = st.tabs(["Recommendation", "Why others failed", "Manual review"])

    with tab_rec:
        rec_head, rec_download = st.columns([1, 1])
        with rec_head:
            st.markdown("### Recommendation report")
        with rec_download:
            pdf_bytes = build_pdf(result, ui, narrative)
            if not st.session_state.report_backup_saved:
                saved, message = save_report(result, ui, narrative, pdf_bytes)
                if saved:
                    st.session_state.report_backup_saved = True
                else:
                    st.warning(f"Report backup could not be saved: {message}")
            st.download_button(
                "Download PDF record",
                data=pdf_bytes,
                file_name=f"extension-edge-{result.field_id}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        st.write(narrative)
        if result.best:
            st.markdown("### Primary recommendation")
            _display_product(result.best)
        if result.backup:
            st.markdown("### Backup option")
            _display_product(result.backup)
        if result.partial_options and not result.best:
            st.markdown("### Top partial options")
            for product in result.partial_options:
                _display_product(product)

    with tab_fail:
        if not result.rejected:
            st.write("No products were rejected by hard label gates.")
        else:
            st.markdown(f"### {len(result.rejected)} product(s) rejected")
            for product, reason, gate in result.rejected:
                st.markdown(f"- **{product.get('trade_name', '-')}** ({gate.replace('_', ' ')}) - {reason}")

    with tab_review:
        if not result.review:
            st.write("No products require manual review.")
        else:
            st.markdown(f"### {len(result.review)} product(s) need manual review")
            for product, reason, gate in result.review:
                st.markdown(f"- **{product.get('trade_name', '-')}** ({gate.replace('_', ' ')}) - {reason}")

    if st.button("Start a new field", use_container_width=True):
        st.session_state.clear()
        st.rerun()


_inject_css()
_header()
_render_input_form()

if st.session_state.submitted_once:
    show_result()
