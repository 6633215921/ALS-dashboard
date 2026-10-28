# ALS progress dashboard (ALSFRS-R)

Web app for the ALS clinic: enter the ALSFRS-R paper form and treatment courses in the browser (or in Excel), and
see each patient's ALSFRS-R total (48 → 0) over time, coloured by treatment, with slopes in **ALSFRS-R points per
month**.

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
  storage.py           the Excel workbook: layout check, Excel-ready template, all-or-nothing save
  codebook.py          ALSFRS-R items and level wording (EN / TH)
views/                 Streamlit pages and what they share
  data.py              the data file: first start, reload after Excel edits, save
  state.py             names of the values a browser session remembers (selected patient, ...)
  widgets.py           patient picker, treatment-course columns, sidebar settings
  dashboard.py         Dashboard page
  chart.py             the Dashboard chart (colours, slope lines, drug markers)
  patient_form.py      Patient form page
  treatments.py        Treatments page
  all_patients.py      All patients & data page
data/                  NOT in Git: made by the app on the computer it runs on
  raw_data.xlsx        the data (created blank on the first start); edit it in the app or in Excel
sample_data/
  raw_data_blank.xlsx  no patients, treatment types Riluzole and Edaravone (upload it to start empty)
  raw_data_DUMMY.xlsx  22 DUMMY patients for demos and training
.streamlit/config.toml Streamlit settings: only this computer (localhost:8501), no usage statistics
requirements.txt       Python packages
start.bat              Windows: start the app (installs the packages into .venv on the first start)
```

To change a calculation, edit `als/`; to change what a page shows, edit `views/`. Chart colours and slope-line
styles are at the top of `views/chart.py`.

## The data (3 tables)

`data/raw_data.xlsx` has these three sheets (+ a README sheet). Every value is text. Edit it in the app or in Excel
(see *Editing the data in Excel*).

* **forms**: one row per patient. `patient_id` (study code such as `MND-13`, never a name or HN), `form_language`
  (TH/EN), `last_assessed`, `notes`, then 48 boxes `q1_Speech_L3 … q12_Respiratory_Insufficiency_L0` = the month
  the patient first reached that level: `MM/YYYY` (AD), `YYYY` if only the year is known (counted as July), or `?`
  (reached by the latest month (the patient has reached this level, but we don’t know the month)). Level 4 = normal, no month.
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

## Install on the clinic computer (for real patient data)

The app runs on one Windows computer and only that computer can open it (`http://localhost:8501`, set in
`.streamlit/config.toml`). Patient data stays in the app folder on that computer.

1. **Python 3.10 or newer** from <https://www.python.org/downloads/windows/>. *Install for current user* needs no
   administrator rights; tick *Add python.exe to PATH*. (Hospital IT may have to approve or do this.)
2. **Get the app without any data**: on GitHub, *Code → Download ZIP*, and unzip it to a folder on the computer's
   own disk, for example `C:\ALS-dashboard`. The ZIP has no `data` folder, so the app starts empty.
   (Copying the folder from another computer also copies its `data` and `.venv`; do not do that.)
3. **Double-click `start.bat`.** The first start installs the packages into `.venv` (a few minutes, needs internet
   once, or see *Install without internet*). The app then opens in the browser. Keep the black window open while
   using the app; closing it stops the app. If Windows asks whether to run the file, choose *More info → Run anyway*.
4. **Desktop shortcut**: right-click `start.bat` → *Send to → Desktop (create shortcut)*.
5. The app starts with no patients and the treatment types Riluzole and Edaravone. If the sidebar says *Sample data:
   DUMMY patients*, upload `sample_data/raw_data_blank.xlsx` (*All patients & data → Upload data*) before entering
   real patients.

**Copies.** The app keeps no backups. Copy the `data` folder to a hospital-approved place (for example a network
drive or an encrypted USB drive) regularly, and download a copy (*All patients & data → Download*) before large
changes such as *Upload data (replace all data)*.

**Update the app**: download the new ZIP and unzip it over the old folder. `data` and `.venv` are not in the ZIP,
so the data stays; `start.bat` installs new packages by itself if `requirements.txt` changed.

**Install without internet**: on a computer with internet and the same Python version (for example 3.12, 64-bit),
open a command prompt in the app folder and run `py -m pip download -r requirements.txt -d wheels`. Copy the app
folder with the new `wheels` folder (but without `data` and `.venv`) to the clinic computer; `start.bat` then
installs from `wheels` without internet.

## Editing the data in Excel

`data/raw_data.xlsx` can be opened and edited in Excel at any time, also while the app is running.

* The file is prepared for Excel: the README sheet explains the columns, cells are formatted as Text (so `03/2026`
  stays `03/2026`), `patient_id` stays in view while scrolling, and `form_language`, `treatments.patient_id` and
  `treatments.treatment` have dropdowns. If Excel still turns a month into a date, the app reads it back as that month.
* After saving in Excel, click anywhere in the app: it shows the new data. If you were in the middle of an edit in the
  app, that edit is not saved (the page says so) and you make it again on the new data. Two browser windows work the
  same way.
* While Excel has the file open, the app cannot save (Windows locks the file); the sidebar says so. Close the file in
  Excel, then press the button in the app again. Your edit stays on the page.
* Keep the layout: do not rename, add or delete sheets or columns. If the layout changes, every page lists what to fix
  and the app does not touch the file until it is fixed. Mistakes in values (a wrong month, an unknown drug) are
  listed in the app under *All patients & data*, column *check*.
* When the app saves, it rewrites the file in its own layout, so formatting or colours added in Excel are not kept.
* Rename a drug in the app (*Treatments*), which also renames it in every course.

## Run on your own computer (development)

Double-click `start.bat`, or from this folder (so that `.streamlit/config.toml` is used):

```
pip install -r requirements.txt
streamlit run app.py
```

The app reads and saves `data/raw_data.xlsx`; on the first start it is created blank. For the DUMMY patients,
upload `sample_data/raw_data_DUMMY.xlsx`.

## Deploy on Streamlit Community Cloud

1. Push this folder to GitHub (a **private** repository: no real patient data in Git, see Privacy).
2. share.streamlit.io → **Create app** → choose the repository, branch `main`, main file `app.py`.
   Already deployed with `visualization.py`? Change the main file to `app.py`; if the app settings do not offer
   that, delete the app and deploy it again (you can reuse the same app URL).
3. Deploy. After an edit in GitHub the app updates by itself. On Streamlit Cloud the first start loads the 22 DUMMY
   patients (`sample_data/raw_data_DUMMY.xlsx`), so the online app is a demo.

The app server's files are reset whenever the app restarts (for example after it has been asleep), so **edits saved on
Streamlit Cloud are lost** at that point (the app shows a warning in the sidebar). After editing there, download
the workbook (*All patients & data → Workbook: data + results*); after a restart, upload it again
(*Upload data (replace all data)*).

## Privacy

* Use study codes only (`MND-xx`). No names, HN, ID card numbers or birth dates in any field, including notes.
* Keep the GitHub repository private and do not commit real data. `data/` (the data file) is in
  `.gitignore`; Git holds only `sample_data/` (blank and DUMMY workbooks).
* Real patient data: use the clinic-computer install above, not Streamlit Cloud.
* Make the Streamlit app private (*Share → Who can view*) and invite only the study team.
* Follow the study's ethics approval and PDPA rules for where patient data may be stored.
