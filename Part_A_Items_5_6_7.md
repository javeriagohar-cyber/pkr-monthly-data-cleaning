# Problem Solving with Data Science: Part A, Items 5-7

Project: predicting next-month PKR depreciation for automotive importers in Pakistan.

# Item 5: EDA v1

Dataset: merged PKR/USD workbook (`data/auto_pkr_merged_dataset.xlsx`, sheet `merged_model_table`), 255 monthly rows, July 2005 to September 2026, 254 with a next-month label. Code: `part5_eda.py`.

## Charts

### Chart 1. PKR/USD rose 4.7x from July 2005 to September 2026
![Chart 1](figures/chart1_fx_log_transform.png)

*The log scale turns proportional changes into equal distances, so early and late years can be compared.*

### Chart 2. Depreciation months fell from about 8 in 10 (2005-12) to 25% in 2025-26
![Chart 2](figures/chart2_depreciation_share_by_year.png)

*The red dashed line is the full-sample share (66.9%); 2026 has only 8 labelled months.*

### Chart 3. Persistence stays about 70% accurate while always-depreciate collapses to 43%
![Chart 3](figures/chart3_baselines_by_era.png)

*Accuracy of two naive rules by era, 254 labelled months.*

### Chart 4. Most months move under 1%, but a few jump 5-14%
![Chart 4](figures/chart4_fx_change_distribution.png)

*Median monthly change is +0.16% and the maximum is +13.9%: a long right tail from sharp devaluation episodes.*

### Chart 5. Auto-related imports are a small, swinging slice of total imports (1.6%-7.6%)
![Chart 5](figures/chart5_auto_import_share.png)

*20 auto-related HS codes, January 2020 to June 2026; detail reconciles to about 96% of the balance-of-payments import line.*

## Transformation: log of the exchange rate

Chart 1 shows the exchange rate before and after taking logs. The raw level has a skewness of about 1.0 and looks as if it explodes after 2018, which hides the earlier years. I compared the skewness of several series first (total imports 0.42, remittances 0.55, reserves -0.01, auto imports 0.48), and the exchange rate level was the most skewed, so it was the one worth transforming. After the log, equal percentage moves are equal distances, so the steady drift of 2005 to 2018 and the jumps of 2018 to 2023 can be compared fairly.

## Five properties of the dataset

- **Structure.** Each row is one month (255 rows, 2005-07 to 2026-09) and the columns are levels, growth rates, lags, labels and flags. The month key is unique and ordered.
- **Granularity.** Everything is monthly, so swings within a month and the day an importer actually buys dollars are invisible. The target compares monthly averages, not the rate on a purchase date.
- **Scope.** Pakistan only. The macro series start in 2005, the vehicle-sales data in 2008 and the auto imports only in January 2020, so the automotive model has just 77 usable months (March 2020 to July 2026).
- **Temporality.** It is a time series, so order matters. Lagged predictors exist, but release timing was verified for none of the rows, so a value may not have been public on the date a forecast would be made.
- **Faithfulness.** The file is a compiled CSV and the original source downloads were not available, so only internal consistency could be checked. Auto imports reconcile to about 96% of the balance-of-payments total, so they are close but not exact.

## Confounder check

The relationship checked is whether the rupee depreciated this month versus whether it depreciates next month, sliced by era as the third variable. Overall, the chance of depreciation next month is 77% after a depreciation month and 46% after a month without depreciation. Sliced by era, the pattern holds every time but the gap changes. After a depreciation month versus a non-depreciation month, the chances were 83% vs 60% in 2005-12 (90 months), 74% vs 52% in 2013-19 (84 months), 79% vs 50% in 2020-22 (36 months) and 65% vs 25% in 2023-26 (44 months).

The persistence rule stayed 65-72% accurate in every era, but the overall share of depreciation months dropped to 43% in 2023-26. So the story did not reverse, but the era matters for how useful an always-depreciate rule is. Two cautions: the era boundaries were chosen by us, and the 2020-22 slice has only 36 months, so the differences between eras are suggestive, not proven.

## Three findings in plain words

1. A US dollar cost 59.6 rupees in July 2005 and 277.6 in September 2026, about 4.7 times as much.
2. The rupee used to weaken in most months (78% of months in 2005-12). In 2025-26 it weakened in only 25% of months, so "it always goes down" is no longer a safe bet.
3. Guessing that next month will do what this month did is right about 70% of the time, and that is the number any model has to beat.

---

# Item 6: Engagement journal

## Before I looked

Going in, I had three expectations, taken from the proposal. First, that the rupee would weaken in a clear majority of months, but that this share would be lower in recent years than in the long-run average. Second, that simply repeating this month's direction (the persistence rule) would be a hard baseline to beat, much harder than always guessing depreciation. Third, that the lagged macro predictors (remittance growth, reserve changes, import growth and auto-import growth) would each carry only a weak signal about next month's direction. I do not have a commit timestamp for these, so they should be read as stated expectations, not as pre-registered evidence.

