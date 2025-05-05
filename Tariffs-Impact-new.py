# -*- coding: utf-8 -*-

"""
@author: alkam
Impact of Tariffs on GDP Growth, Trade Balance & FDI
Data: WB-Data-Final-H.csv (contains corrected Exports/Imports names)
Outputs:
  - pivot_data.csv
  - regression_data_full.csv
  - Combined.csv
  - regression_data.csv
  - charts/*.png
  - tariff_gdp_growth_curves.png
"""


# Importing needed libraries

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

# Intial Settings 
INPUT_CSV  = "WB-Data-Final-H.csv"
OUTPUT_DIR = "charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_style("whitegrid")
plt.rcParams["savefig.dpi"] = 300

#----------------------

#Creating the functions for the plots
def plot_time_series(df, ycol, ylabel, title, filename):
    """Time-series for USA & China with 5-year x-ticks."""
    plt.figure(figsize=(10,5))
    years = sorted(df["Year"].unique())
    for country, color in [("United States","blue"), ("China","orange")]:
        sub = df[df["Country Name"] == country]
        plt.plot(sub["Year"], sub[ycol], marker="o", color=color, label=country)
    plt.title(title)
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.xticks(range(years[0], years[-1]+1, 5))
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.show()

def plot_scatter(df, xcol, ycol, xlabel, ylabel, title, filename):
    """Scatter for USA & China."""
    plt.figure(figsize=(8,5))
    for country, color in [("United States","blue"), ("China","orange")]:
        sub = df[df["Country Name"] == country]
        plt.scatter(sub[xcol], sub[ycol], c=color, alpha=0.7,
                    edgecolors="w", s=80, label=country)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename))
    plt.show()


#----------------------

# Read and clean the CSV file
df = pd.read_csv(INPUT_CSV)

# Drop code column
for col in ["Country Code","Series Code","Unnamed: 0"]:
    if col in df.columns:
        df.drop(columns=col, inplace=True)

# Melt wide → long
long = (df.melt(id_vars=["Country Name","Series Name"],var_name="Year", value_name="Value").assign(Year = lambda d: d["Year"].str.extract(r"(\d{4})").astype(int),Value= lambda d: pd.to_numeric(d["Value"], errors="coerce")))

# Filter exactly on the main five indicators
patterns = [ r"GDP \(current US\$\)",r"Foreign direct investment, net \(BoP, current US\$\)",r"Tariff rate, applied, weighted mean, all products \(\%\)",r"Exports of goods and services \(BoP, current US\$\)",r"Imports of goods and services \(BoP, current US\$\)",]
mask = long["Series Name"].str.contains("|".join(patterns), regex=True, na=False)
filtered = long[mask]

# Pivot back to wide
pivot = (filtered.pivot_table(index=["Country Name","Year"],columns="Series Name",values="Value").reset_index())
pivot.columns.name = None

# Renaming  
pivot = pivot.rename(columns={"GDP (current US$)" : "GDP","Foreign direct investment, net (BoP, current US$)"     : "FDI","Tariff rate, applied, weighted mean, all products (%)" : "Tariff_Rate","Exports of goods and services (BoP, current US$)": "Exports","Imports of goods and services (BoP, current US$)"      : "Imports",})

# Computing Trade Balance
pivot["Trade_Balance"] = pivot["Exports"] - pivot["Imports"]

# Scale to billions
pivot["GDP_bil"] = pivot["GDP"] / 1e9
pivot["FDI_bil"] = pivot["FDI"] / 1e9
pivot["TB_bil"]  = pivot["Trade_Balance"] / 1e9

# Subset USA & China
usa_china = pivot[pivot["Country Name"].isin(["United States","China"])]


#----------------------

# Building the CSV file for the QGIS

# Country‐name fixeing so they match the shapefile
name_map = {
    "Egypt, Arab Rep.":   "Egypt",
    "Russian Federation": "Russia",
    "Turkiye":            "Turkey",
    "United States":      "United States of America"
}

# Loading the full panel 
pivot = pd.read_csv("pivot_data.csv")

# Applying the name mapping
pivot["Country Name"] = pivot["Country Name"].replace(name_map)

