from bs4 import BeautifulSoup
import pandas as pd
import os
import openpyxl

# Define folder path
folder_path = "cleaned_html"
excel_file = "html_output.xlsx"

def expand_table_rows(table):
    """Expands rows considering rowspan and colspan attributes."""
    expanded_rows = []
    row_spans = {}
    
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        expanded_row = []
        col_index = 0
        
        while col_index < len(expanded_row) + len(cells):
            # Handle previous rowspan cells
            if col_index in row_spans:
                expanded_row.append(row_spans[col_index]["value"])
                row_spans[col_index]["count"] -= 1
                if row_spans[col_index]["count"] == 0:
                    del row_spans[col_index]
                col_index += 1
                continue
            
            # Process current cell
            cell = cells.pop(0)
            cell_text = cell.get_text(strip=True)
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))
            
            for _ in range(colspan):
                expanded_row.append(cell_text)
                if rowspan > 1:
                    row_spans[col_index] = {"value": cell_text, "count": rowspan - 1}
                col_index += 1
        
        expanded_rows.append(expanded_row)
    
    return expanded_rows

def is_data_row(row):
    """Checks if a row is a data row by looking for numeric values."""
    return any(cell.replace(',', '').replace('.', '').isdigit() for cell in row if cell)

def make_unique_headers(headers):
    """Ensures headers are unique by appending numbers to duplicates."""
    seen = {}
    unique_headers = []
    
    for col in headers:
        if col in seen:
            seen[col] += 1
            unique_headers.append(f"{col} ({seen[col]})")
        else:
            seen[col] = 1
            unique_headers.append(col)
    
    return unique_headers

def handle_guided_nav_table(table):
    """
    Custom function to handle guided nav tables where data rows start with
    class='GNColored-Row GNNoBorderTop' and anything above is considered headers.
    Handles rowspan and colspan attributes properly.
    Maintains multi-level header structure.
    
    Args:
        table: BeautifulSoup table element
    
    Returns:
        tuple: (headers, data_rows) where headers is a list of header rows
    """
    # First, find the first row with the specific class
    data_start_row = None
    all_rows = table.find_all("tr")
    
    for i, row in enumerate(all_rows):
        if row.get("class") and any(cls in ["GNColored-Row", "GNNoBorderTop"] for cls in row.get("class")):
            data_start_row = i
            break
    
    # If no guided nav row found, return None to fall back to standard processing
    if data_start_row is None:
        return None
    
    # Headers are all rows before the data start row
    header_rows = all_rows[:data_start_row]
    data_rows = all_rows[data_start_row:]
    
    # Expand headers considering rowspan and colspan
    expanded_headers = []
    row_spans = {}
    
    for row in header_rows:
        cells = row.find_all(["td", "th"])
        expanded_row = []
        col_index = 0
        
        while col_index < len(expanded_row) + len(cells):
            # Handle previous rowspan cells
            if col_index in row_spans:
                expanded_row.append(row_spans[col_index]["value"])
                row_spans[col_index]["count"] -= 1
                if row_spans[col_index]["count"] == 0:
                    del row_spans[col_index]
                col_index += 1
                continue
            
            # Process current cell
            cell = cells.pop(0)
            cell_text = cell.get_text(strip=True)
            colspan = int(cell.get("colspan", 1))
            rowspan = int(cell.get("rowspan", 1))
            
            for _ in range(colspan):
                expanded_row.append(cell_text)
                if rowspan > 1 and rowspan + len(expanded_headers) > len(header_rows):
                    # This rowspan extends into data section, ignore it
                    pass
                elif rowspan > 1:
                    row_spans[col_index] = {"value": cell_text, "count": rowspan - 1}
                col_index += 1
        
        expanded_headers.append(expanded_row)
    
    # Expand data rows
    expanded_data = expand_table_rows(table)
    # Only include rows starting from the data_start_row
    expanded_data = expanded_data[data_start_row:]
    
    # Check if the first column appears to be an index column
    has_index_column = True
    if expanded_data:
        # Check if first column looks like an index (contains sequential numbers)
        try:
            first_cols = [int(row[0]) for row in expanded_data if row[0].isdigit()]
            if len(first_cols) < len(expanded_data) * 0.7:  # If less than 70% are numbers
                has_index_column = False
        except (ValueError, IndexError):
            has_index_column = False
    
    # If the first column is an index, remove it
    if has_index_column:
        # Remove first column from each header row
        for row in expanded_headers:
            if len(row) > 1:  # Make sure there's at least one column to remove
                row.pop(0)
        
        # Remove first column from each data row
        for row in expanded_data:
            if len(row) > 1:
                row.pop(0)
    
    # Ensure all header rows have the same length
    max_len = max(len(row) for row in expanded_headers)
    for row in expanded_headers:
        while len(row) < max_len:
            row.append("")
    
    # Ensure data rows match header length
    clean_rows = []
    for row_data in expanded_data:
        while len(row_data) < max_len:
            row_data.append("")  # Fill missing columns with empty strings
        
        if len(row_data) > max_len:
            row_data = row_data[:max_len]  # Trim excess columns
        
        clean_rows.append(row_data)
    
    # Return headers and data rows without applying make_unique_headers
    return expanded_headers, clean_rows