## What I did, in order

I started from the cleaned merged workbook, which joins the PKR/USD and macro series with SBP auto-import payments and PAMA vehicle sales, and I read the cleaning log from the earlier parts so I knew what had already been decided. I looked at the shape, data types and missing-value counts, then plotted the exchange rate. On the raw scale the post-2018 jump dominated the picture, so I compared the skewness of several series, found that the exchange rate level was the most skewed (about 1.0 against roughly 0.5 or less for the others), and applied a log transformation, which I kept because it made early and late years comparable.

Next I plotted how often the rupee depreciated each year and compared the two naive baselines across eras. Then I went looking for a confounder. A dead end here: I computed the correlation of each lagged predictor with next-month depreciation, overall and by era, hoping one of them would show a clear signal that changed across periods. They were all weak (overall correlations between about -0.04 and 0.11), and the by-era numbers moved around without a clean pattern on slices of only 36 to 90 months, so I dropped that route and used the persistence relationship sliced by era instead, which gave a clearer and more interpretable result. Finally I looked at the distribution of monthly changes and at the size of auto imports relative to total imports.

## What surprised me

Three things looked odd. First, April and May 2025 have exactly the same average exchange rate (281.666). The file alone cannot show which value, if either, is wrong, so we kept both and flagged them for checking against the original source. Second, monthly reserve changes run from about -44% to +81%. I treated these as unverified rather than errors, because without the original series I cannot tell a real movement from a change of definition. Third, the share of depreciation months fell from about 78% in 2005-12 to 25% in 2025-26. I checked it by counting labelled months per year: 2026 has only 8 labelled months and none of them is a depreciation, so the pattern is real in this data but the latest period rests on small counts.

## What I revised

**Always-depreciate as a strong baseline.** I first thought a rule that always predicts depreciation would be hard to beat, because the rupee weakened in 66.9% of all labelled months. The data showed that this rule is only 43% accurate in 2023-26 and 55.8% accurate in the 77-month automotive sample, while persistence stays at about 70%. I changed my view: persistence is the main benchmark, and always-depreciate is mainly a warning about class balance.

**The 77-month automotive sample.** The proposal was unsure why 77 automotive-model months run through July 2026 when the auto-import data ends in June 2026. Checking the dates showed that the sample runs from March 2020 to July 2026, which is exactly 77 months. Growth rates need two months of data and the predictors are lagged by one month, so a July 2026 row uses June data. I changed my note from "unexplained" to "explained by lag alignment".

**A cleaning decision.** We first assumed the stored month-over-month change columns could be trusted as given. The cleaning check found that many cells differed from a recalculation using the same formula, for example 249 exchange-rate change cells beyond a tiny tolerance, consistent with rounding or different precision. We changed the pipeline to recompute the change columns from the level series so that they are reproducible, and kept the target labels, which matched the recalculation exactly.

## What I still don't trust

I would not yet bet a decision on three things. First, the timing of the data: release timing and data vintages were verified for none of the 255 rows, so I cannot say a predictor was public on the date a forecast would have been made, and a model could look better than it would have been in real use. Second, the reserves series, because of its extreme monthly swings and an unconfirmed definition. Third, the recent picture from 2025-26, which rests on only about 20 labelled months and could change quickly.

---

# Item 7: Limitations and next steps

**What this dataset cannot answer.** It shows association between monthly macro signals and the direction of next month's PKR/USD average. It cannot show causation, and it cannot say what rate an importer actually paid on a given day, since it uses monthly averages. It also leaves out drivers that may matter, such as oil prices, import duties and sales-tax changes, which have not been collected.

**Biggest risk to the framed question.** The biggest risk is a change of regime. The share of depreciation months dropped from about 78% to 25%, so a model trained on earlier years may learn a pattern that no longer holds. With only 77 usable automotive months, a gain of about five points in balanced accuracy over persistence is only a few months and could easily be luck. The compiled file also has no verified release timing, so a model could appear to use information that would not have been available in time.

**Next steps.** First, verify the repeated April and May 2025 rate and the reserves series against the original sources. Second, run walk-forward evaluation against the persistence baseline on identical months, report the number of evaluated months, and repeat under the stricter 0.25% label. Third, test whether adding lagged auto-import growth or PAMA car/jeep sales growth improves on exchange-rate-only features, changing one thing at a time and logging what was decided not to change.

---

# AI use log (Part A, items 5-7)

Tool used: Claude (Anthropic). Use was permitted by the instructor for Part A, including the journal.

Used for: drafting the structure and wording of items 5, 6 and 7; writing the plotting and summary-statistics code (`part5_eda.py`); computing the figures reported from the merged workbook; and drafting the journal text.

Output was reviewed before submission, and the numbers come directly from the merged workbook and the cleaning outputs of Parts 1-4.