#Computing the 1990 vs 2015 differences
d90 = pivot[pivot.Year == 1990][
    ["Country Name", "Tariff_Rate", "FDI", "Trade_Balance"]
].copy()
d15 = pivot[pivot.Year == 2015][
    ["Country Name", "Tariff_Rate", "FDI", "Trade_Balance"]
].copy()

d90.columns = ["Country Name","Tariff_1990","FDI_1990","TB_1990"]
d15.columns = ["Country Name","Tariff_2015","FDI_2015","TB_2015"]

#Merging and then converting FDI & TB into millions (and round)

diff = d90.merge(d15, on="Country Name", how="inner")
for col in ["FDI_1990","FDI_2015","TB_1990","TB_2015"]:
    diff[col] = (diff[col] / 1_000_000).round(2)

#Computing the differences in those metrics
diff["Tariff_Diff"] = diff["Tariff_2015"] - diff["Tariff_1990"]
diff["FDI_Diff"]    = (diff["FDI_2015"]   - diff["FDI_1990"]).round(2)
diff["TB_Diff"]     = (diff["TB_2015"]    - diff["TB_1990"]).round(2)

#Extracting  the 2020 snapshot and converting FDI to millions
data20 = pivot[pivot.Year == 2020][
    ["Country Name","Tariff_Rate","FDI"]
].copy()
data20.columns = ["Country Name","Tariff_2020","FDI_2020"]
data20["FDI_2020"] = (data20["FDI_2020"] / 1_000_000).round(2)

#Computing GDP growth % 
g90 = pivot[pivot.Year == 1990][["Country Name","GDP_bil"]].rename(
    columns={"GDP_bil":"GDP_1990"}
)
g15 = pivot[pivot.Year == 2015][["Country Name","GDP_bil"]].rename(
    columns={"GDP_bil":"GDP_2015"}
)
gdp = g90.merge(g15, on="Country Name", how="inner")
gdp["GDP_GrowthPct_1990_2015"] = (
    (gdp["GDP_2015"] / gdp["GDP_1990"] - 1) * 100
).round(2)

#Merging everything into one DataFrame
combined = (
    diff
    .merge(data20, on="Country Name", how="outer")
    .merge(gdp,     on="Country Name", how="outer")
)

#Exporting the single combined CSV to be used by QGIS and other purposes 
combined.to_csv("combined_data.csv", index=False)
print(f"✓ combined_data.csv written ({len(combined)} countries)")


#---------------------------------


#Plotting the Charts using the function 
plot_time_series(usa_china, "GDP_bil",    "GDP (billion US$)", "GDP Trend: USA vs China","gdp_trend.png")
plot_time_series(usa_china, "Tariff_Rate","Tariff Rate (%)","Tariff Rate Trend: USA vs China","tariff_trend.png")
plot_time_series(usa_china, "FDI_bil",    "FDI (billion US$)","FDI Trend: USA vs China","fdi_trend.png")
plot_time_series(usa_china, "TB_bil",     "Trade Balance (billion US$)","Trade Balance: USA vs China","trade_balance_trend.png")

plot_scatter(usa_china, "Tariff_Rate","FDI_bil", "Tariff Rate (%)", "FDI (billion US$)", "Scatter: Tariff vs FDI", "scatter_tariff_fdi.png")
plot_scatter(usa_china, "Tariff_Rate","GDP_bil", "Tariff Rate (%)", "GDP (billion US$)","Scatter: Tariff vs GDP",     "scatter_tariff_gdp.png")

#--------------------------------

#preparing the final files for regression 


extra_patterns = [r"GDP growth \(annual %\)",r"Foreign direct investment, net inflows \(% of GDP\)",r"Inflation, consumer prices \(annual %\)",r"Population growth \(annual %\)"]
extra = long[ long["Series Name"].str.contains("|".join(extra_patterns), regex=True, na=False)].copy()

# Pivot the added variables:
extra_pivot = (extra.pivot_table(index=["Country Name","Year"],columns="Series Name",values="Value").reset_index())
extra_pivot.columns.name = None

# Clean‐up column names:
extra_pivot = extra_pivot.rename(columns={
"GDP growth (annual %)":"GDP_growth_pct","Foreign direct investment, net inflows (% of GDP)": "FDI_pct_gdp","Inflation, consumer prices (annual %)":"inflation","Population growth (annual %)": "pop_growth"})

