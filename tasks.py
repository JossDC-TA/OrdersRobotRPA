from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
import time
import os

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_the_intranet_website()
    orders = get_orders()
    store_receipts_and_screenshots(orders)
    archive_receipts()

def open_the_intranet_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def close_annoying_modal():
    """Closes the annoying modal that pops up"""
    page = browser.page()
    page.click("text=OK")

def get_orders():
    """Downloads the orders CSV file and reads it as a table"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    tables = Tables()
    worksheet = tables.read_table_from_csv("orders.csv", header=True)
    return worksheet

import time

def fill_and_submit_order_form(order):
    """Fills in the order data and click the 'Submit' button"""
    time.sleep(1)
    close_annoying_modal()
    page = browser.page()
    page.select_option("#head", str(order["Head"]))

    body_value = str(order["Body"])
    radio_button_selector = f"input[type='radio'][value='{body_value}']"
    page.click(radio_button_selector)
    
    legs_input_selector = "input[placeholder='Enter the part number for the legs']"
    page.fill(legs_input_selector, str(order["Legs"]))
    
    page.fill("#address", str(order["Address"]))
    page.click("#preview")
    
    while True:
        page.click("#order")
        time.sleep(1)
        if not page.locator("div.alert.alert-danger[role='alert']").is_visible():
            break

def store_receipt_as_pdf(order_number):
    """Store the order receipt as a PDF file."""
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()
    base_url = "https://robotsparebinindustries.com"
    receipt_html = receipt_html.replace('src="/', f'src="{base_url}/')
    
    pdf_file_path = f"output/receipts/receipt_{order_number}.pdf"
    pdf = PDF()
    pdf.html_to_pdf(receipt_html, pdf_file_path)
    return pdf_file_path

def screenshot_robot(order_number):
    """Take a screenshot of the robot."""
    screenshot_path = f"output/robot_{order_number}.png"
    page = browser.page()
    page.locator("#robot-preview").screenshot(path=screenshot_path)
    return screenshot_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Embed the robot screenshot into the receipt PDF file."""
    pdf = PDF()
    pdf.add_files_to_pdf([screenshot], pdf_file, append=True)

def store_receipts_and_screenshots(orders):
    """Loop through the orders and store receipts and screenshots"""
    for order in orders:
        fill_and_submit_order_form(order)
        order_number = order["Order number"]
        screenshot = screenshot_robot(order_number)
        pdf_file = store_receipt_as_pdf(order_number)
        embed_screenshot_to_receipt(screenshot, pdf_file)
        go_to_order_another_robot()

def go_to_order_another_robot():
    """Click the 'Order another robot' button."""
    page = browser.page()
    page.click("#order-another")

def archive_receipts():
    """Archive all receipt PDFs and images into a single ZIP file."""
    archive = Archive()
    archive.archive_folder_with_zip("output/receipts", "output/receipts.zip")
