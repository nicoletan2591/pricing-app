# pricing-app
to create app to search database item 
#1. The "Safety First" Setup
#Library Handling: It uses pandas for data, pdfplumber for PDF reading, and BytesIO to handle file downloads without needing to save them to a hard drive.

#Session State (st.session_state): This is the most important part. It creates a "virtual basket." Even if you search for one thing, then search for something else, the items you "added to list" stay saved in the background.

#2. The "Smart Reader" (Uploader)
#Format Flexibility: It doesn't care if you upload a CSV, Excel, or PDF.

#Encoding Fixes: It automatically tries two different ways to read CSVs (utf-8 and cp1252) to prevent those common "weird character" crashes.

#PDF Extraction: If you upload a PDF, it iterates through every page, finds tables, and stitches them together into a single database.

#3. The "Auto-Cleaning" Brain
#Header Scrubbing: It automatically removes newlines and extra spaces from your column names. (e.g., it turns Primary\nField into Primary Field).

#Smart Detection: It scans your file's columns for keywords like "Field" or "Interest." This is why it can find your categories even if the column name isn't a perfect match.

#4. The Triple-Filter Search Engine
#It allows you to narrow down thousands of rows using three simultaneous methods:

#Category Dropdown: A list of unique values found in your "Primary Field" column.

#Interest Search: A text box specifically for searching research interests (like "Skin" or "DNA").

#General Search: A "catch-all" box that searches the entire row (Name, DOI, Grant number, etc.).

#5. The "Curation & Export" Workflow
#The Basket: When you find a group of researchers you like, you click "Add to Export List." This appends them to your collection while automatically removing duplicates.

