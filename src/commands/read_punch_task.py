from src.base import BaseBrowser
import asyncio
import os
from datetime import datetime
import re

async def run(args):
    # Use credentials from args if provided, otherwise use defaults
    username = args[0] if args and len(args) > 0 else "kyluong"
    password = args[1] if args and len(args) > 1 else "19901991"
    
    url = "https://blueprint.cyberlogitec.com.vn/UI_TAT_028"
    
    browser = BaseBrowser(headless=True)
    try:
        page = await browser.start()
        print(f"Checking punch status at {url}...")
        await page.goto(url)
        
        # Check if login is required
        if "login" in page.url or await page.query_selector("#username"):
            await page.fill("#username", username)
            await page.fill("#password", password)
            await page.click("#submit-btn")
            await page.wait_for_load_state("networkidle")

        # Re-navigate to target URL if needed
        if page.url != url:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

        # Find today's date in the table
        today_str = datetime.now().strftime("%b %d, %Y")

        # Wait for either the table or a login element
        try:
            # Wait for today's date to appear in the text
            await page.wait_for_function(f"() => document.body.innerText.includes('{today_str}')", timeout=30000)
            # Give it a tiny bit more time for Webix to finish rendering the cells
            await asyncio.sleep(2)
        except Exception as e:
            # Fallback: check if we are on the login page
            if await page.query_selector("#username"):
                print("Stuck on login page. Attempting login...")
                await page.fill("#username", username)
                await page.fill("#password", password)
                await page.click("#submit-btn")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_function(f"() => document.body.innerText.includes('{today_str}')", timeout=30000)
            else:
                # Take a screenshot to see why it failed
                fail_path = os.path.join(os.getcwd(), "read_punch_fail.png")
                await page.screenshot(path=fail_path)
                print(f"Timed out waiting for date '{today_str}'. Screenshot saved to {fail_path}")
                return

        # print(f"Looking for data for: {today_str}")


        # Extract punch times from today's row
        # Strategy: find the cell with today's date, then find the row, then find cells with HH:mm
        result = await page.evaluate(f'''(todayStr) => {{
            const dateCell = Array.from(document.querySelectorAll('.webix_cell')).find(el => el.innerText.trim() === todayStr);
            if (!dateCell) return {{ error: "Could not find row for " + todayStr }};
            
            const rowTop = dateCell.getBoundingClientRect().top;
            const cellsInRow = Array.from(document.querySelectorAll('.webix_cell')).filter(el => {{
                const rect = el.getBoundingClientRect();
                return Math.abs(rect.top - rowTop) < 5; // Same horizontal line
            }});
            
            const times = cellsInRow
                .map(el => el.innerText.trim())
                .filter(text => /^\\d{{2}}:\\d{{2}}$/.test(text));
                
            return {{
                punchIn: times[0] || "Not found",
                punchOut: times[1] || "Not found",
                allTimes: times
            }};
        }}''', today_str)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"--- Punch Status for {today_str} ---")
            print(f"Punch In : {result['punchIn']}")
            print(f"Punch Out: {result['punchOut']}")
            
            # Save a success screenshot for the record
            # success_path = os.path.join(os.getcwd(), "punch_status_success.png")
            # await page.screenshot(path=success_path)



    finally:
        await browser.stop()

if __name__ == "__main__":
    # For testing directly
    import sys
    asyncio.run(run(sys.argv[1:]))
