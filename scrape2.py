import csv
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Headless mode for faster execution
HEADLESS_MODE = False

# Configure Chrome
options = uc.ChromeOptions()
if HEADLESS_MODE:
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")

# Start undetected Chrome driver
driver = uc.Chrome(options=options)

# URLs for Wicketkeeping and Fielding stats
stats_pages = [
    {
        "url": "https://www.espncricinfo.com/records/tournament/keeping-most-dismissals-career/ranji-trophy-2022-23-14934",
        "category": "Most Dismissals (Wicketkeepers)",
        "scrape_function": "scrape_wicketkeepers"
    },
    {
        "url": "https://www.espncricinfo.com/records/tournament/fielding-most-catches-career/ranji-trophy-2022-23-14934",
        "category": "Most Catches (Fielders)",
        "scrape_function": "scrape_fielders"
    }
]

# Required field headers
header_texts = ["Category", "Player", "Span", "Mat", "Ct", "St"]

def scrape_wicketkeepers(url, category):
    """Scrape Wicketkeeping stats from ESPN Cricinfo."""
    try:
        print(f"🔄 Scraping: {category} | URL: {url}")
        driver.get(url)

        # Wait for the table to load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # Scroll to ensure all content loads
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Locate table
        table = driver.find_element(By.TAG_NAME, "table")

        # Extract table rows
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

        fielding_data = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            row_data = [col.text.strip() for col in columns]

            if len(row_data) >= 7:  # Ensure row has enough data
                player = row_data[0]
                span = row_data[1]   # Span (Season)
                matches = row_data[2]  # Mat
                catches = row_data[5]  # Ct
                stumpings = row_data[6]  # St

                # Append properly formatted data
                fielding_data.append([category, player, span, matches, catches, stumpings])
                print(f"✅ WK Extracted: {player} | {span} | {matches} | {catches} | {stumpings}")

        return fielding_data

    except Exception as e:
        print(f"❌ Error scraping {category}: {e}")
        return []

def scrape_fielders(url, category):
    """Scrape Fielding stats (excluding wicketkeepers) from ESPN Cricinfo."""
    try:
        print(f"🔄 Scraping: {category} | URL: {url}")
        driver.get(url)

        # Wait for the table to load
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # Scroll to ensure all content loads
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Locate table
        table = driver.find_element(By.TAG_NAME, "table")

        # Extract table rows
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

        fielding_data = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            row_data = [col.text.strip() for col in columns]

            if len(row_data) >= 5:  # Ensure row has enough data
                player = row_data[0]
                span = row_data[1]   # Span (Season)
                matches = row_data[2]  # Mat
                catches = row_data[4]  # Ct
                stumpings = "-"  # Fielders don't have stumpings

                # Append properly formatted data
                fielding_data.append([category, player, span, matches, catches, stumpings])
                print(f"✅ Fielder Extracted: {player} | {span} | {matches} | {catches} | {stumpings}")

        return fielding_data

    except Exception as e:
        print(f"❌ Error scraping {category}: {e}")
        return []

# Prepare CSV data
csv_data = [header_texts]  # Start with headers

# Scrape data from both pages
try:
    for page in stats_pages:
        if page["scrape_function"] == "scrape_wicketkeepers":
            scraped_data = scrape_wicketkeepers(page["url"], page["category"])
        else:
            scraped_data = scrape_fielders(page["url"], page["category"])

        if scraped_data:
            csv_data.extend(scraped_data)  # Add data rows

finally:
    # Force quit to avoid "WinError 6" issue
    try:
        driver.quit()
    except Exception as e:
        print(f"⚠️ Chrome quit error ignored: {e}")

# Save to CSV
csv_filename = "filtered_ranji_fielding_stats.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)

print(f"✅ Scraping completed. Data saved to {csv_filename} 🚀")
