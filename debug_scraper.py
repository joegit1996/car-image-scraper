#!/usr/bin/env python3
"""
Debug script to analyze the HTML structure of izmostock.com
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def debug_brands_page():
    """Debug the brands page to understand the HTML structure"""
    base_url = "https://www.izmostock.com/"
    brands_url = urljoin(base_url, "car-stock-photos-by-brand-en-us.htm")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print(f"Fetching: {brands_url}")
    response = session.get(brands_url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Save the HTML for inspection
    with open('brands_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("HTML structure analysis:")
    print("=" * 50)
    
    # Look for different types of links
    all_links = soup.find_all('a', href=True)
    print(f"Total links found: {len(all_links)}")
    
    # Filter links that might be brands
    potential_brands = []
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Look for patterns that might indicate brand pages
        if '/izmostock/' in href and '-en-us.htm' in href:
            potential_brands.append((text, href))
            print(f"Potential brand: '{text}' -> {href}")
    
    print(f"\nFound {len(potential_brands)} potential brand links")
    
    # Look for specific patterns in the HTML
    print("\nLooking for brand containers...")
    
    # Common patterns for brand grids
    for selector in [
        'div[class*="brand"]',
        'div[class*="grid"]', 
        'div[class*="card"]',
        'div[class*="item"]',
        'section',
        'article'
    ]:
        elements = soup.select(selector)
        if elements:
            print(f"Found {len(elements)} elements with selector: {selector}")
            for i, elem in enumerate(elements[:3]):  # Show first 3
                print(f"  {i+1}. {elem.name} - classes: {elem.get('class')} - text: {elem.get_text(strip=True)[:50]}...")
    
    # Look for images that might be brand logos
    images = soup.find_all('img')
    print(f"\nFound {len(images)} images")
    for img in images[:10]:  # Show first 10
        src = img.get('src', '')
        alt = img.get('alt', '')
        print(f"  Image: src={src[:50]}... alt='{alt}'")

if __name__ == "__main__":
    debug_brands_page()