from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import requests
import json
import time
import pickle

skill_dict = pickle.load(open("skill_ids.pkl", "rb"))

rarity_dict = {3: "SSR", 2: "SR", 1: "R"}

type_dict = {"speed": "Speed", "stamina": "Stamina", "power": "Power", "guts": "Guts", "intelligence": "Wit"}

def fetch_support_card_data(card_url):
    # 1) Download card page
    headers = { "User-Agent": "Mozilla/5.0" }
    res = requests.get(card_url, headers=headers)
    res.raise_for_status()
    html = res.text

    # 2) Extract Next.js JSON
    start_tag = '<script id="__NEXT_DATA__" type="application/json">'
    idx = html.find(start_tag)
    if idx == -1:
        raise RuntimeError("Next.js JSON not found in support card page")
    idx += len(start_tag)
    end = html.find("</script>", idx)
    data = json.loads(html[idx:end])
    support_data = data["props"]["pageProps"]["itemData"]
    return support_data

def get_skill_details(skill_id, global_skill_dict):
    # Many cards’ Next.js JSON embeds the global skill definitions for all possible skills
    skill_info = global_skill_dict.get(str(skill_id)) or global_skill_dict.get(skill_id)
    if not skill_info:
        return None

    name = skill_info.get("name") or skill_info.get("name_ja") or "Unknown"
    condition = skill_info.get("condition") or {}
    condition_text = condition.get("text") or condition.get("description") or ""

    return {"id": skill_id, "name": name, "condition": condition_text}


def extract_support_card_info(card_url):
    # Fetch support card JSON data
    support_data = fetch_support_card_data(card_url)

    collected_skills = [skill_dict[hint] for hint in support_data["hints"]["hint_skills"]]
    rarity = rarity_dict[support_data["rarity"]]
    if support_data["type"] not in type_dict:
        return {}
    type_ = type_dict[support_data["type"]]

    return {"character_name": support_data["char_name"],
            "rarity": rarity,
            "type": type_,
            "hint_names": collected_skills}

# --- Configuration ---
URL = "https://gametora.com/umamusume/supports"

# Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run without opening a browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")

# Initialize WebDriver
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=chrome_options
)

try:
    # Load the support card page
    driver.get(URL)
    time.sleep(5)  # Wait for JavaScript to load (adjust if needed)

    # Find all support card links
    # On inspection, each card is an <a> tag with href like /umamusume/supports/<id>-<slug>
    cards = driver.find_elements(By.CSS_SELECTOR, "a[href^='/umamusume/supports/']")

    # Collect unique links
    support_links = set()
    for card in cards:
        href = card.get_attribute("href")
        support_links.add(href)
    
    print(f"Found {len(support_links)} support cards:\n")
    entries = []
    for link in sorted(support_links):
        entries.append(extract_support_card_info(link))
    with open('hints.json', "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

finally:
    driver.quit()