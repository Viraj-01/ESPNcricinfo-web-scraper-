import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import os

# Function to get Selenium WebDriver
def get_driver():
    options = uc.ChromeOptions()
    options.headless = False  # Set to True for headless mode
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

# Extract fielding data from dismissals
def extract_fielding_from_dismissals(dismissal, match_id, match_title, batter):
    fielding_data = []

    # Caught dismissal
    caught_match = re.search(r"c\s([^b]+)\sb", dismissal)
    if caught_match:
        fielder = caught_match.group(1).strip()
        fielding_data.append({
            "Match ID": match_id,
            "Match Title": match_title,
            "Fielder": fielder,
            "Mode": "Catch",
            "Dismissed Player": batter
        })

    # Stumped dismissal
    stumped_match = re.search(r"st\s([^b]+)\sb", dismissal)
    if stumped_match:
        fielder = stumped_match.group(1).strip()
        fielding_data.append({
            "Match ID": match_id,
            "Match Title": match_title,
            "Fielder": fielder,
            "Mode": "Stumping",
            "Dismissed Player": batter
        })

    # Run out dismissal
    runout_match = re.search(r"run out \(([^)]+)\)", dismissal)
    if runout_match:
        fielders = runout_match.group(1).strip().split('/')
        for fielder in fielders:
            fielding_data.append({
                "Match ID": match_id,
                "Match Title": match_title,
                "Fielder": fielder.strip(),
                "Mode": "Run Out",
                "Dismissed Player": batter
            })

    return fielding_data

# Scrape a single match
def scrape_match(url):
    driver = None
    batting_data = []
    bowling_data = []
    fielding_data = []

    try:
        driver = get_driver()
        print(f"🔗 Opening URL: {url}")
        driver.get(url)

        # Wait for the page to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ds-text-title-s"))
            )
        except:
            print("⚠ Page load timed out, proceeding with available content")

        time.sleep(5)  # Buffer time

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract Match ID
        match_id = url.split('/')[-2].split('-')[-1]

        # Extract Match Title
        title_element = soup.find("title")
        match_title = title_element.text.split("|")[0].strip() if title_element else "Unknown Match"

        # ----------------- EXTRACT BATTING DATA -----------------
        innings_sections = soup.find_all("div", class_=lambda x: x and "ds-rounded-lg" in x)
        team_innings_count = {}

        for section in innings_sections:
            innings_header = section.find(lambda tag: tag.name in ["h2", "span"] and "Innings" in tag.text)
            if not innings_header:
                continue

            team_name = re.sub(r'\s*\d(st|nd|rd|th)\s*', '', innings_header.text.strip()).strip()
            team_name = re.sub(r'\(T: \d+ runs\)', '', team_name).strip()

            team_innings_count[team_name] = team_innings_count.get(team_name, 0) + 1
            innings = str(team_innings_count[team_name])

            batting_table = section.find("table")
            if not batting_table:
                continue

            rows = batting_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 8:
                    dismissal_text = cols[1].text.strip() if cols[1].text.strip() else "not out"
                    batting_data.append({
                        "Match ID": match_id,
                        "Match Title": match_title,
                        "Innings": innings,
                        "Team": team_name,
                        "Player": cols[0].text.strip(),
                        "Dismissal": dismissal_text,
                        "Runs": cols[2].text.strip(),
                        "Balls Faced": cols[3].text.strip(),
                        "Fours": cols[5].text.strip(),
                        "Sixes": cols[6].text.strip(),
                        "Strike Rate": cols[7].text.strip(),
                    })

                    # Extract fielding data from dismissals
                    fielding_data.extend(extract_fielding_from_dismissals(dismissal_text, match_id, match_title, cols[0].text.strip()))

        # ----------------- EXTRACT BOWLING DATA -----------------
        for section in innings_sections:
            innings_header = section.find(lambda tag: tag.name in ["h2", "span"] and "Innings" in tag.text)
            if not innings_header:
                continue

            team_name = re.sub(r'\s*\d(st|nd|rd|th)\s*', '', innings_header.text.strip()).strip()
            team_name = re.sub(r'\(T: \d+ runs\)', '', team_name).strip()

            bowling_table = section.find_all("table")[-1]
            if not bowling_table:
                continue

            rows = bowling_table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 8:
                    bowling_data.append({
                        "Match ID": match_id,
                        "Match Title": match_title,
                        "Innings": innings,
                        "Team": team_name,
                        "Player": cols[0].text.strip(),
                        "Overs": cols[1].text.strip(),
                        "Maidens": cols[2].text.strip(),
                        "Runs Conceded": cols[3].text.strip(),
                        "Wickets": cols[4].text.strip(),
                        "Economy": cols[5].text.strip(),
                    })

        return batting_data, bowling_data, fielding_data

    except Exception as e:
        print(f"❌ Error scraping {url}: {str(e)}")
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

    return [], [], []

# Save Data to CSV
def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)

# Check and Retry Missing Links
def check_and_retry_scraping():
    csv_path = "ranji_trophy_results.csv"  # Input CSV with match links
    df = pd.read_csv(csv_path)

    # Load existing data
    scraped_matches = set()
    for file in ["batting_data.csv", "bowling_data.csv", "fielding_data.csv"]:
        if os.path.exists(file):
            df_existing = pd.read_csv(file)
            scraped_matches.update(df_existing["Match ID"].astype(str))

    missing_links = []
    for index, row in df.iterrows():
        match_url = row["Scorecard Link"]
        match_id = match_url.split('/')[-2].split('-')[-1]

        if match_id in scraped_matches:
            print(f"✅ Match {match_id} already scraped, skipping.")
            continue

        print(f"🔍 Scraping match: {match_url}")
        batting, bowling, fielding = scrape_match(match_url)

        save_to_csv(batting, "batting_data.csv")
        save_to_csv(bowling, "bowling_data.csv")
        save_to_csv(fielding, "fielding_data.csv")

    if missing_links:
        print("⚠ These links could not be scraped:", missing_links)

# Run the script
if __name__ == "__main__":
    check_and_retry_scraping()
