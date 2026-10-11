# Cleaning log and six-things check

## Scope

The cleaning pipeline starts from `pkr_monthly.csv`, the compiled input supplied for this analysis. It contains **255 monthly rows and 16 columns**, covering **July 2005 to September 2026**. The input file is preserved unchanged. The original source archive was not available for inspection, so the original source, download dates, definitions, and historical data vintages cannot be independently confirmed. The script creates a cleaned file with derived fields recalculated, quality flags, lagged predictors, model-sample flags, and a data dictionary.

## Cleaning log: one paragraph per loop/cycle

**Loop 1  Check dates and duplicates.** The first check found 255 rows, zero invalid `YYYY-MM` month values, zero duplicate rows, and zero duplicate months; the dates were already in chronological order. I kept all 255 rows and did not sort or delete anything because the monthly index was already consistent. **Rows/cells changed: 0.** I rejected dropping or reordering records because there was no evidence that any row was duplicated or out of sequence.

**Loop 2  Check missing values.** The input has 118 missing values in `policy_rate` and 125 in `cpi_mom_pct`. September 2026 also has missing imports, exports, reserves, and trade balance, while the final next-month target is missing because the next month is not in the file. I left these values missing and added two flags, `incomplete_core_observation` and `incomplete_any_source_series`, so the gaps are visible. **Rows removed: 0; raw missing cells imputed: 0; two flag columns were added across 255 rows.** I rejected filling gaps with means or carrying values forward because those approaches could invent observations or imply that a value was known when it may not have been published.

**Loop 3  Recalculate month-over-month changes.** The four stored change columns (`fx_chg_pct`, `imports_growth`, `remit_growth`, and `reserves_chg_pct`) were recalculated from their underlying level series using the same formula, 100 × (current value / previous value − 1). At a tolerance of 0.000001 percentage points, 249 FX-change cells, 194 import-growth cells, 230 remittance-growth cells, and 205 reserve-change cells differed from the stored values. The differences are consistent with stored values having been rounded or calculated with a slightly different precision. **Rows removed: 0; 878 overlapping numeric cells changed beyond that tolerance across the four derived columns.** July 2005 remains missing for these calculations when the June 2005 level is not available. I rejected retaining the precomputed changes unchanged because the formula should be reproducible from the levels.

**Loop 4  Rebuild the target labels.** I recalculated `depr_this_month`, `depr_next`, and `depr_next_025` from adjacent monthly FX averages. The recalculated labels matched all previously available labels; 254 next-month targets can be calculated, with 170 depreciation labels and 84 no-depreciation labels. The last row remains missing for the two next-month targets by design. **Rows removed: 0; existing overlapping target labels changed: 0; target columns recalculated across 255 rows.** Equal FX averages are coded as no depreciation because the primary definition requires the next month's rate to be strictly higher. I rejected filling the last target or treating an unchanged rate as depreciation.

**Loop 5  Keep the repeated FX values unchanged.** April and May 2025 both have an `fx_avg` of **281.666 PKR/USD**. This is worth checking against the original exchange-rate source, but the compiled file alone does not show which value, if either, is wrong. I preserved both values. **Rows/cells changed: 0.** I rejected changing one value based on expectation alone because that would be an unsupported correction.

**Loop 6  Review extreme reserve movements.** Recalculated month-over-month reserve changes range from approximately **−43.81% to +81.34%**. These values are unusual, but without the original source series and definition, it is not possible to determine whether they are errors, real movements, or a consequence of a source/definition change. I retained the reserve levels and did not clip, winsorise, or delete observations; the reserve-change formula was recalculated as described in Loop 3. **Rows deleted: 0; reserve level cells clipped or overwritten: 0.** I rejected automatic outlier removal because an extreme value alone is not proof of a data error.

