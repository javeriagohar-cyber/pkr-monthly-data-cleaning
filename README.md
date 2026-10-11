# PKR/USD dataset cleaning deliverables

This folder contains the compiled raw input and a reproducible cleaning pipeline.

## Run

Install dependencies if needed:

```bash
pip install pandas numpy
```

Then run from this folder:

```bash
python clean_data.py
```

The script reads `pkr_monthly.csv` and creates the cleaned CSV, full data dictionary, change log, missing-data report, and reproducibility-check report. It does not overwrite the input.

## Important limitation

The input is the compiled `pkr_monthly.csv`; original source downloads and historical data vintages were not available for independent verification. The files clearly flag this limitation instead of claiming source-level validation.
