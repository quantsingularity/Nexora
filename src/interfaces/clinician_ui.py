import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st


def show_clinician_dashboard(patient_data, predictions):
    st.set_page_config(layout="wide")

    # Patient Summary
    with st.expander("Patient Overview"):
        cols = st.columns(3)
        cols[0].metric("Readmission Risk", f"{predictions['risk']:.0%}")
        cols[1].metric("Top Risk Factors", "\n".join(predictions["top_features"][:3]))
        cols[2].metric("Similar Patients", f"n={predictions['cohort_size']}")

    # Temporal View
    st.subheader("Clinical Timeline")
    timeline_fig = px.timeline(
        patient_data, x_start="start", x_end="end", y="event_type", color="department"
    )
    st.plotly_chart(timeline_fig, use_container_width=True)

    # SHAP Explanation
    st.subheader("Risk Factor Breakdown")
    shap_df = pd.DataFrame(
        {"Feature": predictions["shap_features"], "Impact": predictions["shap_values"]}
    ).sort_values("Impact", ascending=False)

    st.altair_chart(
        alt.Chart(shap_df.head(10))
        .mark_bar()
        .encode(x="Impact:Q", y=alt.Y("Feature:N", sort="-x"))
    )

    # Clinical Decision Support
    with st.sidebar:
        st.header("Intervention Checklist")
        if predictions["risk"] > 0.7:
            st.checkbox("Schedule follow-up within 7 days")
            st.checkbox("Verify medication reconciliation")
            st.checkbox("Assess social support needs")
