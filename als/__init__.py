"""ALS progress: data and calculations, no Streamlit.

model     the three tables (forms, treatments, treatment_types), columns, months
scoring   one patient: item scores, raw points, monthly timeline, treatment states, slopes
checks    data checks (errors / warnings)
report    all patients: summary table and monthly timeline
edits     add / change / delete data
storage   read / write the Excel workbook (the data file doctors can also edit in Excel)
codebook  ALSFRS-R item and level wording (EN / TH)
"""
