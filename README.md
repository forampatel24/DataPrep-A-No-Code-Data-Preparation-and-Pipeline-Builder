# DataPrep

A no-code data preparation platform for cleaning, transforming, validating, and exporting structured datasets through reusable preprocessing pipelines.

Built with Django, Pandas, and Bootstrap 5.

## Features

- **Authentication** — User registration, login, and logout
- **File Upload** — Upload CSV, Excel (.xlsx), and JSON files with validation
- **Dataset Profiling** — Automatic type detection, schema identification, and data health scoring
- **Data Cleaning** — Remove duplicates, fill missing values, trim whitespace, normalize text, standardize capitalization, rename columns
- **Data Transformation** — Type conversion, date formatting, text case changes, regex find & replace, derived column generation
- **Data Validation** — Validate email addresses, phone numbers, and dates
- **Outlier Detection** — IQR and Z-score based detection
- **Data Merging** — Inner, left, and right joins on common keys
- **Pipeline Builder** — Create, edit, reorder, and save preprocessing steps as reusable pipelines
- **Pipeline Execution** — Execute pipelines with before/after comparison
- **Export** — Download processed datasets as CSV, Excel, or JSON

## Requirements

- Python 3.12+
- Django 6.0+
- Pandas, NumPy, OpenPyXL, and other dependencies (see `requirements.txt`)

## Quick Start

1. **Clone the repository**
   ```
   git clone <repo-url>
   cd DataPrep
   ```

2. **Create and activate a virtual environment**
   ```
   python -m venv .venv
   .venv\Scripts\activate    # Windows
   source .venv/bin/activate # macOS/Linux
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```
   python manage.py migrate
   ```

5. **Start the development server**
   ```
   python manage.py runserver
   ```

6. **Open the app** at `http://127.0.0.1:8000`

## Project Structure

```
DataPrep/
├── cleanslate/            # Django project configuration
├── authentication/        # Login, signup, logout
├── dashboard/             # Home page with stats and recent activity
├── datasets/              # File upload, dataset overview, profiling
├── pipelines/             # Pipeline CRUD, execution, history
├── processing/            # Modular data processing engine
│   ├── profiling.py       # Dataset profiling & health reports
│   ├── cleaning.py        # Duplicates, missing values, text cleanup
│   ├── transformation.py  # Type conversion, date formatting, derived columns
│   ├── validation.py      # Email, phone, date validation
│   ├── outliers.py        # IQR and Z-score detection
│   ├── merging.py         # Inner/left/right joins
│   ├── conversion.py      # CSV/Excel/JSON export
│   └── pipeline_executor.py  # Sequential step execution
├── templates/             # Bootstrap 5 HTML templates
│   ├── base.html          # Base layout (navbar, dark mode, footer)
│   ├── authentication/    # Login, signup pages
│   ├── dashboard/         # Home page
│   ├── datasets/          # Upload, overview, list, samples
│   └── pipelines/         # Create, edit, execute, results, history, export
├── static/                # Static assets
├── media/
│   ├── uploads/           # Uploaded datasets
│   ├── processed/         # Processed output files
│   └── samples/           # Pre-loaded sample datasets
├── db.sqlite3             # Development database
├── manage.py
├── requirements.txt
├── Project_SPEC.md        # Full development specification
└── .gitignore
```

## Usage

1. **Register** an account and log in
2. **Upload** a CSV, Excel, or JSON dataset — or start with a pre-loaded sample
3. **Review** the automatic profiling (types, schema, health score, health report)
4. **Build a pipeline** by adding preprocessing steps (20 available operations) in order
5. **Execute** the pipeline on your dataset and review the before/after comparison
6. **Download** the cleaned dataset in your preferred format (CSV, Excel, or JSON)
7. **Reuse** saved pipelines on new datasets anytime
8. **Export/Import** pipelines as JSON files for sharing

## Development Order

The project was built following the MVP specification in `Project_SPEC.md`:

1. Project setup
2. Authentication
3. Dashboard
4. File upload
5. Dataset profiling
6. Dataset overview
7. Cleaning engine
8. Transformation engine
9. Validation engine
10. Outlier detection
11. Merge engine
12. Conversion engine
13. Pipeline builder
14. Pipeline execution
15. Processing history
16. Export module
