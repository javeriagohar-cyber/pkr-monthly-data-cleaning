"""Reproducible cleaning pipeline for pkr_monthly.csv.

Run from this folder with:
    python clean_data.py
Requirements: pandas, numpy
The source CSV is read but never overwritten.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "pkr_monthly.csv"
CLEAN = BASE / "A_pkr_monthly_final_cleaned.csv"
DICT = BASE / "B_data_dictionary.csv"
CHANGELOG = BASE / "C_change_log.csv"
MISSING = BASE / "D_missing_data_report.csv"
CHECKS = BASE / "G_reproducibility_checks.txt"

EXPECTED_RAW_COLUMNS = [
    "month", "fx_avg", "imports_musd", "exports_musd", "remit_musd",
    "sbp_reserves_musd", "policy_rate", "cpi_mom_pct", "fx_chg_pct",
    "imports_growth", "remit_growth", "reserves_chg_pct",
    "trade_balance_musd", "depr_next", "depr_next_025", "depr_this_month"
]

# Definitions cover every column in the cleaned file. Source lineage remains
# unverified because the original source archive was not available for inspection.
META = {
"month": ("string", "YYYY-MM", "Monthly observation period.", "Compiled pkr_monthly.csv; original source mapping not verified.", "Original month label retained; checked for valid, unique, ordered monthly periods."),
"fx_avg": ("float", "PKR per USD", "Monthly average PKR per US dollar.", "Compiled pkr_monthly.csv; likely external-sector series, exact download not verified.", "April and May 2025 are both 281.666; retained pending source verification."),
"imports_musd": ("float", "USD million", "Monthly imports value.", "Compiled pkr_monthly.csv; original source mapping not verified.", "September 2026 is missing; exact valuation basis and source vintage not verified."),
"exports_musd": ("float", "USD million", "Monthly exports value.", "Compiled pkr_monthly.csv; original source mapping not verified.", "September 2026 is missing; exact valuation basis and source vintage not verified."),
"remit_musd": ("float", "USD million", "Monthly workers' remittances.", "Compiled pkr_monthly.csv; original source mapping not verified.", "Official/informal channel coverage and historical definition changes not verified."),
"sbp_reserves_musd": ("float", "USD million", "Monthly SBP foreign exchange reserves as represented in the compiled file.", "Compiled pkr_monthly.csv; original source mapping not verified.", "Definition and units need source confirmation; extreme month-to-month changes retained."),
"policy_rate": ("float", "Percent per annum", "Policy-rate level recorded in the compiled file.", "Compiled pkr_monthly.csv; original source mapping not verified.", "118 missing values; effective-date history and carry-forward convention not verified."),
"cpi_mom_pct": ("float", "Percent month-over-month", "Monthly CPI inflation rate recorded in the compiled file.", "Compiled pkr_monthly.csv; original source mapping not verified.", "125 missing values; CPI index, base-year changes, and splice method not verified."),
"fx_chg_pct": ("float", "Percent month-over-month", "100 × (fx_avg_t / fx_avg_(t-1) − 1).", "Recalculated from compiled fx_avg levels.", "First row missing because June 2005 is not included; not a source-verified real-time feature."),
"imports_growth": ("float", "Percent month-over-month", "100 × (imports_t / imports_(t-1) − 1).", "Recalculated from compiled imports_musd levels.", "Missing when current/prior imports are unavailable; September 2026 is missing."),
"remit_growth": ("float", "Percent month-over-month", "100 × (remit_t / remit_(t-1) − 1).", "Recalculated from compiled remit_musd levels.", "First row missing because June 2005 is not included."),
"reserves_chg_pct": ("float", "Percent month-over-month", "100 × (reserves_t / reserves_(t-1) − 1).", "Recalculated from compiled sbp_reserves_musd levels.", "Missing where current/prior reserve levels are missing; extremes retained without clipping."),
"trade_balance_musd": ("float", "USD million", "Exports minus imports.", "Recalculated as exports_musd − imports_musd.", "Missing if either component is missing; definition/source valuation basis not verified."),
"depr_this_month": ("float with missing", "Binary (0/1)", "1 if current month's FX average exceeds previous month's; otherwise 0.", "Recalculated from fx_avg.", "First row missing because there is no June 2005 FX value in the file."),
"depr_next": ("float with missing", "Binary (0/1)", "1 if next month's fx_avg is strictly higher than this month's; otherwise 0.", "Recalculated from adjacent fx_avg values; primary target.", "Last row missing by design; equal FX averages are classified as 0."),
"depr_next_025": ("float with missing", "Binary (0/1)", "1 if next month's FX average rises by strictly more than 0.25%; otherwise 0.", "Recalculated from adjacent fx_avg values; robustness target.", "Strict >0.25% threshold; last row missing by design."),
"prediction_date": ("date string", "YYYY-MM-DD", "Calendar month-end for the observation month; assumed forecast origin.", "Created by cleaning script.", "Month-end assumption does not prove that all input values were published by that date."),
"target_month": ("string", "YYYY-MM", "Month immediately after the observation month.", "Created by cleaning script.", "Last row has a target month label but no observed target value in the file."),
"predictor_source_month": ("string with missing", "YYYY-MM", "Month immediately before the observation month, used as a conservative lag period.", "Created by cleaning script.", "A lagged month is not proof of actual release availability."),
"incomplete_core_observation": ("boolean", "True/False", "True if any of fx_avg, imports_musd, remit_musd, or sbp_reserves_musd is missing.", "Created by cleaning script.", "Marks incomplete core inputs; does not delete the observation."),
"incomplete_any_source_series": ("boolean", "True/False", "True if any of the listed FX, trade, remittance, reserves, policy-rate, or CPI series is missing.", "Created by cleaning script.", "An optional series can make this flag True even if core inputs are present."),
"release_timing_verified": ("boolean", "True/False", "Whether historical release timing was verified.", "Created by audit; False for all observations.", "Historical release calendars were not available for verification."),
"data_vintage_verified": ("boolean", "True/False", "Whether historical real-time data vintages were verified.", "Created by audit; False for all observations.", "Revisions since original publication cannot be ruled out."),
"source_verification_status": ("string", "Text", "Status of source-level verification.", "Created by cleaning script.", "States that only the compiled CSV was available; not evidence of official source verification."),
"fx_chg_pct_lag1": ("float with missing", "Percent month-over-month", "Previous row's fx_chg_pct.", "Created by shifting recalculated fx_chg_pct by one month.", "Conservative timing proxy only; source release date not verified."),
"imports_growth_lag1": ("float with missing", "Percent month-over-month", "Previous row's imports_growth.", "Created by shifting recalculated imports_growth by one month.", "Missing values remain missing; source release date not verified."),
"remit_growth_lag1": ("float with missing", "Percent month-over-month", "Previous row's remit_growth.", "Created by shifting recalculated remit_growth by one month.", "Source release date and historical definitions not verified."),
"reserves_chg_pct_lag1": ("float with missing", "Percent month-over-month", "Previous row's reserves_chg_pct.", "Created by shifting recalculated reserves_chg_pct by one month.", "Source release date and reserve definition not verified."),
"trade_balance_musd_lag1": ("float with missing", "USD million", "Previous row's trade balance.", "Created by shifting recalculated trade_balance_musd by one month.", "Lag does not establish real-time availability."),
"policy_rate_lag1": ("float with missing", "Percent per annum", "Previous row's policy-rate level.", "Created by shifting policy_rate by one month.", "No extra forward-filling; effective-date history not verified."),
"cpi_mom_pct_lag1": ("float with missing", "Percent month-over-month", "Previous row's CPI inflation value.", "Created by shifting cpi_mom_pct by one month.", "CPI base-year/splice and release date not verified."),
"core_model_complete": ("boolean", "True/False", "True if all four lagged core predictors and depr_next are present.", "Created by cleaning script.", "Defines a complete-case sample for a specified model, not the full dataset."),
"core_trade_model_complete": ("boolean", "True/False", "True if lagged core predictors, lagged trade balance, and depr_next are present.", "Created by cleaning script.", "Use identical held-out months when comparing models."),
"policy_extension_complete": ("boolean", "True/False", "True if lagged core predictors, lagged policy rate, and depr_next are present.", "Created by cleaning script.", "Policy-rate missingness limits sample coverage."),
"cpi_extension_complete": ("boolean", "True/False", "True if lagged core predictors, lagged CPI, and depr_next are present.", "Created by cleaning script.", "CPI missingness limits sample coverage."),
"policy_cpi_extension_complete": ("boolean", "True/False", "True if lagged core predictors, lagged policy rate, lagged CPI, and depr_next are present.", "Created by cleaning script.", "Complete-case subset may differ from other model samples."),
"always_depreciate_baseline": ("float with missing", "Binary (0/1)", "Naive baseline prediction of depreciation whenever the target is known.", "Created by cleaning script.", "Descriptive baseline only; not an out-of-sample model result."),
"persistence_baseline": ("float with missing", "Binary (0/1)", "Baseline prediction equal to current-month depreciation direction when target is known.", "Created by cleaning script from depr_this_month.", "Descriptive baseline only; missing when current direction or target is unavailable."),
}


def pct_change(level: pd.Series) -> pd.Series:
    prev = level.shift(1)
    out = (level / prev - 1.0) * 100.0
    return out.where(prev.notna() & level.notna() & prev.ne(0))


def write_dictionary(columns):
    rows = []
    for col in columns:
        if col not in META:
            raise ValueError(f"No dictionary metadata for column: {col}")
        typ, unit, definition, source, caveats = META[col]
        rows.append({"column": col, "type": typ, "unit": unit, "definition": definition,
                     "source": source, "caveats": caveats})
    pd.DataFrame(rows).to_csv(DICT, index=False, encoding="utf-8")


def main():
    if not RAW.exists():
        raise FileNotFoundError(f"Place pkr_monthly.csv beside this script: {RAW}")
    raw_bytes = RAW.read_bytes()
    raw_hash = hashlib.sha256(raw_bytes).hexdigest()
    df = pd.read_csv(RAW, encoding="utf-8")
    if list(df.columns) != EXPECTED_RAW_COLUMNS:
        raise ValueError("Raw file columns differ from the expected 16-column input. Inspect before proceeding.")
    original = df.copy(deep=True)
    if len(df) != 255:
        raise ValueError(f"Expected 255 rows; found {len(df)}. Inspect input before proceeding.")

    # Validate month values and chronology without silently sorting or dropping rows.
    parsed = pd.to_datetime(df["month"], format="%Y-%m", errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"Invalid month strings found: {int(parsed.isna().sum())}")
    duplicate_rows = int(df.duplicated().sum())
    duplicate_months = int(df["month"].duplicated().sum())
    if duplicate_rows or duplicate_months:
        raise ValueError(f"Duplicates detected: rows={duplicate_rows}, months={duplicate_months}; review before cleaning.")
    if not parsed.is_monotonic_increasing:
        raise ValueError("Months are not chronological; script stops rather than silently reordering rows.")

    # Convert expected numeric fields with explicit failure checks.
    numeric_cols = [c for c in EXPECTED_RAW_COLUMNS if c not in ("month",)]
    coercion_failures = {}
    for col in numeric_cols:
        before_nonmissing = df[col].notna()
        converted = pd.to_numeric(df[col], errors="coerce")
        coercion_failures[col] = int((before_nonmissing & converted.isna()).sum())
        df[col] = converted
    if sum(coercion_failures.values()) > 0:
        raise ValueError(f"Non-numeric values found in numeric columns: {coercion_failures}")

    # Recalculate formula-derived fields from their source levels.
    old_derived = df[["fx_chg_pct", "imports_growth", "remit_growth", "reserves_chg_pct",
                      "trade_balance_musd", "depr_this_month", "depr_next", "depr_next_025"]].copy()
    df["fx_chg_pct"] = pct_change(df["fx_avg"])
    df["imports_growth"] = pct_change(df["imports_musd"])
    df["remit_growth"] = pct_change(df["remit_musd"])
    df["reserves_chg_pct"] = pct_change(df["sbp_reserves_musd"])
    df["trade_balance_musd"] = df["exports_musd"] - df["imports_musd"]
    current_change = df["fx_avg"] > df["fx_avg"].shift(1)
    df["depr_this_month"] = current_change.astype(float).where(df["fx_avg"].notna() & df["fx_avg"].shift(1).notna())
    next_change_pct = (df["fx_avg"].shift(-1) / df["fx_avg"] - 1.0) * 100.0
    target_known = df["fx_avg"].notna() & df["fx_avg"].shift(-1).notna()
    df["depr_next"] = (df["fx_avg"].shift(-1) > df["fx_avg"]).astype(float).where(target_known)
    df["depr_next_025"] = (next_change_pct > 0.25).astype(float).where(target_known & next_change_pct.notna())

    # Forecast and data-quality metadata.
    df["prediction_date"] = (parsed + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
    df["target_month"] = (parsed + pd.offsets.MonthBegin(1)).dt.strftime("%Y-%m")
    df["predictor_source_month"] = parsed.shift(1).dt.strftime("%Y-%m")
    core = ["fx_avg", "imports_musd", "remit_musd", "sbp_reserves_musd"]
    all_source = ["fx_avg", "imports_musd", "exports_musd", "remit_musd", "sbp_reserves_musd", "policy_rate", "cpi_mom_pct"]
    df["incomplete_core_observation"] = df[core].isna().any(axis=1)
    df["incomplete_any_source_series"] = df[all_source].isna().any(axis=1)
    df["release_timing_verified"] = False
    df["data_vintage_verified"] = False
    df["source_verification_status"] = "Compiled CSV only; original archive could not be inspected"

    lag_map = {
        "fx_chg_pct_lag1": "fx_chg_pct",
        "imports_growth_lag1": "imports_growth",
        "remit_growth_lag1": "remit_growth",
        "reserves_chg_pct_lag1": "reserves_chg_pct",
        "trade_balance_musd_lag1": "trade_balance_musd",
        "policy_rate_lag1": "policy_rate",
        "cpi_mom_pct_lag1": "cpi_mom_pct",
    }
    for new, source in lag_map.items():
        df[new] = df[source].shift(1)

    lagged_core = ["fx_chg_pct_lag1", "imports_growth_lag1", "remit_growth_lag1", "reserves_chg_pct_lag1"]
    known_target = df["depr_next"].notna()
    df["core_model_complete"] = df[lagged_core].notna().all(axis=1) & known_target
    df["core_trade_model_complete"] = df[lagged_core + ["trade_balance_musd_lag1"]].notna().all(axis=1) & known_target
    df["policy_extension_complete"] = df[lagged_core + ["policy_rate_lag1"]].notna().all(axis=1) & known_target
    df["cpi_extension_complete"] = df[lagged_core + ["cpi_mom_pct_lag1"]].notna().all(axis=1) & known_target
    df["policy_cpi_extension_complete"] = df[lagged_core + ["policy_rate_lag1", "cpi_mom_pct_lag1"]].notna().all(axis=1) & known_target
    df["always_depreciate_baseline"] = pd.Series(np.where(known_target, 1.0, np.nan), index=df.index)
    df["persistence_baseline"] = df["depr_this_month"].where(known_target & df["depr_this_month"].notna())

    ordered = EXPECTED_RAW_COLUMNS + [
        "prediction_date", "target_month", "predictor_source_month", "incomplete_core_observation",
        "incomplete_any_source_series", "release_timing_verified", "data_vintage_verified",
        "source_verification_status", "fx_chg_pct_lag1", "imports_growth_lag1", "remit_growth_lag1",
        "reserves_chg_pct_lag1", "trade_balance_musd_lag1", "policy_rate_lag1", "cpi_mom_pct_lag1",
        "core_model_complete", "core_trade_model_complete", "policy_extension_complete",
        "cpi_extension_complete", "policy_cpi_extension_complete", "always_depreciate_baseline",
        "persistence_baseline"
    ]
    df = df[ordered]
    df.to_csv(CLEAN, index=False, encoding="utf-8", float_format="%.10g")
    write_dictionary(ordered)

    # Reproducible change log, including decisions not to alter uncertain values.
    change_rows = [
      {"entry":"1", "item":"Month field and row order", "finding":"255 rows; 0 invalid month strings; 0 duplicate months; months are chronological.", "decision":"Retain all rows and original month labels.", "rows_or_cells_changed":"0 raw rows; 0 raw month cells.", "alternative_rejected":"Dropping or sorting rows was unnecessary and could hide an input issue."},
      {"entry":"2", "item":"Missing values", "finding":f"policy_rate has {int(original.policy_rate.isna().sum())} missing values; cpi_mom_pct has {int(original.cpi_mom_pct.isna().sum())}; September 2026 lacks imports, exports, reserves, and trade balance.", "decision":"Keep missing values missing and add incompleteness flags.", "rows_or_cells_changed":"0 raw missing cells imputed; 2 quality-flag columns added for all 255 rows.", "alternative_rejected":"Mean/forward-fill imputation was rejected because it could fabricate historical observations."},
      {"entry":"3", "item":"Month-over-month changes", "finding":"Four change/growth columns are formula-derived; July 2005 lacks the prior June 2005 level.", "decision":"Recalculate from current and previous source levels.", "rows_or_cells_changed":"4 derived columns recalculated across 255 rows; missing values preserved where inputs are unavailable.", "alternative_rejected":"Keeping rounded or inconsistent precomputed changes was rejected in favour of a reproducible formula."},
      {"entry":"4", "item":"Targets and direction labels", "finding":"254 next-month labels can be calculated; final row has no next-month observation; April and May 2025 FX averages are equal.", "decision":"Recalculate both targets using strict definitions; equal next/current rates are coded 0.", "rows_or_cells_changed":"3 label columns recalculated across 255 rows; final depr_next and depr_next_025 remain missing by design.", "alternative_rejected":"Filling the final target or classifying an equal rate as depreciation was rejected."},
      {"entry":"5", "item":"Repeated FX average in April–May 2025 (no change made)", "finding":"Both months show fx_avg = 281.666 PKR/USD.", "decision":"Preserve both values until the original source can be checked.", "rows_or_cells_changed":"0 rows; 0 fx_avg cells changed.", "alternative_rejected":"Changing one month based on expectation alone was rejected because no verified evidence identifies which value, if either, is wrong."},
      {"entry":"6", "item":"Extreme reserve changes (no change made)", "finding":"Recalculated monthly reserve changes range from approximately -43.81% to +81.34%.", "decision":"Retain all values and do not clip or delete observations.", "rows_or_cells_changed":"0 rows deleted; 0 reserve levels clipped or overwritten; derived reserve-change column recalculated.", "alternative_rejected":"Automatic winsorisation/deletion was rejected because an extreme value is not by itself proof of error."},
      {"entry":"7", "item":"Types, units, and model timing", "finding":"Numeric columns are already numeric; no numeric coercion failures; unit/source documentation is incomplete.", "decision":"Check types, retain stated units as provisional, add one-month lag predictors and timing-verification flags set to False.", "rows_or_cells_changed":"0 numeric values changed by type conversion; 22 derived/metadata columns added to the 16 input columns.", "alternative_rejected":"Assuming source units, real-time publication, or historical vintages were verified was rejected."},
    ]
    pd.DataFrame(change_rows).to_csv(CHANGELOG, index=False, encoding="utf-8")

    miss = pd.DataFrame({"column": original.columns, "missing_count": original.isna().sum().values,
                         "missing_percent": (original.isna().mean().values * 100).round(3),
                         "rows": len(original)})
    miss.to_csv(MISSING, index=False, encoding="utf-8")

    # Key assertions and checks that are easy to rerun.
    assert len(df) == 255
    assert df["month"].is_unique
    assert df["depr_next"].notna().sum() == 254
    assert int(df["depr_next"].sum()) == 170
    assert int((df["depr_next"] == 0).sum()) == 84
    assert pd.isna(df.iloc[-1]["depr_next"])
    assert len(META) == len(ordered) and set(META) == set(ordered)
    report = {
      "input_file": RAW.name,
      "input_sha256": raw_hash,
      "input_shape": [int(original.shape[0]), int(original.shape[1])],
      "output_shape": [int(df.shape[0]), int(df.shape[1])],
      "period": [df.month.iloc[0], df.month.iloc[-1]],
      "duplicate_rows": duplicate_rows,
      "duplicate_months": duplicate_months,
      "numeric_conversion_failures": coercion_failures,
      "missing_input_cells": int(original.isna().sum().sum()),
      "known_depr_next": int(df.depr_next.notna().sum()),
      "depreciation_labels": int(df.depr_next.sum()),
      "no_depreciation_labels": int((df.depr_next == 0).sum()),
      "source_release_timing_verified_rows": int(df.release_timing_verified.sum()),
      "data_vintage_verified_rows": int(df.data_vintage_verified.sum()),
      "output_columns": ordered,
    }
    CHECKS.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["input_shape", "output_shape", "period", "duplicate_rows", "duplicate_months", "known_depr_next", "depreciation_labels", "no_depreciation_labels"]}, indent=2))
    print(f"Wrote: {CLEAN.name}, {DICT.name}, {CHANGELOG.name}, {MISSING.name}, {CHECKS.name}")

if __name__ == "__main__":
    main()