# Get all HTML files from the folder
html_files = [f for f in os.listdir(folder_path) if f.endswith(".html")]

if not html_files:
    print("No HTML files found in the folder.")
else:
    with pd.ExcelWriter(excel_file, mode="w", engine="openpyxl") as writer:
        for html_file in html_files:
            file_path = os.path.join(folder_path, html_file)
            
            with open(file_path, "r", encoding="utf-8") as file:
                soup = BeautifulSoup(file, "html.parser")

            tables = soup.find_all("table")

            if not tables:
                print(f"No tables found in {html_file}, skipping.")
                continue

            all_data = []  # Store all table data
            master_headers = None  # Store unified column headers

            for idx, table in enumerate(tables):
                # Try to handle as guided nav table first
                guided_nav_result = handle_guided_nav_table(table)
                
                if guided_nav_result:
                    # If guided nav table was found and processed
                    header_rows, clean_rows = guided_nav_result
                    
                    # Create a multi-index from header rows
                    multi_index = pd.MultiIndex.from_arrays(header_rows)
                    
                    # Create DataFrame with multi-level headers
                    df = pd.DataFrame(clean_rows, columns=multi_index)
                else:
                    # Fall back to original processing
                    expanded_table = expand_table_rows(table)
                    
                    if len(expanded_table) < 3:
                        print(f"Skipping table {idx+1} in {html_file} due to missing headers")
                        continue
                    
                    # Skip first row, use 2nd row as main header
                    main_headers = expanded_table[1]

                    # Check if 3rd row is a data row
                    if is_data_row(expanded_table[2]):
                        final_headers = main_headers  # Use 2nd row as header
                        rows = expanded_table[2:]  # Data starts from 3rd row
                    else:
                        sub_headers = expanded_table[2]
                        final_headers = []
                        for h in main_headers:
                            if "price per case" in h.lower():
                                if len(sub_headers) == 1:
                                    final_headers.append(h)  # If no sub-columns, keep as is
                                else:
                                    final_headers.extend(sub_headers)  # Append sub-headers for price
                            else:
                                final_headers.append(h)
                        
                        rows = expanded_table[3:]  # Ensure we do not miss any data rows
                    
                    # Make column headers unique
                    final_headers = make_unique_headers(final_headers)

                    # Ensure all rows match header length
                    clean_rows = []
                    for row_data in rows:
                        while len(row_data) < len(final_headers):
                            row_data.append("")  # Fill missing columns with empty strings
                        
                        if len(row_data) > len(final_headers):
                            row_data = row_data[:len(final_headers)]  # Trim excess columns
                        
                        clean_rows.append(row_data)
                    
                    df = pd.DataFrame(clean_rows, columns=final_headers)

                if df.empty:
                    print(f"Skipping table {idx+1} in {html_file} as it has no valid rows")
                    continue
                
                # Append table data with spacing
                if all_data:
                    # Add empty row for spacing, respecting multi-index if present
                    if isinstance(df.columns, pd.MultiIndex):
                        empty_df = pd.DataFrame([[""] * len(df.columns)], columns=df.columns)
                    else:
                        empty_df = pd.DataFrame([[""] * len(df.columns)], columns=df.columns)
                    all_data.append(empty_df)
                all_data.append(df)

            if all_data:
                # Concatenate all dataframes
                # Note: This assumes all tables have the same header structure within a file
                # If they differ, you might need to handle them separately
                final_df = pd.concat(all_data, ignore_index=True)
                
                # Save each file's data in a separate sheet named after the HTML file
                sheet_name = os.path.splitext(html_file)[0][:31]  # Excel sheet name limit is 31 chars
                
                # For MultiIndex columns, we must include the DataFrame index
                # There's a pandas limitation that doesn't allow index=False with MultiIndex columns
                if isinstance(final_df.columns, pd.MultiIndex):
                    # Add a numeric index but hide it in Excel by not naming it
                    final_df.to_excel(writer, sheet_name=sheet_name, index=True, index_label=None)
                else:
                    final_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                print(f"Data from {html_file} successfully added to {sheet_name} sheet in {excel_file}")
    
    print("All data successfully saved to output.xlsx.")