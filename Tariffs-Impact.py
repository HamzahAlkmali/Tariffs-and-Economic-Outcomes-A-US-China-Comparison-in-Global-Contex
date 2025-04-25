# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 18:22:49 2025

@author: alkam
"""

# Date: 2025‑04‑19
# Project: Impact of Tariffs on GDP, Trade Balance & FDI
# Sections:
#   1. Imports & Settings
#   2. Creating the functions for trend and scateer plots
#   3. Data Reading & Cleaning
#   4. Indicator Computation & Descriptive Statistics
#   5. Export CSVs for QGIS Maps
#   6. Time‑Series Plotting & Scatter Calls
#   7. Baseline OLS Regressions


#   1 - Importing libraies 
  
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm



#Use Seaborn style for all plots and set the resoultion 
sns.set_style("whitegrid")
plt.rcParams['savefig.dpi'] = 300
#-----------------------------

#   2 - Creating the functions for trend and scateer plots
def plot_two_countries(df, col, ylabel, title, countries=("United States", "China"), filename=None):
    """Plot time series for two countries and optionally save."""
    plt.figure(figsize=(10, 5))
    for country in countries:
        sub = df[df["Country Name"] == country]
        plt.plot(sub["Year"], sub[col], marker="o", label=country)
    plt.title(title)
    plt.xlabel("Year")
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if filename:
        plt.savefig(f"charts/{filename}", dpi=300)
    plt.show()

def scatter_by_country(xcol, ycol, xlabel, ylabel, title, df, filename=None):
    """Scatter plot for USA & China and optionally save."""
    plt.figure(figsize=(8, 5))
    for country, color in [("United States", "blue"), ("China", "green")]:
        sub = df[df["Country Name"] == country]
        plt.scatter(sub[xcol], sub[ycol], c=color, alpha=0.7, label=country)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if filename:
        plt.savefig(f"charts/{filename}", dpi=300)
    plt.show()

#--------------------------

#   3 - Data Reading and cleanning 

# Read raw CSV from World Bank data
df = pd.read_csv('468bb41f-0a26-40b1-ab05-af96b387a373_Data.csv')

# Drop unneeded code columns
df = df.drop(columns=["Country Code","Series Code"], errors='ignore')


# Reshape from wide to long format
long = (df.melt(id_vars=["Country Name","Series Name"],var_name="Year", value_name="Value"))

# Extract four‐digit year and convert to integer
long["Year"] = long["Year"].str.extract(r'(\d{4})').astype(int)

# Ensure 'Value' is numeric, coercing non‐numeric to NaN
long["Value"] = pd.to_numeric(long["Value"], errors="coerce")

# Filter only the needed series 

keywords = ["GDP","direct investment","Tariff","Export","Import"]
filtered = long[long["Series Name"].str.contains('|'.join(keywords), case=False, na=False)]


# Pivot back to wide form so each series is a column
pivot = (filtered.pivot_table(index=["Country Name","Year"],columns="Series Name",values="Value").reset_index())
pivot.columns.name = None

# Rename long series names into smaller column names
pivot = pivot.rename(columns={"Exports of goods and services (current US$)"   : "Exports","Imports of goods and services (current US$)" : "Imports","GDP (current US$)" : "GDP","GDP per capita (current US$)" : "GDP Per Capita","Foreign direct investment, net (BoP, current US$)": "FDI","Tariff rate, applied, weighted mean, all products (%)": "Tariff Rate"})

# Compute Trade Balance = Exports − Imports

pivot["Trade Balance"] = pivot["Exports"] - pivot["Imports"]

#-------------------

#  4 - Indicator Computation & Descriptive Statistics

# Preserve a full panel before dropping rows
panel_full = pivot.copy()

# Add GDP in billions for plotting convenience
panel_full["GDP_billion"] = panel_full["GDP"] / 1e9

# Drop rows where GDP is zero or missing
mask = pivot["GDP"].notna() & (pivot["GDP"] != 0)
pivot_pct = pivot.loc[mask].copy()
pivot_pct["FDI_pct"] = pivot_pct["FDI"] / pivot_pct["GDP"] * 100

# Compute world median of FDI_pct by year
world_med = (pivot_pct.groupby("Year", as_index=False)["FDI_pct"].median().assign(**{"Country Name":"World Median"}))

# Creating Subsets for Plotting ------------------------------------------------
usa_china_all = panel_full[panel_full["Country Name"].isin(["United States","China"])]
usa_china_pct = pivot_pct[pivot_pct["Country Name"].isin(["United States","China"])]

#------------------------------

#   5 -  Export CSVs for QGIS Maps

# Export the full panel for attribute‐joins in QGIS

panel_full.to_csv("pivot_data.csv", index=False)

# Map 4:differences 1990-2015

d90 = pivot[pivot["Year"]==1990][["Country Name","Tariff Rate","FDI","Trade Balance"]].copy()
d15 = pivot[pivot["Year"]==2015][["Country Name","Tariff Rate","FDI","Trade Balance"]].copy()
d90.columns = ["Country Name","Tariff_1990","FDI_1990","TB_1990"]
d15.columns = ["Country Name","Tariff_2015","FDI_2015","TB_2015"]
df_diff = d90.merge(d15, on="Country Name", how="inner")
df_diff["Tariff_Diff"] = df_diff["Tariff_2015"] - df_diff["Tariff_1990"]
df_diff["FDI_Diff"]    = df_diff["FDI_2015"]    - df_diff["FDI_1990"]
df_diff["TB_Diff"]     = df_diff["TB_2015"]     - df_diff["TB_1990"]
df_diff.to_csv("diffs_1990_2015.csv", index=False)

# Map 5 & 6: Single‑Year 2020 Tariff & FDI

data2020 = pivot[pivot["Year"]==2020][["Country Name","Tariff Rate","FDI"]]
data2020.to_csv("data2020.csv", index=False)

# Map 8: GDP Growth % 1990→2015

g90 = pivot[pivot["Year"]==1990][["Country Name","GDP"]].rename(columns={"GDP":"GDP_1990"})
g15 = pivot[pivot["Year"]==2015][["Country Name","GDP"]].rename(columns={"GDP":"GDP_2015"})
df_g = g90.merge(g15, on="Country Name", how="inner")
df_g["GDP_GrowthPct"] = (df_g["GDP_2015"]/df_g["GDP_1990"] - 1)*100
df_g[["Country Name","GDP_GrowthPct"]].to_csv("gdp_growth_1990_2015.csv", index=False)

#-------------------

# 6 -  Time‑Series Plotting & Scatter Calls

# FDI_pct Trends: USA, China, World Median

fdi_trends = pd.concat([usa_china_pct[["Country Name","Year","FDI_pct"]], world_med[["Country Name","Year","FDI_pct"]]], ignore_index=True)
plt.figure(figsize=(10,6))
for name, grp in fdi_trends.groupby("Country Name"):
    plt.plot(grp["Year"], grp["FDI_pct"], marker="o", label=name)
plt.title("FDI Net Inflows (% of GDP)")
plt.xlabel("Year"); plt.ylabel("FDI (% of GDP)")
plt.legend(); plt.grid(True); plt.tight_layout(); plt.show()

# USA vs China Trends (absolute series)
plot_two_countries(usa_china_all, "GDP_billion", "GDP (billion US$)","GDP Trend: USA vs China")
plot_two_countries(usa_china_all, "Tariff Rate","Tariff Rate (%)", "Tariff Rate Trend: USA vs China")
plot_two_countries(usa_china_all, "FDI","FDI (current US$)","FDI Trend: USA vs China")
plot_two_countries(usa_china_all, "Trade Balance",  "Trade Balance (Exports - Imports)","Trade Balance: USA vs China")



# Scatter diagnostics
scatter_by_country("Tariff Rate","FDI","Tariff Rate (%)","FDI (current US$)","Scatter: Tariff Rate vs FDI",df=usa_china_all)
scatter_by_country("Tariff Rate","GDP_billion","Tariff Rate (%)","GDP (billion US$)","Scatter: Tariff Rate vs GDP", df=usa_china_all)




#----------------------


    
# 7 – Baseline OLS Regressions (scaled to billions)
reg = pivot.dropna(subset=["GDP","FDI","Trade Balance","Tariff Rate"]).copy()

# 1) scale to billions
reg["GDP_bil"] = reg["GDP"] / 1e9
reg["FDI_bil"] = reg["FDI"] / 1e9
reg["TB_bil"]  = reg["Trade Balance"] / 1e9

# 2) save trimmed file for regression
reg[["Country Name","Year","Tariff Rate","GDP_bil","FDI_bil","TB_bil"]] \
   .to_csv("regression_data.csv", index=False)
print("Wrote regression_data.csv with scaled (bil) outcomes.\n")

# 3) run pooled OLS (robust SE) on each billion‑scaled outcome
print("=== Python: Pooled OLS (billions) ===")
for yvar in ["GDP_bil", "FDI_bil", "TB_bil"]:
    X = sm.add_constant(reg["Tariff Rate"])
    y = reg[yvar]
    model = sm.OLS(y, X).fit(cov_type="HC1")       # heteroskedasticity‑robust SE

    print(f"\nOutcome: {yvar}")
    # print only the coefficient table (second table of summary)
    print(model.summary().tables[1])















