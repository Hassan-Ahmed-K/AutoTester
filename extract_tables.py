import csv
import os
from bs4 import BeautifulSoup
import re

# Configuration
input_file = r"C:/Users/FATTANI COMPUTERS/AppData/Roaming/MetaQuotes/Terminal/D8E196A488CAFD45BB0BBB0BC09A258A/Agent Finder Results/AUDCAD__20251116_211550/sets/HTML Reports\\euraud_as_3_4891.htm"
output_dir = "extracted_data"
os.makedirs(output_dir, exist_ok=True)

def read_html_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-16") as f:
            return f.read()
    except UnicodeError:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
def clean_html_text(html):
    # remove tags
    text = re.sub(r"<.*?>", "", html)
    # normalize spacing
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_table_data(table):
    rows = table.find_all("tr")
    raw_html = "\n".join(str(r) for r in rows)

    clean_text = clean_html_text(raw_html)

    extract_inputs_and_metrics(clean_text)

    data = []
    for row in rows:
        cols = row.find_all(["td", "th"])
        cols = [ele.get_text(strip=True) for ele in cols]
        if cols:
            data.append(cols)

    return data
def extract_inputs_and_metrics(text):
    data = {}

    # Inputs
    input_patterns = {
        "AllowNewSequence": r"AllowNewSequence\s*=\s*(\w+)",
        "StrategyDescription": r"StrategyDescription\s*=\s*([^\s]+)",
        "ColorScheme": r"ColorScheme\s*=\s*(\d+)",
        "MAGIC_NUMBER": r"MAGIC_NUMBER\s*=\s*(\d+)",
        "TradeComment": r"TradeComment\s*=\s*([^\s]+)",
        "UseRandomEntryDelay": r"UseRandomEntryDelay\s*=\s*(\w+)",
        "MaxSpreadPips": r"MaxSpreadPips\s*=\s*([\d\.]+)",
        "apiKey": r"apiKey\s*=\s*([A-Za-z0-9]+)",
        "CustomTradingTimes": r"CustomTradingTimes\s*=\s*(\w+)",
        "MondayStartEnd": r"MondayStartEnd\s*=\s*([\d:]+-[\d:]+)",
        "LotSize": r"LotSize\s*=\s*([\d\.]+)",
        "MaxLots": r"MaxLots\s*=\s*([\d\.]+)",
        "MaxSequencesPerDay": r"MaxSequencesPerDay\s*=\s*(\d+)",

    }

    for key, pattern in input_patterns.items():
        m = re.search(pattern, text)
        if m:
            data[key] = m.group(1).strip()

    # Metrics
    metrics_patterns = {
        "Profit": r"Total Net Profit:\s*([-\d\s]+\.\d+)",
        "PF": r"Profit Factor:\s*([\d\.]+)",
        "RF": r"Recovery Factor:\s*([\d\.]+)",
        "Avg Win": r"Average profit trade:\s*([-\d\.]+)",
        "Avg Loss": r"Average loss trade:\s*([-\d\.]+)",
        "Trade Vol": r"Total Trades:\s*(\d+)",
        "Max DD": r"Balance Drawdown Maximal:\s*([\d\.]+)",
        "Max Drawdown": r"Equity Drawdown Maximal:\s*([\d\.]+)",
        "Max Hold": r"Maximal position holding time:\s*(\d{1,3}:\d{2}:\d{2})",
        "Avg Hold": r"Average position holding time:\s*(\d{1,3}:\d{2}:\d{2})",
    }

    for key, pattern in metrics_patterns.items():
        m = re.search(pattern, text)
        if m:
            data[key] = m.group(1).replace(" ", "")  # remove spaces in numbers
    print("Extracted Inputs and Metrics:"  , data)
    return data

def save_to_csv(filename, rows):
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Saved {filename}")

def process_table_2(table):
    rows = table.find_all("tr")
    
    orders_data = []
    deals_data = []
    
    current_section = None
    # State machine: None -> FOUND_ORDERS -> ORDERS_HEADER -> ORDERS_DATA -> FOUND_DEALS -> DEALS_HEADER -> DEALS_DATA

    capture_orders = False
    capture_deals = False
    
    # To handle the "next row is header" logic
    expecting_orders_header = False
    expecting_deals_header = False
    
    for row in rows:
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        
        # Check for empty rows that might be spacers
        if not any(cells):
            continue
            
        # Check for Section Headers
        # The snippet shows the "Orders" text is in a <th> with colspan, or just a cell with "Orders"
        # We'll check if "Orders" is the only substantial text or if it's explicitly "Orders"
        
        # Join cells to check content easily
        row_text = "".join(cells).lower()
        
        if "orders" == row_text or (len(cells) == 1 and "orders" in cells[0].lower()):
            print("Found Orders Section")
            capture_orders = True
            capture_deals = False
            expecting_orders_header = True
            continue
            
        if "deals" == row_text or (len(cells) == 1 and "deals" in cells[0].lower()):
            print("Found Deals Section")
            capture_orders = False
            capture_deals = True
            expecting_deals_header = True
            continue
            
        # Capture Data
        if capture_orders:
            if expecting_orders_header:
                orders_data.append(cells) # Add header
                expecting_orders_header = False
            else:
                orders_data.append(cells)
                
        elif capture_deals:
            if expecting_deals_header:
                deals_data.append(cells)
                expecting_deals_header = False
            else:
                deals_data.append(cells)

    return orders_data, deals_data

def main():
    content = read_html_file(input_file)
    if not content:
        return

    soup = BeautifulSoup(content, "html.parser")
    tables = soup.find_all("table")
    
    if len(tables) >= 1:
        print("Processing Table 1...")
        t1_data = extract_table_data(tables[0])
        save_to_csv("table1_properties.csv", t1_data)
    
    if len(tables) >= 2:
        print("Processing Table 2...")
        orders, deals = process_table_2(tables[1])
        save_to_csv("table2_orders.csv", orders)
        save_to_csv("table2_deals.csv", deals)
    else:
        print("Table 2 not found!")

if __name__ == "__main__":
    main()
