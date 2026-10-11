# Updated Proposal: Predicting PKR Depreciation for Automotive Importers in Pakistan

## 1. Problem framing

For automotive importers in Pakistan---including assemblers, parts
importers and dealers purchasing completely built-up (CBU) vehicles or
auto parts in US dollars---we aim to predict whether the monthly average
PKR/USD exchange rate will be higher next month than this month.
Predictors will include recent exchange-rate movement, import growth,
changes in foreign-exchange reserves, remittance growth, lagged
automotive-import growth and Pakistan Automotive Manufacturers
Association (PAMA) car/jeep sales growth.

The intended user is an owner, purchasing manager or finance manager who
must decide when to buy dollars and place import orders. A monthly
output could read: "Next month: depreciation, estimated probability
72%." The signal is decision support, not a guarantee or financial
advice.

**Problem type:** Binary classification. The target is 1 if the next
month's monthly average PKR/USD rate is higher than the current month's
rate (PKR depreciation), and 0 otherwise. Evaluation will use
time-ordered walk-forward splits only.

## 2. Success metric and baseline

The primary target is balanced accuracy of at least 0.75, averaged
across walk-forward out-of-sample evaluation months. This is a proposed
success threshold, not a result already achieved. The key comparator is
a persistence baseline, and both baselines and the trained model must be
evaluated on exactly the same months.

  -----------------------------------------------------------------------
  Metric / finding        Workbook-based result   Interpretation
  ----------------------- ----------------------- -----------------------
  All labelled months     254                     The September 2026
                                                  observation has no
                                                  next-month label.

  Depreciation share      170/254 = 66.9%         The majority-class
                                                  baseline can look
                                                  strong on ordinary
                                                  accuracy.

  Always-depreciate       55.8% accuracy; 0.50    Balanced accuracy
  baseline                balanced accuracy       reveals that this rule
                                                  does not discriminate
                                                  between classes.

  Persistence baseline,   70.1% accuracy; 0.696   This is the main
  77-observation          balanced accuracy;      benchmark to beat.
  automotive sample       0.744 recall; 0.727     
                          precision               

  Stricter robustness     106/254 = 41.7%         Define depreciation as
  label                                           an increase greater
                                                  than 0.25%; re-run all
                                                  evaluation metrics
                                                  under this label.
  -----------------------------------------------------------------------

Balanced accuracy is preferred over ordinary accuracy because the target
classes are not evenly distributed and the share of depreciation months
changes over time. The secondary metrics are recall for depreciation
months and precision, with the confusion matrix reported. A false
negative---failing to flag a depreciation month---may cause an importer
to pay more rupees later, although the actual business cost depends on
the order and purchasing circumstances.

The 0.75 target is approximately five percentage points above the
persistence baseline's balanced accuracy. With a small sample, that
difference may represent only a few months. We will report the number of
evaluated months and avoid claiming a meaningful improvement if results
are unstable or do not clearly beat persistence.

## 3. Data and sample

The merged workbook contains 255 monthly rows from July 2005 through
September 2026. The target is available for 254 rows. Automotive import
details cover January 2020 through June 2026, while PAMA monthly vehicle
production and sales data cover January 2008 through June 2026. The
workbook flags 77 complete observations for the automotive model; the
complete modelling sample is not identical to the source-coverage period
because predictors use lags and the target requires a subsequent month's
exchange rate. The workbook's flagged automotive-model rows extend
through July 2026, so the final feature/target alignment should be
checked and explained in the analysis notebook before final results are
reported.

Core predictors are lagged exchange-rate change, total import growth,
remittance growth and reserve change. Automotive extensions add lagged
automotive-import growth and PAMA car/jeep sales growth. Policy rate,
CPI and trade balance are candidate extensions because those series are
present in the workbook. Oil prices, import duties and sales-tax changes
are possible future additions, but they have not been collected for this
version.

## 4. What changed from Week 1

The framing is narrowed to automotive importers because the sector's
exposure to foreign-currency purchases makes the decision more concrete.
The data now combine SBP import payments for 20 automotive-related HS
codes with PAMA vehicle production and sales. The evaluation plan uses
balanced accuracy and depreciation recall rather than relying on
ordinary accuracy alone. A walk-forward test will compare the model with
persistence and always-depreciate baselines on identical evaluation
months.

The workbook shows a changing target pattern: depreciation occurs in
66.9% of all labelled months, but only 25.0% of available labelled
months from January 2025 through August 2026. This is a warning that a
majority-class rule may not remain useful. The monthly
exchange-rate-change distributions also differ between the specified
historical and recent periods under a two-sample KS test; the p-value
should be confirmed using the team's original test code and exact
missing-data rules before the figure is reported.
