#!/usr/bin/env python3
"""
Car Image Scraper for izmostock.com
Scrapes all car brand and model images from the website.
"""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CarImageScraper:
    def __init__(self, base_url: str = "https://www.izmostock.com/", download_dir: str = "car_images"):
        self.base_url = base_url
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create download directory
        os.makedirs(self.download_dir, exist_ok=True)
        
    def get_soup(self, url: str) -> BeautifulSoup:
        """Fetch URL and return BeautifulSoup object"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filename"""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)  # Replace spaces with underscores
        return filename.strip('._')
    
    def get_car_brands(self) -> List[Tuple[str, str]]:
        """Get all car brands from the main brands page"""
        brands_url = urljoin(self.base_url, "car-stock-photos-by-brand-en-us.htm")
        soup = self.get_soup(brands_url)
        
        if not soup:
            return []
        
        brands = []
        
        # The page loads brand data via JavaScript - look for the izmoStockData
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'izmoStockData' in script.string:
                script_content = script.string
                
                # Extract the brandList from the JavaScript
                import re
                import json
                
                # Find the brandList array in the JavaScript
                match = re.search(r'"brandList":\s*(\[.*?\])', script_content)
                if match:
                    try:
                        brand_list_json = match.group(1)
                        brand_data = json.loads(brand_list_json)
                        
                        for brand in brand_data:
                            brand_name = brand.get('make', '')
                            model_list_url = brand.get('modelListUrl', '')
                            
                            if brand_name and model_list_url:
                                full_url = urljoin(self.base_url, model_list_url)
                                brands.append((brand_name, full_url))
                                logger.info(f"Found brand: {brand_name} -> {full_url}")
                        
                        break
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing brand JSON: {e}")
                        continue
        
        logger.info(f"Found {len(brands)} car brands")
        return brands
    
    def get_car_models(self, brand_name: str, brand_url: str) -> List[Tuple[str, str]]:
        """Get all car models for a specific brand"""
        soup = self.get_soup(brand_url)
        
        if not soup:
            return []
        
        models = []
        
        # The page loads model data via JavaScript - look for the izmoStockData
        scripts = soup.find_all('script')
        
        for script in scripts:
            if script.string and 'izmoStockData' in script.string:
                script_content = script.string
                
                # Extract the modelList from the JavaScript
                import re
                import json
                
                # Find the modelList array in the JavaScript
                match = re.search(r'"modelList":\s*(\[.*?\])', script_content)
                if match:
                    try:
                        model_list_json = match.group(1)
                        model_data = json.loads(model_list_json)
                        
                        for model in model_data:
                            model_name = model.get('fullName', '')
                            image_url = model.get('imageUrl', '')
                            
                            if model_name and image_url:
                                models.append((model_name, image_url))
                                logger.info(f"Found model: {model_name} -> {image_url}")
                        
                        break
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing model JSON: {e}")
                        continue
        
        logger.info(f"Found {len(models)} models for {brand_name}")
        return models
    
    def download_car_image(self, brand_name: str, model_name: str, image_url: str) -> bool:
        """Download the main car image from direct image URL"""
        if not image_url:
            logger.warning(f"No image URL provided for {brand_name} {model_name}")
            return False
        
        # Create filename
        safe_brand = self.sanitize_filename(brand_name)
        safe_model = self.sanitize_filename(model_name)
        filename = f"{safe_brand}_{safe_model}.jpg"
        filepath = os.path.join(self.download_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            logger.info(f"Image already exists: {filename}")
            return True
        
        # Download image
        try:
            logger.info(f"Downloading image: {image_url}")
            img_response = self.session.get(image_url, timeout=15)
            img_response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            logger.info(f"Successfully downloaded: {filename}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            return False
    
    def scrape_all(self, max_brands: int = None, delay: float = 1.0):
        """Scrape all car brands and models"""
        logger.info("Starting car image scraping...")
        
        # Get all brands
        brands = self.get_car_brands()
        
        if not brands:
            logger.error("No brands found!")
            return
        
        if max_brands:
            brands = brands[:max_brands]
            logger.info(f"Limiting to first {max_brands} brands")
        
        total_images = 0
        
        for i, (brand_name, brand_url) in enumerate(brands, 1):
            logger.info(f"Processing brand {i}/{len(brands)}: {brand_name}")
            
            # Get models for this brand
            models = self.get_car_models(brand_name, brand_url)
            
            if not models:
                logger.warning(f"No models found for {brand_name}")
                continue
            
            # Download images for each model
            for j, (model_name, image_url) in enumerate(models, 1):
                logger.info(f"Processing model {j}/{len(models)}: {model_name}")
                
                if self.download_car_image(brand_name, model_name, image_url):
                    total_images += 1
                
                # Be respectful with delays
                time.sleep(delay)
            
            logger.info(f"Completed {brand_name}: processed {len(models)} models")
            time.sleep(delay * 2)  # Longer delay between brands
        
        logger.info(f"Scraping completed! Downloaded {total_images} images total.")


def main():
    """Main function to run the scraper"""
    scraper = CarImageScraper()
    
    # Start scraping all brands - set max_brands=None to scrape everything
    # To test with fewer brands, change max_brands to a small number like 5
    scraper.scrape_all(max_brands=None, delay=1.0)


if __name__ == "__main__":
    main()