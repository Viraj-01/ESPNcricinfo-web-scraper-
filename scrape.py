import csv
import re
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Headless mode for faster execution (set to False for debugging)
HEADLESS_MODE = False

# Configure Chrome
options = uc.ChromeOptions()
if HEADLESS_MODE:
    options.headless = True

# Start undetected Chrome driver
driver = uc.Chrome(options=options)

# ESPN Cricinfo match results page
url = "https://www.espncricinfo.com/records/tournament/team-match-results/ranji-trophy-2022-23-14934"

def extract_match_data():
    try:
        print(f"Scraping: {url}")
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))

        # Wait for the results table
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody")))

        # Find all rows in the results table
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        match_data = []
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")

            if len(columns) >= 7:  # Ensure all required columns exist
                team_1 = columns[0].text.strip()
                team_2 = columns[1].text.strip()
                winner = columns[2].text.strip()
                margin = columns[3].text.strip()
                ground = columns[4].text.strip()
                match_date = columns[5].text.strip()
                scorecard_link = columns[6].find_element(By.TAG_NAME, "a").get_attribute("href")

                # Extract match title and match ID
                match_title, match_id = extract_match_info(scorecard_link)

                match_data.append([match_title, match_id, team_1, team_2, winner, margin, ground, match_date, scorecard_link])
                print(f"Extracted: {match_title} | Match ID: {match_id} | {team_1} vs {team_2} | Winner: {winner}")

        return match_data

    except Exception as e:
        print(f"Error extracting data: {e}")
        return []

# Function to extract match title and match ID from the scorecard link
def extract_match_info(scorecard_url):
    # Extract match ID from the URL (last number in the link)
    match_id_match = re.search(r'(\d+)/full-scorecard$', scorecard_url)
    match_id = match_id_match.group(1) if match_id_match else "Unknown"

    # Extract match title from the URL (last part before match ID)
    match_title_match = re.search(r'/([^/]+)-(\d+)/full-scorecard$', scorecard_url)
    match_title = match_title_match.group(1).replace("-", " ").title() if match_title_match else "Unknown"

    return match_title, match_id

# Prepare CSV data
csv_data = [["Match Title", "Match ID", "Team 1", "Team 2", "Winner", "Margin", "Ground", "Match Date", "Scorecard Link"]]

# Scrape match results
try:
    match_results = extract_match_data()
    csv_data.extend(match_results)
finally:
    driver.quit()

# Save to CSV
csv_filename = "ranji_trophy_results.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)

print(f"Scraping completed. Data saved to {csv_filename}")
