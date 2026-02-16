"""Streamlit frontend for the Medical Case Generator."""

from __future__ import annotations

import json

import streamlit as st

from frontend.api_client import (
    delete_case,
    generate_case,
    get_case,
    list_cases,
    patch_case,
)

st.set_page_config(page_title="Medical Case Generator", layout="wide")

SPECIALTIES = [
    "",
    "cardiology",
    "pulmonology",
    "neurology",
    "gastroenterology",
    "endocrinology",
    "nephrology",
    "infectious disease",
    "hematology/oncology",
    "rheumatology",
    "psychiatry",
    "pediatrics",
    "surgery",
    "emergency medicine",
    "internal medicine",
]

page = st.sidebar.radio("Navigation", ["Generate", "Browse", "Detail / Edit"])

# ── Generate Page ──────────────────────────────────────────────────────────────

if page == "Generate":
    st.title("Generate a Medical Case")

    col1, col2 = st.columns(2)
    with col1:
        specialty = st.selectbox("Specialty", SPECIALTIES)
        difficulty = st.selectbox("Difficulty", ["", "easy", "medium", "hard"])
    with col2:
        prompt = st.text_area("Additional prompt / context", height=120)

    if st.button("Generate Case", type="primary"):
        with st.spinner("Generating case via LLM..."):
            try:
                case = generate_case(
                    specialty=specialty or None,
                    prompt=prompt or None,
                    difficulty=difficulty or None,
                )
                st.success(f"Case generated: {case.get('case_title', case['case_id'])}")
                st.session_state["last_case"] = case
            except Exception as e:
                st.error(f"Generation failed: {e}")

    if "last_case" in st.session_state:
        case = st.session_state["last_case"]
        st.subheader(case.get("case_title", "Untitled Case"))

        with st.expander("Demographics & Vitals", expanded=True):
            st.json(case.get("demographics"))
            st.json(case.get("vitals"))

        with st.expander("Chief Complaint & HPI"):
            st.json(case.get("chief_complaint_hpi"))

        with st.expander("History"):
            st.json(case.get("past_medical_history"))
            st.json(case.get("social_history"))
            st.json(case.get("medications"))
            st.json(case.get("allergies"))

        with st.expander("Physical Exam"):
            st.json(case.get("physical_exam"))

        with st.expander("Diagnostics"):
            st.json(case.get("diagnostics"))

        with st.expander("Assessment & Plan"):
            st.json(case.get("assessment"))
            st.json(case.get("plan"))


# ── Browse Page ────────────────────────────────────────────────────────────────

elif page == "Browse":
    st.title("Browse Cases")

    col1, col2 = st.columns([2, 1])
    with col1:
        filter_specialty = st.selectbox("Filter by specialty", SPECIALTIES, key="browse_spec")
    with col2:
        browse_page = st.number_input("Page", min_value=1, value=1, key="browse_page")

    try:
        data = list_cases(page=browse_page, specialty=filter_specialty or None)
        st.caption(f"Showing page {data['page']} — {data['total']} total cases")

        for item in data.get("items", []):
            with st.container():
                cols = st.columns([3, 1, 1, 1])
                cols[0].write(f"**{item.get('case_title', 'Untitled')}**")
                cols[1].write(item.get("specialty", ""))
                cols[2].write(item.get("difficulty", ""))
                if cols[3].button("View", key=item["case_id"]):
                    st.session_state["view_case_id"] = item["case_id"]
                    st.rerun()
    except Exception as e:
        st.error(f"Failed to load cases: {e}")


# ── Detail / Edit Page ────────────────────────────────────────────────────────

elif page == "Detail / Edit":
    st.title("Case Detail")

    case_id = st.text_input("Case ID", value=st.session_state.get("view_case_id", ""))

    if not case_id:
        st.info("Enter a Case ID or click View from the Browse page.")
    else:
        try:
            case = get_case(case_id)
        except Exception as e:
            st.error(f"Failed to load case: {e}")
            st.stop()

        st.subheader(case.get("case_title", "Untitled Case"))
        st.caption(f"ID: {case['case_id']} | Specialty: {case['specialty']} | Difficulty: {case['difficulty']}")

        editing = st.toggle("Edit mode")

        if editing:
            raw = st.text_area("Case JSON (edit below)", value=json.dumps(case, indent=2, default=str), height=500)
            col1, col2, col3 = st.columns(3)
            if col1.button("Save changes"):
                try:
                    updated = json.loads(raw)
                    result = patch_case(case_id, {"case_data": updated})
                    st.success("Case updated!")
                    st.json(result)
                except Exception as e:
                    st.error(f"Update failed: {e}")
            if col2.button("Delete case", type="secondary"):
                try:
                    delete_case(case_id)
                    st.success("Case deleted.")
                except Exception as e:
                    st.error(f"Delete failed: {e}")
        else:
            with st.expander("Demographics & Vitals", expanded=True):
                st.json(case.get("demographics"))
                st.json(case.get("vitals"))
            with st.expander("Chief Complaint & HPI"):
                st.json(case.get("chief_complaint_hpi"))
            with st.expander("History"):
                st.json(case.get("past_medical_history"))
                st.json(case.get("social_history"))
                st.json(case.get("medications"))
                st.json(case.get("allergies"))
            with st.expander("Physical Exam"):
                st.json(case.get("physical_exam"))
            with st.expander("Diagnostics"):
                st.json(case.get("diagnostics"))
            with st.expander("Assessment & Plan"):
                st.json(case.get("assessment"))
                st.json(case.get("plan"))
