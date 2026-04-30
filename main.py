import asyncio
import sys
import os
from scraper import InstagramScraper
from utils import is_valid_reel_url
from excel import export_to_excel

async def main():
    print("\n--- Instagram Reel Scraper (Updated) ---")
    
    # Check for cookies.json
    if not os.path.exists('cookies.json'):
        print("Error: 'cookies.json' not found. Please create it with your Instagram session cookies.")
        print("Refer to the README for instructions on how to export cookies.")
        return

    # Prompt user for Reel URL
    target_reel_url = input("Enter the target Reel URL (to scrape all reels uploaded after this one): ").strip()
    
    if not is_valid_reel_url(target_reel_url):
        print("Error: Invalid Instagram Reel URL.")
        return

    scraper = InstagramScraper(cookies_path='cookies.json')
    
    try:
        # Initialize browser
        await scraper.init_browser(headless=True)
        
        # 1. Extract reel info (username and date)
        print("Extracting reel info...")
        username, target_date = await scraper.get_reel_info(target_reel_url)
        print(f"Username: {username}")
        print(f"Target Reel Upload Date: {target_date}")
        
        # 2. Visit profile and scrape reels
        print(f"Collecting all reels from @{username} uploaded after the target reel...")
        reels_data = await scraper.scrape_profile_reels(username, target_reel_url)
        
        # 3. Export to Excel
        print(f"Processing {len(reels_data)} reels...")
        success = export_to_excel(reels_data, 'reels_output.xlsx')
        
        if success:
            print("\nDone! Results saved to 'reels_output.xlsx'.")
            print(f"Total reels collected: {len(reels_data)}")
            print("Order: Oldest to Newest (chronological)")
        else:
            print("\nNo reels found after the target date or failed to export.")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        await scraper.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(0)
