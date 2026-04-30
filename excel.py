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