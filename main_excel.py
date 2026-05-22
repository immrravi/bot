import asyncio
import sys
import os
import pandas as pd
from scraper import InstagramScraper
from utils import is_valid_reel_url
from excel import export_to_excel

async def main():
    print("\n--- Instagram Reel Scraper (Excel Input) ---")
    
    # Check for cookies.json
    if not os.path.exists('cookies.json'):
        print("Error: 'cookies.json' not found. Please create it with your Instagram session cookies.")
        return

    # Prompt user for Excel file path
    excel_path = input("Enter the path to the Excel file (.xlsx): ").strip()
    
    if not os.path.exists(excel_path):
        print(f"Error: File '{excel_path}' not found.")
        return

    try:
        # Read Excel file
        all_grouped_links = read_grouped_links_from_excel(excel_path)
        if not all_grouped_links:
            print("Error: No valid groups of links found in the Excel file.")
            return

        all_results = []
        scraper = InstagramScraper(cookies_path='cookies.json')
        
        try:
            await scraper.init_browser(headless=True)

            for i, links_group in enumerate(all_grouped_links):
                print(f"\n--- Processing Group {i+1}/{len(all_grouped_links)} ---")
                if not links_group:
                    print("Skipping empty group.")
                    continue

                first_link = links_group[0]
                last_link = links_group[-1]
                
                print(f"First link (oldest) for group {i+1}: {first_link}")
                print(f"Last link (latest) for group {i+1}: {last_link}")

                if not is_valid_reel_url(first_link) or not is_valid_reel_url(last_link):
                    print(f"Error: One or more links in group {i+1} are invalid Instagram Reel URLs. Skipping this group.")
                    continue

                try:
                    print(f"Extracting profile info from the first link of group {i+1}...")
                    username, _ = await scraper.get_reel_info(first_link)
                    print(f"Username for group {i+1}: {username}")
                    
                    print(f"Collecting reels from @{username} between the specified links for group {i+1}...")
                    reels_data = await scraper.scrape_profile_reels(username, first_link, last_link)
                    
                    if reels_data:
                        all_results.extend(reels_data)
                        print(f"Collected {len(reels_data)} reels for group {i+1}.")
                    else:
                        print(f"No reels found for group {i+1} between {first_link} and {last_link}.")

                except Exception as e:
                    print(f"\nAn error occurred during scraping for group {i+1}: {e}")

            # 3. Export all collected data to Excel
            output_filename = 'reels_output_from_excel.xlsx'
            print(f"\nProcessing a total of {len(all_results)} reels from all groups...")
            success = export_to_excel(all_results, output_filename)
            
            if success:
                print(f"\nDone! Results saved to '{output_filename}'.")
                print(f"Total reels collected: {len(all_results)}")
            else:
                print("\nFailed to export results.")
                
        except Exception as e:
            print(f"\nAn error occurred during the overall scraping process: {e}")
        finally:
            await scraper.close()

    except Exception as e:
        print(f"\nAn error occurred reading the Excel file: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(0)