# Merging the four onto main `pivot` by Country & Year:
pivot = pivot.merge(extra_pivot[["Country Name","Year","GDP_growth_pct","FDI_pct_gdp","inflation","pop_growth"]],on=["Country Name","Year"],how="left")


# Continue with  Quick check:
print("\n>> Pivot columns now include controls:")
print(pivot.columns.tolist())

#---------------------------------------

# Preparing the "full" panel for Stata:
    
full_vars = ["Country Name","Year","Tariff_Rate","GDP_growth_pct", "FDI_pct_gdp","inflation","pop_growth", "TB_bil"]

# Dropping rows with any NA in those columns:
reg_full = pivot.dropna(subset=full_vars).copy()

# Exporting for Stata:
reg_full[full_vars].to_csv("regression_data_full.csv", index=False)
print(f"  • regression_data_full.csv: {len(reg_full)} obs × {len(full_vars)} vars")

# Preparing the simple pooled-OLS panel (billions outcomes):
pooled_vars =["Country Name","Year","Tariff_Rate","GDP_bil","FDI_bil","TB_bil"]

pooled = pivot.dropna(subset=pooled_vars).copy()
pooled[pooled_vars].to_csv("regression_data.csv", index=False)
print(f"  • regression_data.csv:      {len(pooled)} obs × {len(pooled_vars)} vars")

#Quick pooled-OLS in Python (robust SE)
print("\n=== Python: Pooled OLS (billions) ===")
for yvar in ["GDP_bil","FDI_bil","TB_bil"]:
    X = sm.add_constant(pooled["Tariff_Rate"])
    y = pooled[yvar]
    m = sm.OLS(y, X).fit(cov_type="HC1")
    print(f"\nOutcome: {yvar}")
    print(m.summary().tables[1])
    
    
#-------------------------------
    
#The final relation curve based on Regression outputs     


plt.savefig("tariff_gdp_growth_curves.png", dpi=300)
plt.show()

########
import matplotlib.pyplot as plt
import numpy as np

# Coefficients from Stata
ols = {'intercept': 1.475713, 'b1': 0.2488985, 'b2': -0.0031829}
fe =  {'intercept': 2.06,      'b1': 0.1436,     'b2': -0.00214}

# Tariff range
tariff = np.linspace(0, 90, 500)

# GDP growth functions
gdp_ols = ols['intercept'] + ols['b1'] * tariff + ols['b2'] * tariff**2
gdp_fe  = fe['intercept']  + fe['b1']  * tariff + fe['b2']  * tariff**2

# Turning points
tp_ols = -ols['b1'] / (2 * ols['b2'])
tp_fe  = -fe['b1']  / (2 * fe['b2'])

# Country cases (based on OLS)
points = {
    'USA 2020': 2,
    'China 2020': 10,
    'China 2025': 85,
    'USA 2025': 100
}
colors = {'USA 2020': 'green', 'China 2020': 'blue', 'China 2025': 'red', 'USA 2025': 'purple'}

# Plot
plt.figure(figsize=(10, 6))
plt.plot(tariff, gdp_ols, label='OLS + Controls', color='blue', linewidth=2)
plt.plot(tariff, gdp_fe, '--', label='Fixed Effects', color='green', linewidth=2)
plt.axvline(tp_ols, color='blue', linestyle=':', label=f'OLS Turning ≈ {tp_ols:.1f}%')
plt.axvline(tp_fe, color='green', linestyle=':', label=f'FE Turning ≈ {tp_fe:.1f}%')

# Plot country points
for name, rate in points.items():
    gdp = ols['intercept'] + ols['b1'] * rate + ols['b2'] * rate**2
    plt.plot(rate, gdp, 'o', color=colors[name], label=name)
    plt.text(rate + 1, gdp, name, color=colors[name], fontsize=9)

# Styling
plt.title("Tariff Rate and GDP Growth: OLS vs Fixed Effects", fontsize=13)
plt.xlabel("Tariff Rate (%)")
plt.ylabel("Predicted GDP Growth (%)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("tariff_gdp_growth_curves.png", dpi=300)
plt.show()


###


