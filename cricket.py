from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize Selenium WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent detection
driver = webdriver.Chrome(options=options)

# Load the Ranji Trophy match results page
URL = "https://www.espncricinfo.com/records/tournament/team-match-results/ranji-trophy-2022-23-14934"
driver.get(URL)

try:
    # Wait for the page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/full-scorecard')]")))

    # Extract full scorecard links
    match_links = [a.get_attribute("href") for a in driver.find_elements(By.XPATH, "//a[contains(@href, '/full-scorecard')]")]

    if match_links:
        print(f"✅ Found {len(match_links)} match links!")
        
        # Save links to file
        with open("match_links.txt", "w") as file:
            file.write("\n".join(match_links))

        print("📂 Match links saved to 'match_links.txt'")

    else:
        print("❌ No match links found. Try again.")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    driver.quit()

# Read the file and clean links
with open("match_links.txt", "r") as file:
    links = file.readlines()

# Keep only links containing '/full-scorecard' (removes extra links)
valid_links = [link.strip() for link in links if "/full-scorecard" in link]

# Remove the last 3 links if there are more than 3 links
if len(valid_links) > 3:
    valid_links = valid_links[:-3]

# Save cleaned links back to file
with open("match_links.txt", "w") as file:
    file.write("\n".join(valid_links))

print(f"✅ Cleaned {len(valid_links)} valid match links saved to 'match_links.txt'.")
