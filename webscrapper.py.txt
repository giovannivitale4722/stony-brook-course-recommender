import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CREDITS_REGEX = re.compile(r'\b(\d+)\s*credits?\b', flags=re.I)

def get_clean_lines(content_block):
    for br in content_block.find_all("br"):
        br.replace_with("\n")
        
    text = content_block.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines()]
    return [line for line in lines if line]

def parse_course_info(lines, title_text):
    description_lines = []
    credits = "Credits not found"
    
    if lines and lines[0].strip() == title_text.strip():
        lines = lines[1:]

    for line in lines:
        line_low = line.lower()
        
        credit_match = CREDITS_REGEX.search(line_low)
        if credit_match:
            credits = credit_match.group(0)
            continue
            
        if line_low.startswith("prerequisite:") or line_low.startswith("prerequisites:"):
            continue
            
        description_lines.append(line)

    description = " ".join(description_lines).strip()
    
    if not description:
        description = "Description not found"
        
    return description, credits

def scrape_course_details(driver, url):
    try:
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "course_preview_title"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_el = soup.find(id="course_preview_title")
        course_title = title_el.get_text(strip=True) if title_el else "Title not found"

        content_block = soup.select_one("td.block_content, div.block_content")
        
        if content_block is None and title_el:
            content_block = title_el.find_parent(["td", "div"])
            
        if not content_block:
            content_block = soup.body or soup

        lines = get_clean_lines(content_block)
        description, credits = parse_course_info(lines, course_title)

        return {
            "url": url,
            "title": course_title,
            "description": description,
            "credits": credits
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def main():
    print("Setting up Selenium driver...")
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        print("Please make sure Chrome is installed.")
        return

    input_file = 'stony_brook_all_course_links.txt'
    try:
        with open(input_file, 'r') as f:
            course_urls = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: '{input_file}' not found.")
        driver.quit()
        return
    
    if not course_urls:
        print("No URLs found in file. Exiting.")
        driver.quit()
        return

    all_course_data = []
    total_courses = len(course_urls)
    print(f"Found {total_courses} courses to scrape.")

    for i, url in enumerate(course_urls, 1):
        print(f"Scraping course {i}/{total_courses}...")
        
        data = scrape_course_details(driver, url) 
        
        if data:
            all_course_data.append(data)
        
        time.sleep(0.5) 

    if not all_course_data:
        print("\nScraping finished, but no data was collected.")
    else:
        df = pd.DataFrame(all_course_data)
        output_file = 'stony_brook_all_course_data.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\nScraping complete! Collected data for {len(all_course_data)} courses.")
        print(f"Saved to '{output_file}'.")
    
    driver.quit()
    print("All done. Driver closed.")

if __name__ == "__main__":
    main()