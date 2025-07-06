from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
import os

# ==== CONFIGURATION ====

num_docs = 2  # How many documents you want (change this)
barcode_prefix = "Booklet2025"  # Prefix before barcode number

barcode_start = 1  # Starting number (e.g., 1 for ID-0001)

output_folder = "output_barcodes/"
os.makedirs(output_folder, exist_ok=True)

# Barcode size (points)
barcode_width = 113.4   # approx 7 cm
barcode_height = 30   # approx 1.75 cm

# Barcode position (points) — adjust these for exact placement
barcode_x = 150  # Distance from left
barcode_y = 400  # Distance from bottom

for i in range(barcode_start, barcode_start + num_docs):
    barcode_value = f"{barcode_prefix}{i:04d}"  # e.g., ID-0001

    # Create barcode
    barcode = code128.Code128(barcode_value, barHeight=barcode_height, barWidth=barcode_width / len(barcode_value))
    
    # Create PDF
    pdf_file = os.path.join(output_folder, f"document_{i:04d}.pdf")
    c = canvas.Canvas(pdf_file, pagesize=A4)
    page_width, page_height = A4
    
    # Optional: Add Title
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(page_width / 2, page_height - 100, f"Document {barcode_value}")
    
    # Draw Barcode at specified position
    barcode.drawOn(c, barcode_x, barcode_y)
    
    # Optional: Draw barcode value as text below barcode
    c.setFont("Helvetica", 12)
    c.drawCentredString(barcode_x + barcode_width / 2, barcode_y - 15, barcode_value)
    
    c.save()

print(f"✅ Successfully generated {num_docs} A4 barcode documents in '{output_folder}'")
