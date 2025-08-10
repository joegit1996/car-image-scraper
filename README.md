# Car Image Scraper for izmostock.com

This script scrapes all car brand and model images from izmostock.com and saves them with the naming format: `(brand_model).png`

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the scraper:
```bash
python car_scraper.py
```

## How it works

1. **Navigates to the main brands page**: `https://www.izmostock.com/car-stock-photos-by-brand-en-us.htm`
2. **Extracts all car brands** from the grid layout
3. **For each brand**: visits the brand page and extracts all available models
4. **For each model**: visits the model page and downloads the main car image
5. **Saves images** in the `car_images/` folder with the format: `BrandName_ModelName.png`

## Features

- **Respectful scraping**: Includes delays between requests to avoid overwhelming the server
- **Error handling**: Logs errors and continues with the next item
- **Duplicate prevention**: Skips downloading if the image already exists
- **Safe filenames**: Automatically sanitizes brand/model names for valid filenames
- **Progress logging**: Shows detailed progress as it scrapes

## Configuration

You can modify these settings in the `main()` function:

- `max_brands=None`: Set to `None` to scrape all 76 brands, or set to a number like `5` for testing
- `delay=1.0`: Delay between requests in seconds (be respectful to the server)
- `download_dir="car_images"`: Directory to save images

## Performance

- **76 total car brands** available for scraping
- **Thousands of car models** across all brands
- **Fast operation**: Downloads images directly from JSON data (no need to visit individual model pages)
- **Duplicate detection**: Skips downloading images that already exist
- **Error handling**: Continues scraping if individual downloads fail

## Output

Images will be saved as:
- `Abarth_Abarth_600e_Electric_Pack_Scorpionissima_SUV_2025.jpg`
- `Acura_Acura_MDX_SH-AWD_A-Spec_SUV_2026.jpg`
- `Alfa_Romeo_Alfa_Romeo_Giulia_Quadrifoglio_Base_Sedan_2025.jpg`
- etc.

All progress and errors are logged to the console. Successfully tested with 114 images downloaded from the first 5 brands.