**Loop 7  Check types, units, and timing.** The month field is text in `YYYY-MM` format, and the other 15 input columns were read as numeric; the conversion check found zero non-numeric values in numeric columns. I checked plausible ranges and the identity `trade_balance_musd = exports_musd − imports_musd` for the available rows. The FX average ranges from **59.6234 to 297.754 PKR/USD** in the input. No definite unit error was established, but source units and definitions remain unverified because the original source archive could not be inspected. I added seven one-month-lagged predictors plus forecast-date, coverage, verification, model-sample, and baseline fields; release-timing and vintage verification are explicitly set to `False`. **Rows removed: 0; numeric coercion failures: 0; 22 derived/metadata columns added to the 16 input columns.** I rejected assuming that a lag automatically proves a value was public at the forecast date.

## Six-things check

### 1. Missing values  found and checked

I checked `isna()` counts for every input column. There are 118 missing values in `policy_rate`, 125 in `cpi_mom_pct`, one each in `imports_musd`, `exports_musd`, `sbp_reserves_musd`, and `trade_balance_musd` (all in the incomplete September 2026 observation), and missing values in derived changes and targets where a previous or following month is unavailable. The final next-month target is missing by design. No values were imputed; quality flags make incomplete observations easier to identify.

### 2. Duplicates  none found, after checking

I checked both complete-row duplicates (`DataFrame.duplicated()`) and repeated values in `month`. Both checks returned **0**. I also checked that parsed months are in ascending order. Since the monthly key is unique and ordered, no rows were removed or reordered.

### 3. Wrong types  none detected, after checking

I inspected the column dtypes and explicitly attempted numeric conversion on all 15 non-month columns, counting any non-missing values that became missing during conversion. The check found **0 numeric conversion failures**. The `month` field is stored as text in `YYYY-MM` format and parsed separately for validation and date calculations. No silent coercion or row deletion was needed.

### 4. Wrong units  no confirmed error, but source units remain unverified

I reviewed the recorded units and ranges, including the FX average (59.6234–297.754 PKR/USD), policy rate (5.75–22.0), and monthly CPI inflation (−2.79664% to 6.19138%). I also checked whether `trade_balance_musd` equals exports minus imports; it does for all rows where both components are available. These checks did not reveal a definite unit mismatch. However, the original source archive was unavailable, so these are internal consistency checks, not independent confirmation of the official source units or definitions. Large reserve changes were retained rather than labelled as unit errors without evidence.

### 5. Encoding  no issue detected, after checking

The input CSV was read successfully as UTF-8, and the headers and month labels were parsed without decoding errors or replacement characters. The source columns contain standard ASCII labels and `YYYY-MM` dates. The cleaning script writes its outputs as UTF-8 as well. This confirms that the file can be decoded consistently; it does not prove anything about the encoding of source files that were not available for inspection.

### 6. Drift  descriptive time variation found; not automatically treated as an error

I checked the monthly time order, compared the FX level at the beginning and end of the series, and reviewed missingness across the full period. The FX average rises from **59.6234 PKR/USD in July 2005 to 277.594 PKR/USD in September 2026**, indicating substantial time variation in the level. Missingness also varies by series, with 118 policy-rate and 125 CPI values missing, and several trade/reserve fields absent in September 2026. These patterns indicate temporal drift and differences in series coverage. They are not, by themselves, proof of incorrect data, so I did not standardise the level series, clip values, or remove later observations. For modelling, time-aware validation and checks for structural breaks are more appropriate than silently changing the data.

## Reproducibility

The pipeline is in `clean_data.py`. Keep `pkr_monthly.csv` in the same folder and run:

```bash
python clean_data.py
```

The script requires `pandas` and `numpy`. It reads but does not overwrite the input and creates:

- `A_pkr_monthly_final_cleaned.csv` — cleaned dataset (255 rows, 38 columns)
- `B_data_dictionary.csv` — one entry for every cleaned column, including type, unit, definition, source, and caveats
- `C_change_log.csv` — machine-readable summary of the cleaning decisions
- `D_missing_data_report.csv` — missing counts and percentages for each input column
- `G_reproducibility_checks.txt` — key assertions and input hash

The script includes checks for the expected input columns, 255 rows, unique/ordered months, target counts, and dictionary coverage. The result is reproducible from the supplied compiled CSV, but source-level verification and historical publication timing remain unresolved.
