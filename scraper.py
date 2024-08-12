from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
import pandas as pd
import datetime
import time
import os

def initialize_driver():
    chrome_options = Options()
    # Set the download directory
    download_dir = os.path.join(os.getcwd(), "downloaded_docs")
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Other options remain the same
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("useAutomationextension=false")
    chrome_options.add_argument("excludeSwitches=enable-automation")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-certificate-error")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--disable-web-security")
    return webdriver.Chrome(options=chrome_options)

def initialize_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.join(os.getcwd(), "downloaded_docs"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True  # This is the key setting to download PDFs
    })
    return webdriver.Chrome(options=chrome_options)

def download_document(driver, link, download_count):
    original_window = driver.current_window_handle
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    
    metadata = {}
    try:
        driver.get(link)
        
        # Extract metadata
        title_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h2.item-page-title-field"))
        )
        title_text = title_element.text
        metadata['Document Type'] = title_text.split(':')[0].strip()
        metadata['Title'] = ':'.join(title_text.split(':')[1:]).strip()

        abstract_element = driver.find_element(By.XPATH,"//div[contains(@class, 'content dont-break-out preserve-line-breaks truncated')]")
        metadata['Abstract'] = abstract_element.text
        
        Date = driver.find_element(By.XPATH, "//span[contains(@class, 'preserve-line-breaks') and contains(@class, 'dont-break-out')]")
        metadata['Date_Published'] = Date.text
        
        url_element = driver.find_element(By.CSS_SELECTOR, "a[href^='https://hdl.handle.net']")
        metadata['URL'] = url_element.get_attribute('href')
        
        collection_element = driver.find_element(By.CSS_SELECTOR, "a[href^='/collections']")
        metadata['Collections'] = collection_element.text
        
        # Download the document
        download_link = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='dont-break-out' and @data-customlink='fd:body:en:pdf']"))
        )
        dhref = download_link.get_attribute('href')
        driver.execute_script(f"window.location.href = '{dhref}';")
        print(f"Downloading document {download_count}: {dhref}")
        time.sleep(10)  # Wait for download to start
        return True, metadata
    except Exception as e:
        print(f"Error downloading document {download_count}: {e}")
        return False, metadata
    finally:
        driver.close()
        driver.switch_to.window(original_window)

def main():
    download_path = os.path.join(os.getcwd(), "downloaded_docs")
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    driver = initialize_driver()
    base_url = "https://openknowledge.worldbank.org/search?spc.page={}&query=&f.country=India,equals&spc.rpp=5"

    total_downloads = 0
    total_attempts = 0
    
    # Create a list to store metadata
    metadata_list = []

    try:
        for page in range(1, 2):  # 14 pages in total
            driver.get(base_url.format(page))
            print(f"\nProcessing page {page}")

            WebDriverWait(driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.lead.item-list-title"))
            )

            links = driver.find_elements(By.CSS_SELECTOR, "a.lead.item-list-title")
            
            for link in links:
                total_attempts += 1
                href = link.get_attribute('href')
                success, metadata = download_document(driver, href, total_attempts)
                if success:
                    total_downloads += 1
                    metadata_list.append(metadata)
                
                print(f"Progress: {total_downloads}/{total_attempts} documents downloaded")

            time.sleep(2)  # Wait between pages

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()

    print(f"\nDownload process completed. Total documents downloaded: {total_downloads}/{total_attempts}")
    print(f"Documents are saved in: {download_path}")
    
    # Create DataFrame from the list of metadata
    df = pd.DataFrame(metadata_list)
    
    # Save the DataFrame to a CSV file
    csv_path = os.path.join(os.getcwd(), 'document_metadata.csv')
    df.to_csv(csv_path, index=False)
    print(f"Metadata saved to: {csv_path}")

if __name__ == "__main__":
    main()