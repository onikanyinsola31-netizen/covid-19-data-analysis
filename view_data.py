import pandas as pd

# Load data
url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
df = pd.read_csv(url)

# Save to CSV for easy viewing
df.to_csv('data/covid_data_full.csv', index=False)
print("✅ Full data saved to: data/covid_data_full.csv")

# Create a simplified version with just key info
simple_df = df[['Country/Region', 'Province/State', 'Lat', 'Long']].copy()
# Add the latest date column
date_cols = [col for col in df.columns if '/' in col]
latest_date = date_cols[-1]
simple_df['Latest_Cases'] = df[latest_date]

simple_df.to_csv('data/covid_data_simple.csv', index=False)
print("✅ Simplified data saved to: data/covid_data_simple.csv")

# Show statistics
print(f"\n📊 DATA STATISTICS:")
print(f"Total countries: {df['Country/Region'].nunique()}")
print(f"Latest date in data: {latest_date}")
print(f"Total data points: {df.shape[0] * df.shape[1]:,}")

print(f"\n🔍 First 30 countries:")
for i, country in enumerate(df['Country/Region'].unique()[:30], 1):
    print(f"{i:2}. {country}")

print(f"\n💡 To fix your dashboard, look for US name above.")
print("   Common variations: 'US', 'USA', 'United States'")
