# UlineScraper

## Overview
This codebase implements a data processing pipeline for scraping, cleaning, and processing product data from ULINE's website. The workflow involves fetching HTML, cleaning it, extracting tables to Excel, and performing various transformations on the data.

## Process Flow

1. **HTML Scraping (HtmlFetcher.py)**
   - Reads URLs from `uline_scrap_products.csv`
   - Scrapes product pages with different approaches:
     - Regular URLs: Uses standard requests library
     - GuidedNav URLs: Uses Selenium for dynamic content loading
   - Saves HTML files to `scraped_html/` directory
   - Extracts H1 tags from HTML files to create cleaning commands in `input.txt`

2. **HTML Cleaning (H1Cleaner.py)**
   - Processes HTML files from `scraped_html/` using commands generated in `input.txt`
   - Two cleaning modes:
     - Standard HTML: Extracts content starting from a specified heading (H1 tag)
     - GuidedNav HTML: Extracts specific tables with id='tblChartBody'
   - Removes unnecessary elements like navigation bars, headers, scripts
   - Preserves product tables and CSS styling
   - Saves cleaned HTML files to `cleaned_html/` directory

3. **Table Extraction (HtmlExtractor.py)**
   - Reads all cleaned HTML files from `cleaned_html/` directory
   - Extracts tables using BeautifulSoup
   - Special handling for GuidedNav tables with multi-level headers
   - Processes complex table structures with rowspan/colspan
   - Converts tables to pandas DataFrames
   - Saves all extracted tables to `html_output.xlsx` with each HTML file as a separate sheet

4. **Data Cleaning & Processing (cleaner.py)**
   - Two-phase process:
     
     **Phase 1: clean_excel()**
     - Standardizes column names (making them lowercase)
     - Extracts MODELNO., QTY./CASE, and PRICE columns
     - Cleans price values (removing commas, extracting numeric values)
     - Removes '*' from MODELNO values
     - Adds empty CASE, Price, and Code columns
     - Saves intermediate results to a temporary file
   
     **Phase 2: update_case_and_price_columns()**
     - Updates CASE column:
       - For sheets with QTY./CASE: Multiply QTY./CASE by price multipliers
       - For sheets without QTY./CASE: Copy price multipliers directly
     - Updates Price column:
       - For sheets with QTY./CASE: Calculate QTY./CASE divided by price
     - Saves final processed data to `processed_output.xlsx`

5. **Data Merging (cleaner.py → append_case_price())**
   - Merges processed Excel data with the original CSV data
   - Links products using manu_sku (CSV) and modelno. (Excel)
   - Formats CASE and Price data as lists
   - Generates Code column (list of 'C' values matching Price list length)
   - Saves the final merged data to `updated_uline_scrap_products.csv`

## Orchestration (main.py)
The entire workflow is orchestrated by `main.py` which:
1. Executes HTML scraping
2. Extracts H1 tags to create the input.txt file
3. Processes each command in input.txt (running H1Cleaner.py)
4. Runs HtmlExtractor.py to create html_output.xlsx
5. Runs cleaner.py to process data and create final outputs
6. Maintains a detailed time log of each step

## File Relationships

- **Input Files:**
  - `uline_scrap_products.csv`: Original product data with URLs
  
- **Intermediate Files/Directories:**
  - `scraped_html/`: Raw HTML files scraped from URLs
  - `input.txt`: Generated commands for H1Cleaner.py
  - `cleaned_html/`: Cleaned HTML files
  - `html_output.xlsx`: Extracted tables from HTML
  - `temp_cleaned_output.xlsx`: Temporary file during processing
  - `processed_output.xlsx`: Processed data after cleaning
  
- **Output File:**
  - `updated_uline_scrap_products.csv`: Final product data with added CASE, Price, and Code columns

## Data Transformations

The key transformations performed are:
1. HTML → Structured tables (in Excel)
2. Raw price/quantity data → Calculated CASE values
3. Raw price/quantity data → Calculated Price values (units per dollar)
4. Product SKUs → Standardized format (removing special characters)
5. Merging processed data back with original product metadata

## Special Handling

- **GuidedNav Tables:** Special processing for tables with multi-level headers
- **Complex Tables:** Handling of rowspan and colspan attributes
- **Dynamic Content:** Using Selenium for pages that require scrolling
- **Specific Formatting Requirements:** The code implements specific business logic for calculating CASE and Price values
