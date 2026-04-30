# Local Instagram Reel Scraper (Updated)

This is a complete, local Instagram reel scraping tool that runs on macOS without any server or hosting. It uses Python and Playwright to scrape reel data from a user's profile based on a given reel URL.

## New Features
- **Fetch All Reels**: No longer limited to 12 reels. It scrolls until the target reel is found.
- **Chronological Order**: Exports reels from **old to new** (oldest first).
- **Target Filtering**: Automatically filters out reels older than the specified link.

## Project Structure

```
instagram_scraper/
├── main.py           # Main entry point of the script
├── scraper.py        # All Playwright scraping logic
├── utils.py          # Helper functions (e.g., view conversion)
├── excel.py          # Excel export functionality
├── requirements.txt  # Python package dependencies
├── telegram_bot.py   # Telegram bot integration
├── cookies.json      # Your Instagram session cookies (you must create this)
├── Dockerfile        # Docker configuration for deployment
├── HOSTING_GUIDE.md  # Guide for 24/7 free hosting
└── reels_output.xlsx # The output file with scraped data
```

## Setup Instructions for macOS

Follow these steps carefully to set up and run the scraper.

### Step 1: Prerequisites

Ensure you have **Python 3** installed on your macOS. You can check by opening `Terminal` and running:

```sh
python3 --version
```

If you don't have it, you can install it from [python.org](https://www.python.org/downloads/).

For macOS users, especially those with M1/M2/M3/M4 chips, it's crucial to have the **Xcode Command Line Tools** installed, as they provide compilers and other tools necessary for some Python packages to build correctly. Install them by running:

```sh
xcode-select --install
```

### Step 2: Download the Project

Download the project files and place them in a folder on your computer.

### Step 3: Install Python Packages

1.  Open the `Terminal` application.
2.  Navigate to the project directory where you saved the files.

    ```sh
    cd path/to/your/instagram_scraper
    ```

3.  Install the required Python packages using `pip`:

    ```sh
    pip3 install -r requirements.txt
    ```

### Step 4: Install Playwright Browsers

After installing the packages, you need to download the necessary browser binaries for Playwright. Run this command in the terminal:

```sh
playwright install
```

This will download a headless Chromium browser that Playwright will use for scraping.

### Step 5: Export Your Instagram Cookies (Mandatory)

This is the most critical step. The scraper needs your Instagram session cookies to access profiles as if you were logged in. Without valid cookies, it will fail.

1.  **Install a Cookie Exporter Extension**:
    -   Use a browser extension that can export cookies in the standard `cookies.json` format.
    -   A recommended extension for Chrome is **[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/jjfboifjdnnhgonljdgfigpgojdlcdol)**.

2.  **Export the Cookies**:
    -   Log in to your Instagram account at [www.instagram.com](https://www.instagram.com).
    -   Click the cookie exporter extension icon in your browser's toolbar.
    -   Find the option to **Export** or **Export as JSON**.
    -   Make sure the domain is `www.instagram.com`.
    -   Save the exported file and name it **`cookies.json`**.

3.  **Place the `cookies.json` File**:
    -   Move the `cookies.json` file you just downloaded into the `instagram_scraper` project directory, alongside `main.py`.

**Important**: Your `cookies.json` file contains sensitive session information. **Do not share it with anyone.**

## How to Run the Scraper

Once you have completed the setup, you can run the scraper.

1.  Open `Terminal` and navigate to the project directory.
2.  Run the `main.py` script:

    ```sh
    python3 main.py
    ```

3.  The script will prompt you to enter an Instagram reel URL. Paste the URL and press `Enter`.

    ```
    Enter the target Reel URL: https://www.instagram.com/reel/C1a2b3d4e5f/
    ```

4.  The script will then show progress logs as it works:

    ```
    Extracting reel info...
    Collecting all reels...
    Processing reels...
    Exporting Excel...
    ```

## How to Run the Telegram Bot

If you prefer to use the scraper via Telegram:

1.  **Get a Telegram Bot Token**:
    -   Message [@BotFather](https://t.me/botfather) on Telegram.
    -   Create a new bot and copy the API Token.

2.  **Set the Environment Variable**:
    -   In your terminal, set your bot token:
    ```sh
    export TELEGRAM_BOT_TOKEN="your_bot_token_here"
    ```

3.  **Run the Bot**:
    ```sh
    python3 telegram_bot.py
    ```

4.  **Use the Bot**:
    -   Open your bot in Telegram and send `/start`.
    -   Send any Instagram Reel URL to the bot.
    -   The bot will process the request and send you the Excel file directly.

## Output

## Hosting 24/7 for Free

For a complete guide on how to host this Telegram bot 24/7 for free, refer to the `HOSTING_GUIDE.md` file in this project.

The scraped data will be saved in a file named `reels_output.xlsx` in the same directory.

The Excel file will have the following columns, sorted by **oldest reels first** (chronological order):

| Reel URL          | Views    | Upload Date         |
| ----------------- | -------- | ------------------- |
| `https://...`     | `45000`  | `2024-03-19 15:00:00` |
| `https://...`     | `1200000`| `2024-03-20 10:30:00` |

## Disclaimer

This tool is for educational purposes only. Web scraping can be against the terms of service of many websites, including Instagram. Use this script responsibly and at your own risk. The developers are not responsible for any consequences of its use.
