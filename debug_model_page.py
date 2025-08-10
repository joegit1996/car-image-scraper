#!/usr/bin/env python3
"""
Debug script to analyze the HTML structure of a model page
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def debug_abarth_page():
    """Debug the abarth page to understand the model HTML structure"""
    url = "https://www.izmostock.com/izmostock/abarth-en-us.htm"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print(f"Fetching: {url}")
    response = session.get(url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Save the HTML for inspection
    with open('abarth_page.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())
    
    print("HTML structure analysis:")
    print("=" * 50)
    
    # Look for different types of links
    all_links = soup.find_all('a', href=True)
    print(f"Total links found: {len(all_links)}")
    
    # Filter links that might be models
    potential_models = []
    for link in all_links:
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Look for patterns that might indicate model pages
        if '/izmostock/' in href and 'abarth' in href.lower() and '-en-us.htm' in href:
            potential_models.append((text, href))
            print(f"Potential model: '{text}' -> {href}")
    
    print(f"\nFound {len(potential_models)} potential model links")
    
    # Look for JavaScript data
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('abarth' in script.string.lower() or 'model' in script.string.lower()):
            print(f"\nFound relevant script content: {script.string[:200]}...")

if __name__ == "__main__":
    debug_abarth_page()