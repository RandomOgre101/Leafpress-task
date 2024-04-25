from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Storing the user data in a .env file so as not to hardcode it into the script
LOGIN_USERNAME = os.environ.get("LOGIN_USERNAME")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")


try:
    with sync_playwright() as p:
        # I am using chromium for this project
        browser = p.chromium.launch(headless=False)

        # Initializing context as on logging in, the website opens a new tab, so I have to keep that tab in context
        context = browser.new_context()

        page = context.new_page()
        page.set_default_timeout(
            600000
        )  # Large timeout as I am using a VPN and the speeds are slow

        # Going to the website
        page.goto("https://www.aepenergy.com/")

        # Click the 'My Account' button to access login popup
        page.get_by_role("button", name="My Account").click()

        # Enter the credentials
        page.get_by_role("textbox", name="username").fill(LOGIN_USERNAME)
        page.get_by_role("textbox", name="password").fill(LOGIN_PASSWORD)

        # Saving the login button in a variable
        login_button = page.get_by_role("button", name="Login")

        # Clicking the Login button and telling Playwright that a new tab will be opened so change the context to that
        with context.expect_page() as user_page_tab:
            login_button.click()
        user_page = user_page_tab.value

        user_page.wait_for_load_state(
            timeout=6000000
        )  # Again, large timeout as I am using a VPN and the speeds are slow

        # Pressing the 'View All Statements' hyperlink
        user_page.get_by_role("link", name="View All Statements").click()

        # Clicking the 'View All' hyperlink so all the data in table appears in one page
        user_page.get_by_role("link", name="View All").nth(1).click()
        user_page.wait_for_timeout(5000)

        # Selecting the table of data
        table = user_page.wait_for_selector('//table[@id="row"]', timeout=6000000)

        # Making a list of the rows in the table
        rows = table.query_selector_all("tbody tr")

        # Iterating through the rows
        for row in rows:

            # Storing each cell of the row in a list
            cells = row.query_selector_all("td")

            # Getting the dates of today and 12 months ago so we can have a range
            now = datetime.now().strftime("%m/%d/%y")
            today_date = datetime.strptime(now, "%m/%d/%y")

            year_ago = (datetime.now() - timedelta(days=365)).strftime("%m/%d/%y")
            ago_date = datetime.strptime(year_ago, "%m/%d/%y")

            # Extracting the dates from the table and formatting them into a datetime object for easy comparison
            date1 = datetime.strptime(
                str(cells[0].inner_text()).split(" - ")[0], "%m/%d/%y"
            )
            date2 = datetime.strptime(
                str(cells[0].inner_text()).split(" - ")[-1], "%m/%d/%y"
            )

            # Checking if those dates are from 12 months ago till today
            if today_date >= date2 >= ago_date and today_date >= date1 >= ago_date:

                # If they are, then download the pdf
                link = row.query_selector_all("td")[1].query_selector("a")

                # Telling Playwright that we will be downloading a file
                with user_page.expect_download() as download_info:
                    link.click()
                    download = download_info.value

                # Making the folder if it doesnt exist
                directory = f"Billing History/{datetime.now().year}-{datetime.now().month}-{datetime.now().day}"
                os.makedirs(directory, exist_ok=True)

                # Finally saving it with a proper name and order
                download.save_as(
                    f"{directory}/{str(date1.date())}_to_{str(date2.date())}_Statement.pdf"
                )


# Error handling if anything goes wrong
except Exception as e:
    print(f"[ERROR]: {e}")

finally:
    # Making sure the browser is closed
    if "browser" in locals():
        browser.close()
