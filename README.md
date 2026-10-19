# ALS progress dashboard (ALSFRS-R)

Web app for the ALS clinic: enter the ALSFRS-R paper form and treatment courses in the browser, and see each
patient's ALSFRS-R total (48 → 0) over time, coloured by treatment, with slopes in **ALSFRS-R points per month**.

| Page | What it does |
|---|---|
| Dashboard | Chart for one patient: raw points, Linear / Step / None between them, slopes (all, before treatment, on treatment, time of interest), drug start/stop markers, slope by treatment state |
| Patient form | Add, edit, rename or delete a patient: the 12 × 4 level boxes of the paper form + the patient's treatment courses |
| Treatments | Treatment types (add a new drug, rename) and all treatment courses in one table |
| All patients & data | Summary of every patient (domain scores, slopes, checks), download the workbook / timeline, upload a workbook |

## Folder structure

```
app.py                 main file: page menu (run this one)
als/                   data and calculations, no Streamlit
  model.py             the 3 tables, column names, months (MM/YYYY <-> month number)
  scoring.py           one patient: item scores, raw points, monthly timeline, treatment states, slopes
  checks.py            data checks (errors block a save, warnings are shown)
  report.py            all patients: summary table and score_timeline
  edits.py             add / change / delete patients, treatment types and courses
  storage.py           read / write data/raw_data.xlsx, download / upload workbooks
  codebook.py          ALSFRS-R items and level wording (EN / TH)
views/                 Streamlit pages
  shared.py            data access, save, patient picker, sidebar
  dashboard.py         Dashboard page
  chart.py             the Dashboard chart (colours, slope lines, drug markers)
  patient_form.py      Patient form page
  treatments.py        Treatments page
  all_patients.py      All patients & data page
data/raw_data.xlsx     the data (sample: DUMMY patients only)
requirements.txt       Python packages
run_app.bat            Windows: install packages and start the app
```

To change a calculation, edit `als/`; to change what a page shows, edit `views/`. Chart colours and slope-line
styles are at the top of `views/chart.py`.

## The data (3 tables)

`data/raw_data.xlsx` has these three sheets (+ a README sheet). Every value is text.

* **forms**: one row per patient. `patient_id` (study code such as `MND-13`, never a name or HN), `form_language`
  (TH/EN), `last_assessed`, `notes`, then 48 boxes `q1_Speech_L3 … q12_Respiratory_Insufficiency_L0` = the month
  the patient first reached that level: `MM/YYYY` (AD), `YYYY` if only the year is known (counted as July), or `?`
  (reached by the latest month). Level 4 = normal, no month.
* **treatments**: one row per course: `patient_id`, `treatment`, `start`, `stop` (`MM/YYYY`, blank stop = still
  on), `notes`. Any number of courses per patient, also the same drug twice (stopped and restarted).
* **treatment_types**: the drugs the app offers (`Riluzole`, `Edaravone`, …).

**Adding a new drug**: Treatments page → add a row under *Treatment types* → *Save types*. Then add courses for it
(Patient form page or *All treatment courses*). Months on two drugs at once are shown as e.g.
`Riluzole + Edaravone + <new drug>` with their own colour; *Slope, on treatment* covers every month on any drug.

## Calculations

* Raw points = months in which at least one item changed level, plus an optional 48/48 baseline one month before
  the first change (sidebar checkbox) and `last_assessed` if it is later than the last change.
* Months between raw points: **Linear interpolation** (the base for all slopes), Step or None (Dashboard option).
* Slope = least-squares line through the monthly totals, ALSFRS-R points per month. Fewer than 3 raw points =
  not reliable (shown in the captions and the `check` column).

## Run on your computer

Double-click `run_app.bat`, or:

```
pip install -r requirements.txt
streamlit run app.py
```

The app reads and saves `data/raw_data.xlsx`.

## Deploy on Streamlit Community Cloud

1. Push this folder to GitHub (a **private** repository: no real patient data in Git, see Privacy).
2. share.streamlit.io → **Create app** → choose the repository, branch `main`, main file `app.py`.
   Already deployed with `visualization.py`? Change the main file to `app.py`; if the app settings do not offer
   that, delete the app and deploy it again (you can reuse the same app URL).
3. Deploy. After an edit in GitHub the app updates by itself.

The app server's files are reset whenever the app restarts (for example after it has been asleep), so **edits saved on
Streamlit Cloud are lost** at that point (the app shows a warning in the sidebar). After editing there, download
the workbook (*All patients & data → Workbook: data + results*); after a restart, upload it again
(*Upload data (replace all data)*).

## Privacy

* Use study codes only (`MND-xx`). No names, HN, ID card numbers or birth dates in any field, including notes.
* Keep the GitHub repository private and do not commit real data; `data/raw_data.xlsx` in Git holds DUMMY data only.
* Make the Streamlit app private (*Share → Who can view*) and invite only the study team.
* Follow the study's ethics approval and PDPA rules for where patient data may be stored.
