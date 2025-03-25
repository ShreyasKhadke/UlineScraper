# UlineScraper
# ULINE Product Data Processor

This repository contains a data processing pipeline for extracting, cleaning, and processing product data from ULINE's website. The system automatically scrapes product pages, extracts structured data from HTML tables, performs calculations, and merges the processed data with original product metadata.

## Overview

The pipeline consists of several Python scripts that work together to transform raw HTML product pages into structured data with additional computed fields. The system handles complex HTML tables, dynamic content loading, and specific business logic for calculating case quantities and pricing information.

## Features

- Web scraping with both standard HTTP requests and browser automation (Selenium)
- Intelligent HTML cleaning to extract only relevant product information
- Handling of complex HTML tables with rowspan/colspan attributes
- Multi-level header recognition and processing
- Price and case quantity calculations based on business rules
- Comprehensive logging of pipeline execution

## Pipeline Flow

1. **HTML Scraping** - Fetch product pages from URLs in the source CSV
2. **HTML Cleaning** - Remove irrelevant content, keeping only product information
3. **Table Extraction** - Convert HTML tables to structured Excel format
4. **Data Processing** - Clean and standardize data, perform calculations
5. **Data Merging** - Combine processed data with original product metadata

## Files and Components

- `main.py` - Main orchestration script that executes the pipeline steps
- `HtmlFetcher.py` - Scrapes HTML from product URLs
- `H1Cleaner.py` - Cleans HTML by extracting only relevant content
- `HtmlExtractor.py` - Extracts tables from HTML and converts to Excel
- `cleaner.py` - Processes Excel data with business logic for pricing
- `test.py` - Contains testing utilities for specific components
- `flow.txt` - Detailed explanation of the data processing flow
- `requirements.txt` - List of required Python packages

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/ShreyasKhadke/UlineScraper.git
   cd UlineScraper
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. If using Selenium, ensure Chrome is installed on your system

## Usage

1. Place your input CSV file with product URLs in the project directory:
   ```
   # Format should include columns:
   # manu_sku, product_name, prod_page_url, updated_on
   ```

2. Run the main script:
   ```
   python main.py
   ```

3. The processed data will be available in `updated_uline_scrap_products.csv`

## Customization

- To modify the scraping behavior (e.g., scrolling parameters), edit `HtmlFetcher.py`
- To change how tables are processed, modify `HtmlExtractor.py`
- To adjust price and case calculations, edit `cleaner.py`

## Outputs

The pipeline generates the following files:

- `scraped_html/` - Directory containing raw HTML files
- `cleaned_html/` - Directory containing processed HTML files
- `html_output.xlsx` - Excel file with extracted tables
- `processed_output.xlsx` - Excel file with cleaned and processed data
- `updated_uline_scrap_products.csv` - Final output CSV with merged data
- `timelog.txt` - Log file with execution timestamps

## Requirements

- Python 3.8+
- Chrome browser (for Selenium-based scraping)
- Packages listed in `requirements.txt`

## Logging

The pipeline maintains a detailed log of execution in `timelog.txt`, recording the start and end times of each processing step.
