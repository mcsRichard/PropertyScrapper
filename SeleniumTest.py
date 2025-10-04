from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Path to your ChromeDriver executable
service = Service('C:/Projects/Scrapper/chromedriver.exe')
driver = webdriver.Chrome(service=service)

driver.get('https://www.zoopla.co.uk/for-sale/details/69607310/')
print(driver.page_source)  # Get page HTML

# Example: Find an element
# element = driver.find_element(By.ID, 'element_id')
# print(element.text)

driver.quit()