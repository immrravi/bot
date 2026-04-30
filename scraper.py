import asyncio
import json
import random
import os
import re
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from utils import parse_views, clean_username

class InstagramScraper:
    def __init__(self, cookies_path='cookies.json'):
        self.cookies_path = cookies_path
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def init_browser(self, headless=True):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        # Load cookies if they exist
        if os.path.exists(self.cookies_path):
            try:
                with open(self.cookies_path, 'r') as f:
                    cookies = json.load(f)
                
                # Clean cookies for Playwright compatibility
                valid_samesite = ["Strict", "Lax", "None"]
                cleaned_cookies = []
                for cookie in cookies:
                    # Playwright requires name, value, domain, path
                    if not all(k in cookie for k in ["name", "value", "domain", "path"]):
                        continue
                        
                    if "sameSite" in cookie:
                        if cookie["sameSite"] is None:
                            cookie["sameSite"] = "Lax"
                        else:
                            ss = str(cookie["sameSite"]).capitalize()
                            if ss not in valid_samesite:
                                cookie["sameSite"] = "Lax"
                            else:
                                cookie["sameSite"] = ss
                    
                    # Remove incompatible fields
                    for field in ["id", "storeId", "firstPartyDomain"]:
                        if field in cookie:
                            del cookie[field]
                    
                    cleaned_cookies.append(cookie)

                self.context = await self.browser.new_context()
                if cleaned_cookies:
                    await self.context.add_cookies(cleaned_cookies)
                else:
                    print("Warning: No valid cookies found in cookies.json after cleaning.")
            except Exception as e:
                print(f"Error loading cookies: {e}")
                self.context = await self.browser.new_context()
        else:
            self.context = await self.browser.new_context()
        
        self.page = await self.context.new_page()
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def human_delay(self, min_s=1, max_s=2):
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def get_reel_info(self, reel_url):
        """
        Extract username and upload timestamp from a specific reel using a fail-safe approach.
        """
        print(f"Extracting reel info from {reel_url}...")
        
        try:
            await self.page.goto(reel_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Initial page load timed out or failed: {e}. Attempting to proceed anyway...")

        current_url = self.page.url
        if "login" in current_url or "accounts/login" in current_url:
            raise Exception("Instagram redirected to login. Your cookies in cookies.json are likely expired or invalid.")
        
        extraction_script = """
        () => {
            let data = { username: null, timestamp: null };
            try {
                let ogDesc = document.querySelector('meta[property="og:description"]')?.content;
                if (ogDesc) {
                    let match2 = ogDesc.match(/-\s+([a-zA-Z0-9._]+)\s+on\s+/);
                    if (match2) data.username = match2[1];
                    if (!data.username) {
                        let match1 = ogDesc.match(/^([a-zA-Z0-9._]+)\s+on\s+/);
                        if (match1) data.username = match1[1];
                    }
                }
                if (!data.username) {
                    let ogTitle = document.querySelector('meta[property="og:title"]')?.content;
                    if (ogTitle && ogTitle.includes(' on Instagram')) {
                        data.username = ogTitle.split(' on Instagram')[0].trim();
                    }
                }
                let timeElem = document.querySelector('time');
                if (timeElem) {
                    data.timestamp = timeElem.getAttribute('datetime') || timeElem.getAttribute('title');
                }
            } catch (e) {}
            return data;
        }
        """
        
        try:
            result = await self.page.evaluate(extraction_script)
            username = result.get('username')
            timestamp_str = result.get('timestamp')

            if not username:
                match = re.search(r'instagram\.com/([^/]+)/reels?/', current_url)
                if match: username = match.group(1)

            if not username:
                raise Exception("Could not find username.")

            upload_date = None
            if timestamp_str:
                try:
                    upload_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except: pass
            
            if not upload_date:
                upload_date = datetime.now(timezone.utc)

            if upload_date.tzinfo is None:
                upload_date = upload_date.replace(tzinfo=timezone.utc)

            return clean_username(username), upload_date

        except Exception as e:
            raise Exception(f"Failed to extract reel info: {str(e)}")

    async def get_reel_date(self, reel_url, semaphore):
        """Fetch date for a single reel using a shared semaphore to limit concurrency."""
        async with semaphore:
            new_page = await self.context.new_page()
            try:
                # Use fast loading for date fetching
                await new_page.goto(reel_url, wait_until="domcontentloaded", timeout=20000)
                # Small delay for JS to render the time element
                await asyncio.sleep(1)
                
                time_elem = await new_page.query_selector('time')
                if time_elem:
                    ts = await time_elem.get_attribute('datetime')
                    reel_date = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                else:
                    reel_date = datetime.now(timezone.utc)
                
                if reel_date.tzinfo is None:
                    reel_date = reel_date.replace(tzinfo=timezone.utc)
                
                return reel_date
            except Exception as e:
                print(f"Error getting date for {reel_url}: {e}")
                return datetime.now(timezone.utc)
            finally:
                await new_page.close()

    async def scrape_profile_reels(self, username, target_reel_url):
        """
        Visit profile reels section and scrape all reels uploaded after target_reel_url.
        Optimized for speed and ensures chronological sorting by using discovery order.
        """
        target_reel_id_match = re.search(r'/reels?/([^/]+)', target_reel_url)
        target_reel_id = target_reel_id_match.group(1) if target_reel_id_match else ""
        
        profile_reels_url = f"https://www.instagram.com/{username}/reels/"
        print(f"Visiting profile: {profile_reels_url}")
        await self.page.goto(profile_reels_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        all_collected_reels = []
        seen_urls = set()
        
        max_scroll_attempts = 200 
        scroll_attempt = 0
        found_target = False
        consecutive_no_new = 0
        
        print("Scrolling profile and collecting reels until target is reached...")
        
        # Optimization: Use JS to extract all reels at once from the DOM
        extraction_js = """
        () => {
            let results = [];
            let items = document.querySelectorAll('a[href*="/reel/"]');
            items.forEach(item => {
                let href = item.getAttribute('href');
                let ariaLabel = item.getAttribute('aria-label') || "";
                let innerText = item.innerText || "";
                results.push({ href, ariaLabel, innerText });
            });
            return results;
        }
        """

        while scroll_attempt < max_scroll_attempts:
            items_data = await self.page.evaluate(extraction_js)
            new_reels_this_scroll = 0
            
            for data in items_data:
                href = data['href']
                if not href: continue
                
                clean_href = href.split('?')[0]
                reel_url = f"https://www.instagram.com{clean_href}"
                
                if reel_url not in seen_urls:
                    seen_urls.add(reel_url)
                    
                    reel_id_match = re.search(r'/reel/([^/]+)', reel_url)
                    reel_id = reel_id_match.group(1) if reel_id_match else ""
                    
                    if reel_id == target_reel_id:
                        print(f"Target reel found! (ID: {reel_id})")
                        found_target = True
                        break
                    
                    # Extract views from data
                    views = 0
                    view_match = re.search(r'([\d.MK,]+)\s*(?:views|plays|view|play)', data['ariaLabel'], re.IGNORECASE)
                    if view_match:
                        views = parse_views(view_match.group(1))
                    
                    if views == 0:
                        parts = re.split(r'[\n\s]+', data['innerText'].strip())
                        for part in parts:
                            if re.search(r'^[\d.MK,]+$', part):
                                parsed = parse_views(part)
                                if parsed > 0:
                                    views = parsed
                                    break
                    
                    all_collected_reels.append({
                        'Reel URL': reel_url,
                        'Views': views,
                        'Discovery Order': len(all_collected_reels) # Save discovery order (0 = newest)
                    })
                    new_reels_this_scroll += 1
            
            if found_target:
                break
                
            # Faster scrolling
            await self.page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(0.8)
            
            if new_reels_this_scroll == 0:
                consecutive_no_new += 1
                if consecutive_no_new > 5:
                    await self.page.keyboard.press('End')
                    await asyncio.sleep(2)
                if consecutive_no_new > 15:
                    print("Profile reached the end or stuck. Stopping scroll.")
                    break
            else:
                consecutive_no_new = 0
                
            scroll_attempt += 1

        if not found_target:
            print(f"Warning: Target reel was not found in the profile after {scroll_attempt} scrolls.")

        # Optimization: Parallel date fetching with a limit to avoid blocks
        print(f"Fetching exact dates for {len(all_collected_reels)} reels in parallel...")
        semaphore = asyncio.Semaphore(5) # Process 5 reels at a time
        
        # Collect dates in the SAME ORDER as all_collected_reels (which is new-to-old from profile)
        tasks = []
        for data in all_collected_reels:
            tasks.append(self.get_reel_date(data['Reel URL'], semaphore))
        
        dates = await asyncio.gather(*tasks)
        
        reels_data = []
        for i, data in enumerate(all_collected_reels):
            reels_data.append({
                'Reel URL': data['Reel URL'],
                'Views': data['Views'],
                'Upload Date': dates[i],
                'Discovery Order': data['Discovery Order'] # Pass discovery order to excel.py
            })
                
        return reels_data