"""ALS progress: ALSFRS-R dashboard and data workbench (Streamlit).

Run:  streamlit run app.py        (or double-click run_app.bat)

Pages (views/)
  Dashboard            ALSFRS-R total of one patient over time, coloured by treatment, slopes in points/month
  Patient form         add / edit / delete a patient: the 12 x 4 level boxes of the paper form + treatment courses
  Treatments           treatment types (add a new drug, rename) and all treatment courses in one table
  All patients & data  summary (scores, slopes, checks), download results, upload / restore a workbook
Data and calculations (als/): see als/__init__.py. Data: data/raw_data.xlsx.
"""
import streamlit as st

from views import all_patients, dashboard, patient_form, shared, treatments

st.set_page_config(page_title="ALS progress", layout="wide")
st.session_state.setdefault("baseline", True)
page = st.navigation([
    st.Page(dashboard.render, title="Dashboard", icon=":material/monitoring:", default=True),
    st.Page(patient_form.render, title="Patient form", icon=":material/edit_note:", url_path="patient-form"),
    st.Page(treatments.render, title="Treatments", icon=":material/medication:", url_path="treatments"),
    st.Page(all_patients.render, title="All patients & data", icon=":material/table_view:", url_path="data"),
])
page.run()
shared.sidebar_footer()
