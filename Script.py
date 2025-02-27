import requests
import pandas as pd
import time

# Replace with your actual Alpha Vantage API key (sign up at https://www.alphavantage.co/)
API_KEY = 'CBLJTFA6885VIHMF'

# Define companies in the technology sector
companies = ['AAPL', 'MSFT', 'GOOGL']

# List to store data
data = []

def calculate_price_changes(price_data, report_date):
    """Calculate percentage price changes over 7 and 14 trading days after report_date."""
    dates = sorted(price_data.keys())  # Sort dates in ascending order
    try:
        # Find the first trading day on or after the report date
        start_date = next(d for d in dates if d >= report_date)
    except StopIteration:
        return None, None  # Report date is beyond available data
    start_index = dates.index(start_date)
    start_price = float(price_data[start_date]['4. close'])
    
    # Calculate 7-day price change
    change_7d = None
    if start_index + 7 < len(dates):
        price_7d = float(price_data[dates[start_index + 7]]['4. close'])
        change_7d = (price_7d - start_price) / start_price * 100
    
    # Calculate 14-day price change
    change_14d = None
    if start_index + 14 < len(dates):
        price_14d = float(price_data[dates[start_index + 14]]['4. close'])
        change_14d = (price_14d - start_price) / start_price * 100
    
    return change_7d, change_14d

# Fetch data for each company
for company in companies:
    print(f"Fetching data for {company}...")
    
    # 1. Fetch earnings data to get the latest report date
    earnings_url = f'https://www.alphavantage.co/query?function=EARNINGS&symbol={company}&apikey={API_KEY}'
    earnings_response = requests.get(earnings_url)
    earnings_data = earnings_response.json()
    if 'quarterlyEarnings' not in earnings_data:
        print(f"Error fetching earnings data for {company}")
        continue
    latest_earnings = earnings_data['quarterlyEarnings'][0]
    report_date = latest_earnings['reportedDate']
    
    # 2. Fetch P/E ratio from overview
    overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={company}&apikey={API_KEY}'
    overview_response = requests.get(overview_url)
    overview_data = overview_response.json()
    if 'PERatio' not in overview_data:
        print(f"Error fetching overview data for {company}")
        continue
    pe_ratio = float(overview_data['PERatio']) if overview_data['PERatio'] != 'None' else None
    
    # 3. Fetch revenue data from income statement
    income_url = f'https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={company}&apikey={API_KEY}'
    income_response = requests.get(income_url)
    income_data = income_response.json()
    if 'quarterlyReports' not in income_data:
        print(f"Error fetching income statement data for {company}")
        continue
    quarterly_reports = income_data['quarterlyReports']
    latest_revenue = float(quarterly_reports[0]['totalRevenue'])
    previous_revenue = float(quarterly_reports[1]['totalRevenue'])
    revenue_change = (latest_revenue - previous_revenue) / previous_revenue * 100
    
    # 4. Fetch price data
    price_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={company}&outputsize=full&apikey={API_KEY}'
    price_response = requests.get(price_url)
    price_data = price_response.json().get('Time Series (Daily)', {})
    if not price_data:
        print(f"Error fetching price data for {company}")
        continue
    
    # 5. Calculate price changes
    change_7d, change_14d = calculate_price_changes(price_data, report_date)
    
    # 6. Store data
    data.append({
        'Company': company,
        'Report Date': report_date,
        'P/E Ratio': pe_ratio,
        'Revenue Change (%)': revenue_change,
        'Price Change 7D (%)': change_7d,
        'Price Change 14D (%)': change_14d
    })
    
    # Respect API rate limits (5 requests per minute)
    time.sleep(15)

# Create DataFrame and save to CSV
df = pd.DataFrame(data)
df.to_csv('stock_data.csv', index=False)
print("Data saved to stock_data.csv")

# Analyze and summarize
print("\nAnalysis and Summary:")
for index, row in df.iterrows():
    print(f"\n{row['Company']} (Report Date: {row['Report Date']}):")
    print(f"  P/E Ratio: {row['P/E Ratio']:.2f}" if row['P/E Ratio'] else "  P/E Ratio: N/A")
    print(f"  Revenue Change: {row['Revenue Change (%)']:.2f}%")
    print(f"  Price Change 7D: {row['Price Change 7D (%)']:.2f}%" if row['Price Change 7D (%)'] else "  Price Change 7D: N/A")
    print(f"  Price Change 14D: {row['Price Change 14D (%)']:.2f}%" if row['Price Change 14D (%)'] else "  Price Change 14D: N/A")
    
    # Check for patterns
    if row['Revenue Change (%)'] > 0 and row['Price Change 7D (%)'] and row['Price Change 7D (%)'] > 0:
        print("  Pattern: Positive revenue change followed by positive 7-day price move.")
    if row['Revenue Change (%)'] > 0 and row['Price Change 14D (%)'] and row['Price Change 14D (%)'] > 0:
        print("  Pattern: Positive revenue change followed by positive 14-day price move.")

print("\nSummary of Observations:")
print("With only three companies, statistical correlation is limited. However:")
if len([row for row in data if row['Revenue Change (%)'] > 0 and row['Price Change 7D (%)'] and row['Price Change 7D (%)'] > 0]) >= 2:
    print("- Most companies showed a positive 7-day price move following revenue growth, suggesting a potential short-term trading signal.")
else:
    print("- No consistent pattern observed between revenue changes and price movements across all companies.")
print("Consider expanding the sample size or incorporating additional fundamentals (e.g., EPS surprise) for more robust insights.")