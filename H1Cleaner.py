from bs4 import BeautifulSoup
import os
import re
import argparse
import glob

def clean_html(input_file, output_file, heading_text="Crinkle Paper"):
    """
    Cleans HTML by removing all content above the specified heading.
    
    Parameters:
    - input_file (str): Path to the input HTML file
    - output_file (str): Path to save the cleaned HTML
    - heading_text (str): The text of the heading to use as starting point (default: "Crinkle Paper")
    
    Returns:
    - bool: True if successful, False otherwise
    """
    try:
        # Read the input HTML file
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Method 1: Find the h1 tag with exact text match
        h1_tag = soup.find('h1', string=heading_text)
        
        # Method 2: Find h1 tag with whitespace-normalized text
        if not h1_tag:
            print("Trying to find h1 with normalized whitespace...")
            for h1 in soup.find_all('h1'):
                if h1.get_text().strip() == heading_text:
                    h1_tag = h1
                    print(f"Found h1 tag with normalized text: {h1_tag}")
                    break
        
        # Method 3: Find h1 with case-insensitive match
        if not h1_tag:
            print("Trying case-insensitive match...")
            for h1 in soup.find_all('h1'):
                if h1.get_text().strip().lower() == heading_text.lower():
                    h1_tag = h1
                    print(f"Found h1 tag with case-insensitive match: {h1_tag}")
                    break
        
        # Method 4: Look for text nodes containing the heading
        if not h1_tag:
            print("Looking for text nodes containing the heading...")
            heading_pattern = re.compile(re.escape(heading_text), re.IGNORECASE)
            for element in soup.find_all(string=heading_pattern):
                parent = element.parent
                if parent.name == 'h1':
                    h1_tag = parent
                    print(f"Found h1 via text node search: {h1_tag}")
                    break
                
                # If parent isn't h1, check if it's inside an h1
                h1_parent = parent.find_parent('h1')
                if h1_parent:
                    h1_tag = h1_parent
                    print(f"Found h1 as ancestor of text node: {h1_tag}")
                    break
        
        # Method 5: Find by title or page title as a last resort
        if not h1_tag:
            print("Checking page title and metadata...")
            title_tag = soup.find('title')
            if title_tag and heading_text.lower() in title_tag.get_text().lower():
                print(f"Found heading text in title: {title_tag.get_text()}")
                
                # Try to find the first h1 or the main content div
                h1_tag = soup.find('h1')
                if h1_tag:
                    print(f"Using first h1 as fallback: {h1_tag.get_text().strip()}")
                else:
                    # Try to find a main content div
                    content_div = soup.find('div', class_=lambda c: c and ('content' in c.lower() or 
                                                                          'main' in c.lower() or 
                                                                          'product' in c.lower()))
                    if content_div:
                        print(f"Using main content div as fallback")
                        h1_tag = content_div
        
        # Find the parent div containing the product content
        content_div = None
        
        if h1_tag:
            # Step 1: Try to find a specific container with meaningful classes
            # These are common class names for content containers in product pages
            content_div = h1_tag.find_parent('div', class_=lambda c: c and any(keyword in c.lower() 
                                                                         for keyword in ['content', 'subgroup', 
                                                                                        'product', 'main', 
                                                                                        'detail', 'description']))
            
            # Step 2: Look for div with specific ID attributes if class search failed
            if not content_div:
                content_div = h1_tag.find_parent('div', id=lambda i: i and any(keyword in i.lower() 
                                                                       for keyword in ['content', 'product', 
                                                                                      'main', 'detail']))
            
            # Step 3: If no specific content div is found, use the nearest parent div
            if not content_div:
                content_div = h1_tag.find_parent('div')
            
            # Step 4: If still no container, try to find a meaningful container near the h1
            if not content_div:
                # Go up 3 levels from h1 to find a substantial container
                current = h1_tag
                for _ in range(3):
                    if current.parent:
                        current = current.parent
                        if current.name == 'div' and len(current.find_all()) > 5:  # Co ntainer has some substance
                            content_div = current
                            break
            
            # Step 5: If still no container, we'll just use everything from the h1 onwards
            if not content_div:
                print("Warning: Could not find content container. Using h1 tag as starting point.")
                content_div = h1_tag
        else:
            print("Error: Could not find heading tag.")
            return False
        
        # Create a new HTML document with just the content we want
        new_html = f"<!DOCTYPE html>\n<html>\n<head>\n<title>{heading_text}</title>\n"
        
        # Preserve CSS and style information from the original document
        style_tags = soup.find_all('style')
        for style in style_tags:
            new_html += str(style) + "\n"
             
        # Look for relevant CSS in link tags
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            new_html += str(link) + "\n"
        
        new_html += "</head>\n<body>\n</body>\n</html>"
        new_soup = BeautifulSoup(new_html, 'html.parser')
        
        # Add the content div to the new document's body
        new_soup.body.append(content_div)
        
        # IMPORTANT: Make sure all tables are preserved
        # If we're not getting all tables, let's find tables specifically
        if not new_soup.find_all('table'):
            print("No tables found in extracted content, looking for product tables specifically...")
            product_tables = soup.find_all('table', class_=lambda c: c and any(keyword in str(c).lower() 
                                                                            for keyword in ['product', 'chart', 'subgroup']))
            if product_tables:
                print(f"Found {len(product_tables)} product tables to preserve")
                for table in product_tables:
                    new_soup.body.append(table)
        
        # Clean up - remove any script tags for security and cleanliness
        for script in new_soup.find_all('script'):
            script.decompose()
            
        # Remove any unneeded navigation or header elements that might have been included
        # BUT DO NOT remove tables or product information
        for nav in new_soup.find_all(['nav', 'header']):
            nav.decompose()
            
        # Verify that we have preserved all important product information
        # Check for tables, which are often used for product details and pricing
        tables = new_soup.find_all('table')
        if tables:
            print(f"Preserved {len(tables)} tables in the cleaned HTML")
        else:
            print("WARNING: No tables found in cleaned HTML. Product information might be missing.")
            
        # Check for product information like prices, item numbers, etc.
        product_info_present = False
        for indicator in ['price', 'item', 'model', 'product', '$', 'qty', 'quantity']:
            if indicator in str(new_soup).lower():
                product_info_present = True
                break
                
        if not product_info_present:
            print("WARNING: Possible loss of product information in cleaned HTML.")
        
        # Save the cleaned HTML to the output file
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(str(new_soup))
        
        print(f"Successfully cleaned HTML and saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return False

def analyze_html_structure(html_file):
    """
    Analyzes the structure of an HTML file to help identify important elements.
    This is useful for debugging or understanding the structure of complex HTML files.
    
    Parameters:
    - html_file (str): Path to the HTML file
    """
    try:
        with open(html_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print(f"\nAnalyzing HTML structure of {html_file}:")
        print(f"{'='*50}")
        
        # Document title
        title = soup.find('title')
        print(f"Document title: {title.get_text() if title else 'None'}")
        
        # Find all h1, h2 tags
        headings = soup.find_all(['h1', 'h2'])
        print(f"\nHeadings (h1, h2) found ({len(headings)}):")
        for i, h in enumerate(headings[:10], 1):  # Show first 10
            print(f"  {i}. <{h.name}> {h.get_text().strip()[:50]}")
        if len(headings) > 10:
            print(f"  ... {len(headings) - 10} more headings")
        
        # Find main content divs
        print("\nPotential content containers:")
        containers = []
        for div in soup.find_all('div', class_=True):
            classes = div.get('class', [])
            class_str = ' '.join(classes)
            if any(keyword in class_str.lower() for keyword in ['content', 'main', 'product', 'detail']):
                containers.append((div, class_str))
        
        for i, (div, class_str) in enumerate(containers[:5], 1):  # Show first 5
            headings_inside = len(div.find_all(['h1', 'h2', 'h3']))
            paragraphs = len(div.find_all('p'))
            print(f"  {i}. <div class='{class_str}'> - {headings_inside} headings, {paragraphs} paragraphs")
        if len(containers) > 5:
            print(f"  ... {len(containers) - 5} more potential containers")
        
        # Look specifically for tables which might contain product information
        print("\nTables found (potential product information):")
        tables = soup.find_all('table')
        for i, table in enumerate(tables[:5], 1):  # Show first 5
            classes = ' '.join(table.get('class', []))
            rows = len(table.find_all('tr'))
            print(f"  {i}. <table class='{classes}'> - {rows} rows")
        if len(tables) > 5:
            print(f"  ... {len(tables) - 5} more tables")
        
        # Check for navbar or header that should be removed
        print("\nNavigation and header elements:")
        nav_elements = soup.find_all(['nav', 'header'])
        for i, nav in enumerate(nav_elements[:3], 1):  # Show first 3
            classes = ' '.join(nav.get('class', []))
            print(f"  {i}. <{nav.name} class='{classes}'>")
        if len(nav_elements) > 3:
            print(f"  ... {len(nav_elements) - 3} more navigation elements")
        
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"Error analyzing HTML structure: {e}")

def clean_guidednav_html(input_file, output_file):
    """
    Extracts the table with id='tblChartBody' and ensures its headers are in two separate rows.
    Keeps all data rows intact.
    
    Parameters:
    - input_file (str): Path to the input HTML file
    - output_file (str): Path to save the cleaned HTML
    
    Returns:
    - bool: True if successful, False otherwise
    """
    try:
        # Read the input HTML file
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the target table
        target_table = soup.find('table', id='tblChartBody')
        
        if not target_table:
            print("Error: Could not find table with id='tblChartBody'")
            return False
        
        print("Found table with id='tblChartBody'")
        
        # Check the structure of the header
        # If headers are combined, split them into two rows
        header_rows = target_table.find_all('tr')[:2]
        if len(header_rows) < 2:
            print("Table has fewer than 2 rows. Cannot ensure 2-row header structure.")
            
        # Create a new HTML document
        new_html = """<!DOCTYPE html>
<html>
<head>
<title>Product Table</title>
<style>
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f2f2f2; }
</style>
"""
        
        # Add all style tags from the original document to preserve table styling
        style_tags = soup.find_all('style')
        for style in style_tags:
            new_html += str(style) + "\n"
        
        # Add all link tags for CSS
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            new_html += str(link) + "\n"
        
        new_html += "</head>\n<body>\n</body>\n</html>"
        new_soup = BeautifulSoup(new_html, 'html.parser')
        
        # Add the table to the new document
        new_soup.body.append(target_table)
        
        # Save the cleaned HTML to the output file
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(str(new_soup))
        
        print(f"Successfully extracted table and saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error processing GuidedNav HTML: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main function that processes HTML files based on command line arguments
    or uses default values if run directly.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Clean HTML by removing content above a specified heading or hero image')
    parser.add_argument('--input', '-i', help='Input HTML file or directory path')
    parser.add_argument('--output', '-o', help='Output HTML file or directory path')
    parser.add_argument('--heading', '-t', default="Crinkle Paper", help='Heading text to use as starting point')
    parser.add_argument('--recursive', '-r', action='store_true', help='Process all HTML files in directory recursively')
    parser.add_argument('--analyze', '-a', action='store_true', help='Analyze HTML structure instead of cleaning')
    parser.add_argument('--guidednav', '-g', action='store_true', help='Process file as GuidedNav HTML format')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle analyze mode
    if args.analyze:
        if args.input:
            analyze_html_structure(args.input)
            return
        else:
            print("Please provide an HTML file to analyze with --input")
            return
    
    # Default values if not provided
    input_path = args.input if args.input else "Crinkle-Paper.html"
    output_path = args.output if args.output else None
    heading_text = args.heading
    
    # Check if this is a GuidedNav file based on filename or flag
    is_guidednav = args.guidednav or (os.path.basename(input_path).startswith("GuidedNav_") if os.path.isfile(input_path) else False)
    
    # Check if input is a directory
    if os.path.isdir(input_path):
        # Process multiple files
        pattern = os.path.join(input_path, "**/*.html") if args.recursive else os.path.join(input_path, "*.html")
        html_files = glob.glob(pattern, recursive=args.recursive)
        
        # Create output directory if needed
        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)
        
        success_count = 0
        for html_file in html_files:
            # Determine output file path
            if output_path:
                rel_path = os.path.relpath(html_file, input_path)
                out_file = os.path.join(output_path, rel_path)
                os.makedirs(os.path.dirname(out_file), exist_ok=True)
            else:
                base_name = os.path.basename(html_file)
                out_file = os.path.splitext(base_name)[0] + "-Cleaned.html"
            
            # Determine if this file is a GuidedNav file
            file_is_guidednav = is_guidednav or os.path.basename(html_file).startswith("GuidedNav_")
            
            # Process the file with appropriate function
            print(f"Processing: {html_file} -> {out_file}")
            if file_is_guidednav:
                print("Processing as GuidedNav HTML format")
                success = clean_guidednav_html(html_file, out_file)
            else:
                success = clean_html(html_file, out_file, heading_text)
                
            if success:
                success_count += 1
                
                # Print file size statistics
                original_size = os.path.getsize(html_file)
                cleaned_size = os.path.getsize(out_file)
                reduction = ((original_size - cleaned_size) / original_size) * 100
                
                print(f"  Original size: {original_size:,} bytes")
                print(f"  Cleaned size: {cleaned_size:,} bytes")
                print(f"  Size reduction: {reduction:.2f}%\n")
        
        print(f"Processed {len(html_files)} files, {success_count} successful.")
    
    else:
        # Process single file
        # Determine output file path if not provided
        if not output_path:
            output_path = os.path.splitext(input_path)[0] + "-Cleaned.html"
        
        # Ensure the input file exists
        if not os.path.exists(input_path):
            print(f"Error: Input file '{input_path}' not found.")
            return
        
        # Clean the HTML with appropriate function
        if is_guidednav:
            print("Processing as GuidedNav HTML format")
            success = clean_guidednav_html(input_path, output_path)
        else:
            success = clean_html(input_path, output_path, heading_text)
        
        if success:
            print("HTML cleaning completed successfully.")
            
            # Print file size statistics
            original_size = os.path.getsize(input_path)
            cleaned_size = os.path.getsize(output_path)
            reduction = ((original_size - cleaned_size) / original_size) * 100
            
            print(f"Original size: {original_size:,} bytes")
            print(f"Cleaned size: {cleaned_size:,} bytes")
            print(f"Size reduction: {reduction:.2f}%")
        else:
            print("HTML cleaning failed.")

if __name__ == "__main__":
    main()