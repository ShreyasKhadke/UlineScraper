import os
import pandas as pd
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re

# Add Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def scrape_html_from_csv(csv_file, save_folder="scraped_html"):
    """
    Reads URLs from the given CSV file, scrapes their HTML, and saves them with unique filenames.
    Uses Selenium for GuidedNav URLs and requests for regular URLs.
    """
    
    # Ensure the output folder exists
    os.makedirs(save_folder, exist_ok=True)

    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Check if 'prod_page_url' column exists
        if "prod_page_url" not in df.columns:
            print("Error: 'prod_page_url' column not found in CSV.")
            return

        # Remove duplicates and NaN values
        urls = df["prod_page_url"].dropna().unique()

        for url in urls:
            filename = get_filename_from_url(url)
            file_path = os.path.join(save_folder, filename)

            if os.path.exists(file_path):
                print(f"Skipping {url} (already scraped)")
                continue  # Skip duplicate scraping

            # Check if the URL matches the GuidedNav pattern
            if "GuidedNav" in url:
                fetch_and_save_html_selenium(url, file_path)
            else:
                fetch_and_save_html(url, file_path)

    except Exception as e:
        print(f"Error processing CSV: {e}")

def get_filename_from_url(url):
    """Extracts the product name from the URL to create a filename."""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip("/").split("/")
    
    if "GuidedNav" in url:
        # For GuidedNav URLs, use the t parameter as identifier
        t_param = re.search(r't=(\d+)', url)
        if t_param:
            return f"GuidedNav_{t_param.group(1)}.html"
        else:
            return f"GuidedNav_{hash(url) % 10000}.html"  # Fallback
    
    # For regular URLs, use the last part of the path
    if path_parts and path_parts[-1]:
        return f"{path_parts[-1]}.html"
    else:
        return f"page_{hash(url) % 10000}.html"  # Fallback for unusual URLs

def fetch_and_save_html(url, file_path):
    """Fetches HTML from the given URL using requests and saves it."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"Saved (regular): {file_path}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")

def fetch_and_save_html_selenium(url, file_path, scroll_pause_time=2, max_scrolls=30, target_model="S-23318"):
    """
    Fetches HTML from the given URL using Selenium with smart scrolling and saves it.
    Stops scrolling if the target model number is found or if no more content loads.
    """
    driver = None
    try:
        print(f"Using Selenium for: {url}")
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        
        # Allow initial page load
        time.sleep(3)
        
        # Initialize tracking variables
        last_height = driver.execute_script("return document.body.scrollHeight")
        model_found = False
        scroll_count = 0
        
        while not model_found and scroll_count < max_scrolls:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_count += 1
            
            # Wait for new content to load
            time.sleep(scroll_pause_time)
            
            # Check if target model is found in the page
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for the model in table cells - adjust this selector as needed for your specific page structure
            for cell in soup.find_all('td'):
                if target_model in cell.get_text():
                    print(f"Found target model '{target_model}' after {scroll_count} scrolls!")
                    model_found = True
                    break
            
            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            # If heights are the same and we've scrolled at least once, we might have reached the end
            if new_height == last_height and scroll_count > 1:
                print(f"No more content loading after {scroll_count} scrolls.")
                # Try one more small scroll to ensure everything is loaded
                driver.execute_script("window.scrollBy(0, 300);")
                time.sleep(scroll_pause_time)
                break
                
            last_height = new_height
            print(f"Scroll {scroll_count}: Page height now {new_height}px")
        
        # Get the final page source
        page_source = driver.page_source
        
        # Save the complete HTML
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(page_source)
            
        if model_found:
            print(f"Saved (Selenium with target model found): {file_path}")
        else:
            print(f"Saved (Selenium after {scroll_count} scrolls): {file_path}")
        
    except Exception as e:
        print(f"Error fetching with Selenium {url}: {e}")
    finally:
        # Always close the driver
        if driver:
            driver.quit()

def extract_h1_texts(folder_path='scraped_html', output_file='input.txt'):
    h1_entries = []
    
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.html'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')
                h1_tags = soup.find_all('h1')
                for tag in h1_tags:
                    h1_text = tag.get_text(strip=True)
                    h1_entries.append(f"python H1Cleaner.py --input scraped_html/{filename} --heading \"{h1_text}\"")
    
    with open(output_file, 'w', encoding='utf-8') as output:
        output.write('\n'.join(h1_entries))
    
    print(f"Extracted H1 texts saved to '{output_file}'")

# Example usage:
# scrape_html_from_csv("uline_scrap_products.csv")
# extract_h1_texts()