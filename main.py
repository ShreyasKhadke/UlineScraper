import subprocess
import os
import time
from datetime import datetime
from HtmlFetcher import extract_h1_texts, scrape_html_from_csv

def log_time(event):
    """Logs the event timestamp to a file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {event}\n"
    
    with open("timelog.txt", "a") as log_file:
        log_file.write(log_entry)
    
    print(log_entry.strip())  # Print log to console

def main():
    start_time = time.time()
    log_time("Script started")

    # Step 1: Extract H1 texts from HTML files
    log_time("Starting HTML scraping")
    scrape_html_from_csv("uline_scrap_products.csv")
    log_time("Finished HTML scraping")

    log_time("Starting H1 text extraction")
    extract_h1_texts()
    log_time("Finished H1 text extraction")

    # Step 2: Execute commands from the generated input.txt
    output_dir = "cleaned_html"
    os.makedirs(output_dir, exist_ok=True)
    log_time(f"Created/verified directory: {output_dir}")

    input_file_path = "input.txt"
    default_entry = "python H1Cleaner.py --input scraped_html/GuidedNav_184360.html --output cleaned_html/GuidedNav_184360-Cleaned.html\n"

    # Ensure input.txt exists and append the default entry correctly
    with open(input_file_path, "a+") as f:
        f.seek(0)
        lines = f.readlines()
        if default_entry.strip() not in [line.strip() for line in lines]:
            f.write("\n" + default_entry)

    # Read input.txt
    if not os.path.exists(input_file_path):
        log_time("Error: input.txt not found. Exiting script.")
        return

    with open(input_file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    log_time("Processing input.txt")

    # Process each line
    for line in lines:
        line = line.strip()
        if "--heading" in line:
            parts = line.split("--heading")
            if len(parts) == 2:
                input_file = parts[0].replace("python H1Cleaner.py --input ", "").strip()
                heading = parts[1].strip().strip('"')
                output_file = os.path.join(output_dir, os.path.basename(input_file))
                command = ["python", "H1Cleaner.py", "--input", input_file, "--output", output_file, "--heading", heading]
        else:
            # Handling default entry without heading
            command = line.split()

        # Run the H1Cleaner script with logging
        log_time(f"Running command: {' '.join(command)}")
        try:
            subprocess.run(command, check=True)
            log_time(f"Completed command: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            log_time(f"Error executing command: {' '.join(command)}: {e}")

    # Remove input.txt after processing
    os.remove(input_file_path)
    log_time("Deleted input.txt")

    # Run HtmlExtractor.py
    log_time("Running HtmlExtractor.py")
    subprocess.run(["python", "HtmlExtractor.py"])
    log_time("Completed HtmlExtractor.py")

    # Run cleaner.py
    log_time("Running cleaner.py")
    subprocess.run(["python", "cleaner.py"])
    log_time("Completed cleaner.py")

    # Log total execution time
    total_time = time.time() - start_time
    log_time(f"Script completed in {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
