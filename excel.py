import pandas as pd
import os
from datetime import timezone

def export_to_excel(data, filename='reels_output.xlsx'):
    """
    Export list of dictionaries to an Excel file, ensuring strict serial order.
    Uses Discovery Order from the scraper, which is the most reliable way to maintain 
    the exact sequence from the Instagram profile (newest to oldest).
    """
    if not data:
        print("No data to export.")
        return False
    
    try:
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Ensure all datetimes are timezone-aware (UTC)
        def normalize_date(d):
            if pd.isna(d): return d
            if hasattr(d, 'tzinfo') and d.tzinfo is not None:
                return d.astimezone(timezone.utc)
            return d.replace(tzinfo=timezone.utc)

        df['Upload Date'] = df['Upload Date'].apply(normalize_date)

        # DEEP FIX: SORTING LOGIC
        # Instagram profiles are naturally ordered from NEWEST to OLDEST.
        # The scraper collects them in this exact order and assigns a 'Discovery Order'.
        # Discovery Order 0 = Newest, Discovery Order N = Oldest.
        # To get the sheet in "Serial Order" (Oldest to Newest), we sort by Discovery Order DESCENDING.
        
        if 'Discovery Order' in df.columns:
            print("Sorting by Discovery Order (descending) to ensure strict serial sequence...")
            df = df.sort_values(by='Discovery Order', ascending=False)
        else:
            print("Discovery Order not found, falling back to Upload Date sorting...")
            df = df.sort_values(by='Upload Date', ascending=True)
        
        # Convert datetime to string for Excel compatibility (removing timezone for cleaner output)
        df['Upload Date String'] = df['Upload Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Prepare final columns for export
        # We don't include 'Discovery Order' in the final Excel to keep it clean
        final_df = df[['Reel URL', 'Views', 'Upload Date String']].copy()
        final_df.rename(columns={'Upload Date String': 'Upload Date'}, inplace=True)
        
        # Export to Excel using openpyxl engine
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False)
        
        print(f"Successfully exported {len(final_df)} reels to {filename} in strict serial order.")
        return True
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        return False

def read_grouped_links_from_excel(filepath):
    """
    Reads an Excel file, parses links into groups separated by two blank rows.
    Automatically finds the 'link' column and skips headers.
    Returns a list of lists, where each inner list is a group of links.
    """
    try:
        # Read the entire sheet without headers first to find the 'link' column
        df_raw = pd.read_excel(filepath, header=None)
        
        # Find the column index that contains 'link' (case-insensitive)
        link_col_idx = -1
        start_row = 0
        
        for r in range(min(5, len(df_raw))): # Check first 5 rows for header
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c]).strip().lower()
                if val == 'link':
                    link_col_idx = c
                    start_row = r + 1 # Data starts after the header row
                    break
            if link_col_idx != -1:
                break
        
        # If 'link' header not found, default to first column and start from row 0
        if link_col_idx == -1:
            print("Warning: 'link' column header not found. Defaulting to the first column.")
            link_col_idx = 0
            start_row = 0

        grouped_links = []
        current_group = []
        blank_row_count = 0

        # Iterate through the rows starting from the data row
        for index in range(start_row, len(df_raw)):
            cell_value = df_raw.iloc[index, link_col_idx]
            
            if pd.isna(cell_value) or str(cell_value).strip() == '':
                blank_row_count += 1
                if blank_row_count >= 2 and current_group:
                    grouped_links.append(current_group)
                    current_group = []
                    blank_row_count = 0
                continue
            else:
                blank_row_count = 0
                link = str(cell_value).strip()
                # Basic validation to skip headers if they were accidentally included
                if link.lower() != 'link' and 'instagram.com' in link:
                    current_group.append(link)
        
        if current_group:
            grouped_links.append(current_group)

        return grouped_links
    except Exception as e:
        print(f"Error reading grouped links: {e}")
        return []
