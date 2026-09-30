import os
import json
import time
import re
from datetime import datetime
import pandas as pd
from playwright.sync_api import sync_playwright

# Configuration Paths
EXCEL_FILE = "contacts.xlsx"
REPORT_JSON = "report.json"
REPORT_EXCEL = "report.xlsx"
SCREENSHOT_DIR = "screenshots"
SESSION_DIR = "./whatsapp_session_data" # Holds persistent session state / cookies

# Ensure screenshot folder exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_whatsapp_automation():
    # 1. Parse Excel Sheet Data Using Pandas
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: Target initialization file '{EXCEL_FILE}' not found.")
        return

    print("Parsing contact records ledger...")
    df = pd.read_excel(EXCEL_FILE)
    
    # Standardize column naming rules to avoid case mismatches
    df.columns = [col.strip().lower() for col in df.columns]
    
    if 'name' not in df.columns or 'phone' not in df.columns:
        print("Error: Excel spreadsheet must contain 'Name' and 'Phone' columns.")
        return
        
    contacts = []
    for _, row in df.iterrows():
        name = str(row['name']).strip()
        phone = str(row['phone']).strip()
        # Fallback template if column is missing or empty
        template = str(row['message']).strip() if 'message' in df.columns and pd.notna(row['message']) else "Hello {name}!"
        
        if name and phone and name != 'nan' and phone != 'nan':
            # Strip spaces, hyphens, and structural symbols out of the dial target
            phone = re.sub(r'[\s\-()]', '', phone)
            contacts.append({"name": name, "phone": phone, "template": template})

    print(f"Successfully staged {len(contacts)} records.")

    # 2. Launch Persistent Browser Context
    with sync_playwright() as p:
        print("Launching automated browser engine...")
        # launch_persistent_context acts like your personal Chrome profile, saving cookies
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,  # Must be visible to interactively scan QR code on the first run
            args=['--start-maximized'],
            no_viewport=True
        )
        
        page = context.pages[0]
        page.goto("https://web.whatsapp.com/")
        
        print("Awaiting user login authentication... (Scan the QR Code now if prompted)")
        
        try:
            # Wait for main application UI search/chat input structure to initialize
            #page.wait_for_selector('div[contenteditable="true"]', timeout=90000)
            page.wait_for_load_state("networkidle", timeout=90000)
            print("Session successfully authorized!")
        except Exception:
            print("Authentication lifecycle window timed out. Please try running the program again.")
            context.close()
            return

        execution_summary = []

        # 3. Process Target Batch
        for contact in contacts:
            print(f"\nProcessing target profile: {contact['name']} ({contact['phone']})")
            
            record = {
                "name": contact["name"],
                "phone": contact["phone"],
                "status": "Failed",
                "extracted_messages": [],
                "screenshot_path": "",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            try:
                # Bypass unstable DOM layout elements using WhatsApp's direct URL deep link protocol
                formatted_phone = contact["phone"].replace("+", "")
                wa_url = f"https://whatsapp.com/send/?phone={formatted_phone}&text&type=phone_number&app_absent=0"
                page.goto(wa_url)
                
                # Listen for the chat frame or the "Invalid Phone Number" dialog box modal
                page.wait_for_selector('footer div[contenteditable="true"], div[role="dialog"]', timeout=30000)
                page.wait_for_timeout(3000)  # Safe buffer for data rendering to stabilize
                
                # Check for error warning dialogues
                dialog = page.query_selector('div[role="dialog"]')
                if dialog:
                    dialog_text = dialog.inner_text().lower()
                    if "invalid" in dialog_text or "shared via url" in dialog_text:
                        raise Exception("Target destination number is invalid or not registered on WhatsApp.")
                
                # Merge target profile identity parameters into template string
                message_payload = contact["template"].replace("{name}", contact["name"])
                chat_input = 'footer div[contenteditable="true"]'
                
                page.focus(chat_input)
                # Ensure the field is empty before typing
                page.keyboard.press("Control+A")
                page.keyboard.press("Delete")
                page.type(chat_input, message_payload)
                page.wait_for_timeout(500)
                
                # Transmit Payload
                page.keyboard.press("Enter")
                
                # Assert checkmark visibility to guarantee message exited local queue out to cloud server
                delivery_checkmark = 'span[data-icon="msg-check"], span[data-icon="msg-dblcheck"]'
                page.wait_for_selector(delivery_checkmark, timeout=15000)
                page.wait_for_timeout(1000)  # Render safety window
                
                # Generate Verification Snapshot Output
                screenshot_filename = os.path.join(SCREENSHOT_DIR, f"{formatted_phone}_sent.png")
                page.screenshot(path=screenshot_filename)
                record["screenshot_path"] = screenshot_filename

                # --- SMART DATA EXTRACTION (BONUS PART) ---
                print("Scraping historical context message logs...")
                chat_bubble_element = 'div.message-in, div.message-out'
                
                page.wait_for_selector(chat_bubble_element, timeout=5000)
                message_nodes = page.query_selector_all(chat_bubble_element)
                
                # Grab the final 3 chronological message entities
                target_sample_nodes = message_nodes[-3:]
                
                for node in target_sample_nodes:
                    try:
                        text_span = node.query_selector('span.copyable-text')
                        if text_span:
                            message_text = text_span.inner_text().strip()
                            class_attr = node.get_attribute('class') or ""
                            origin_tag = "Contact" if "message-in" in class_attr else "You"
                            
                            record["extracted_messages"].append(f"[{origin_tag}]: {message_text}")
                    except Exception:
                        pass # Ignore layout nodes representing empty spaces or rich non-text components

                record["status"] = "Success"
                print(f"Tasks completed successfully for {contact['name']}.")

            except Exception as step_error:
                error_msg = str(step_error)
                print(f"Failed processing execution step tracking logic: {error_msg}")
                record["status"] = f"Failed: {error_msg}"
                
            execution_summary.append(record)
            time.sleep(4)  # Natural human interaction spacing delay

        # 4. Generate Reports File Pipelines
        print("\nWriting out final payload telemetry outputs...")
        
        # Save structured JSON array
        with open(REPORT_JSON, "w", encoding="utf-8") as json_out:
            json.dump(execution_summary, json_out, indent=4, ensure_ascii=False)
        print(f"JSON Ledger saved to: {REPORT_JSON}")
        
        # Flatten extraction arrays and convert summary output arrays to a DataFrame
        flattened_summary = []
        for item in execution_summary:
            flattened_item = item.copy()
            # Convert python string array into a single readable string cell
            flattened_item["extracted_messages"] = " | ".join(item["extracted_messages"])
            flattened_summary.append(flattened_item)
            
        report_df = pd.DataFrame(flattened_summary)
        
        # Rename output sheet headers cleanly
        report_df.columns = [col.replace("_", " ").title() for col in report_df.columns]
        
        # Save structured Excel logs using openpyxl engine framework
        report_df.to_excel(REPORT_EXCEL, index=False, sheet_name="Execution Metrics Summary")
        print(f"Excel Sheet generated at destination: {REPORT_EXCEL}")
        
        context.close()

if __name__ == "__main__":
    run_whatsapp_automation()
