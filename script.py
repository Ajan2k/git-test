import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GoogleMapsScraper:
    def __init__(self, headless=False):
        self.setup_driver(headless)
    
    def setup_driver(self, headless=False):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        # Standard user agent to avoid bot detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
    
    def search_location(self, query):
        """Search Google Maps for businesses"""
        search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        self.driver.get(search_url)
        time.sleep(5) # Wait for page load
        self.scroll_to_load_results()
    
    def scroll_to_load_results(self, max_scrolls=3):
        """Scroll the results pane to load more businesses"""
        try:
            # This selector targets the scrollable results pane
            scrollable_div = self.driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            for _ in range(max_scrolls):
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(2)
        except Exception as e:
            print(f"Note: Scrolling pane not found or end of list reached.")

    def extract_businesses(self):
        businesses = []
        # Find all result links
        links = self.driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        
        for link in links[:50]: # Process top 20 for safety
            try:
                # Get the name from the aria-label before clicking
                name = link.get_attribute("aria-label")
                link.click()
                time.sleep(3) # Wait for details to slide in
                
                data = {
                    'name': name,
                    'address': self.get_text_by_selector("[data-item-id='address']"),
                    'phone': self.get_text_by_selector("[data-item-id*='phone:']"),
                    'website': self.get_attr_by_selector("[data-item-id='authority']", "href"),
                    'rating': self.get_text_by_selector("span.ceis6c[aria-hidden='true']"),
                    'search_query': self.current_query
                }
                
                businesses.append(data)
                print(f"✅ Extracted: {name}")
            except Exception as e:
                print(f"⚠️ Skip: Error on one result")
                continue
        return businesses

    def get_text_by_selector(self, selector):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector).text.strip()
        except:
            return "N/A"

    def get_attr_by_selector(self, selector, attr):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector).get_attribute(attr)
        except:
            return "N/A"

    def scrape_multiple_searches(self, search_queries):
        all_businesses = []
        for query in search_queries:
            print(f"\n🔍 Searching: {query}")
            self.current_query = query
            self.search_location(query)
            businesses = self.extract_businesses()
            all_businesses.extend(businesses)
            time.sleep(5)
        return all_businesses

    def save_to_excel(self, data, filename="ai ml.xlsx"):
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        print(f"💾 Saved {len(data)} businesses to {filename}")

    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    queries = ["ai ml it companies in madurai"]
    scraper = GoogleMapsScraper(headless=False) # Keep False to see it working
    try:
        results = scraper.scrape_multiple_searches(queries)
        scraper.save_to_excel(results)
    finally:
        scraper.close()