#!/usr/bin/env python3
"""
Debug script to analyze the HTML structure of a specific model page
"""

import requests
from bs4 import BeautifulSoup

def debug_model_page():
    """Debug a specific model page to understand the image HTML structure"""
    url = "https://www.izmostock.com/izmostock/abarth-600e-electric-pack-scorpionissima-suv-2025-13-en-us.htm"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print(f"Fetching: {url}")
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Save the HTML for inspection
    with open('model_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("HTML structure analysis:")
    print("=" * 50)
    
    # Look for different types of images
    all_images = soup.find_all('img')
    print(f"Total images found: {len(all_images)}")
    
    for i, img in enumerate(all_images):
        src = img.get('src', '')
        alt = img.get('alt', '')
        width = img.get('width', '')
        height = img.get('height', '')
        print(f"Image {i+1}: src={src[:80]}... alt='{alt}' width={width} height={height}")
    
    # Look for the main image container based on the screenshot
    print("\nLooking for main image container...")
    
    # Common patterns for main car images
    for selector in [
        'img[src*="psecn.photoshelter.com"]',
        'img[src*="izmo"]',
        '.main-image img',
        '.car-image img',
        '.product-image img'
    ]:
        elements = soup.select(selector)
        if elements:
            print(f"Found {len(elements)} elements with selector: {selector}")
            for elem in elements:
                print(f"  - src: {elem.get('src', '')}")

if __name__ == "__main__":
    debug_model_page()