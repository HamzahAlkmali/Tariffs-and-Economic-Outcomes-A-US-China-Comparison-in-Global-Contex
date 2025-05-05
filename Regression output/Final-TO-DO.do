*******************************************************
* tariff_gdp_analysis.do
* Impact of Tariffs on GDP Growth & Trade Balance
* Data: regression_data_full.csv
*******************************************************

clear all
set more off

* ─── Start logging ─────────────────────────────────────
log using "tariff_gdp_analysis.log", text replace

* 1. Load Data
import delimited "regression_data_full.csv", varnames(1) clear

* 2. Confirm variable names
display ">> Variable list:"
describe

* 3. Create a numeric panel ID
egen country_id = group(countryname), label

* 4. Declare panel structure
xtset country_id year
display ">> Panel declared: country_id × year"

* 5. Generate squared tariff term
gen tariff_rate_sq = tariff_rate^2

* 6. Summarize key variables
display ">> Summaries of key variables:"
summarize countryname year tariff_rate ///
          gdp_growth_pct fdi_pct_gdp inflation pop_growth tb_bil

* 7. Baseline Pooled OLS on GDP growth
display "=== 7. Baseline Pooled OLS: GDP Growth on Tariffs ==="
reg gdp_growth_pct tariff_rate, vce(cluster country_id)
est store Pooled

* 8. OLS + Controls
display "=== 8. OLS + Controls ==="
reg gdp_growth_pct tariff_rate fdi_pct_gdp inflation pop_growth, ///
    vce(cluster country_id)
est store Controls

* 9. OLS + Controls + Tariff²
display "=== 9. OLS + Controls + Tariff² ==="
reg gdp_growth_pct tariff_rate tariff_rate_sq fdi_pct_gdp inflation pop_growth, ///
    vce(cluster country_id)
est store Quad

* 10. Country Fixed Effects
display "=== 10. Country Fixed Effects ==="
xtreg gdp_growth_pct tariff_rate tariff_rate_sq fdi_pct_gdp inflation pop_growth, ///
    fe vce(cluster country_id)
est store FE_country

* 11. Time Fixed Effects
display "=== 11. Time Fixed Effects ==="
reg gdp_growth_pct tariff_rate tariff_rate_sq fdi_pct_gdp inflation pop_growth i.year, ///
    vce(cluster country_id)
est store FE_time

* 12. Two-Way Fixed Effects (Country + Time)
display "=== 12. Two-Way Fixed Effects ==="
xtreg gdp_growth_pct tariff_rate tariff_rate_sq fdi_pct_gdp inflation pop_growth i.year, ///
    fe vce(cluster country_id)
est store FE_twoway

* 13. Pooled OLS on Trade Balance (TB_bil)
display "=== 13. Pooled OLS: Trade Balance on Tariffs ==="
reg tb_bil tariff_rate tariff_rate_sq fdi_pct_gdp inflation pop_growth, ///
    vce(cluster country_id)
est store TB

* ─── Close the log ────────────────────────────────────
log close

* 14. Done
display ">> All regressions complete. Results saved in tariff_gdp_analysis.log"
exit
