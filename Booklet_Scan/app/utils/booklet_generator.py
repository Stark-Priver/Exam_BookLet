from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
import os
import datetime

# Default configuration (can be overridden by function arguments)
DEFAULT_BARCODE_PREFIX = "BK"
DEFAULT_OUTPUT_FOLDER = "output_barcodes/"

# Barcode visual properties
BARCODE_WIDTH_POINTS = 113.4  # approx 4 cm at 72 DPI
BARCODE_HEIGHT_POINTS = 30    # approx 1.05 cm at 72 DPI
BARCODE_X_POS = 150
BARCODE_Y_POS = 700 # Positioned higher on the page

def generate_single_booklet(
    unique_id: str,
    output_folder: str = DEFAULT_OUTPUT_FOLDER,
    barcode_prefix: str = DEFAULT_BARCODE_PREFIX,
    student_name: str = "N/A",
    exam_name: str = "N/A"
) -> tuple[str | None, str | None]:
    """
    Generates a single PDF booklet with a unique barcode.

    Args:
        unique_id (str): A unique identifier to be part of the barcode and filename.
                         This could be a timestamp, a counter, or a combination.
        output_folder (str): Directory to save the generated PDF. Defaults to DEFAULT_OUTPUT_FOLDER.
        barcode_prefix (str): Prefix for the barcode value. Defaults to DEFAULT_BARCODE_PREFIX.
        student_name (str): Optional student name to print on the booklet.
        exam_name (str): Optional exam name to print on the booklet.

    Returns:
        tuple[str | None, str | None]: A tuple containing (file_path, barcode_value).
                                       Returns (None, None) if generation fails.
    """
    os.makedirs(output_folder, exist_ok=True)

    barcode_value = f"{barcode_prefix}{unique_id}"

    # Sanitize unique_id for use in filename (replace non-alphanumeric)
    safe_filename_id = "".join(c if c.isalnum() else "_" for c in unique_id)
    pdf_filename = f"Booklet_{barcode_prefix}_{safe_filename_id}.pdf"
    pdf_file_path = os.path.join(output_folder, pdf_filename)

    try:
        # Create barcode object
        # Adjust barWidth dynamically: ReportLab's barWidth is per bar, not total width.
        # A common approach is to estimate based on desired total width and number of characters.
        # For Code128, the number of bars varies. Let's use a fixed reasonable barWidth.
        # If barcode_width_pts is the total desired width, barWidth might be barcode_width_pts / (len(barcode_value) * N_MODULES_PER_CHAR_APPROX)
        # For simplicity, we'll use a fixed bar width that generally looks good.
        # You might need to fine-tune this if barcodes are too wide/narrow.
        estimated_bar_width = 0.8 # points
        barcode = code128.Code128(
            barcode_value,
            barHeight=BARCODE_HEIGHT_POINTS,
            barWidth=estimated_bar_width
        )

        # Create PDF
        c = canvas.Canvas(pdf_file_path, pagesize=A4)
        page_width, page_height = A4

        # Add Title and Info
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(page_width / 2, page_height - 70, "Exam Booklet")

        c.setFont("Helvetica", 12)
        c.drawString(BARCODE_X_POS, BARCODE_Y_POS + BARCODE_HEIGHT_POINTS + 25, f"Student: {student_name}")
        c.drawString(BARCODE_X_POS, BARCODE_Y_POS + BARCODE_HEIGHT_POINTS + 10, f"Exam: {exam_name}")

        # Draw Barcode at specified position
        # barcode.drawOn might require x, y for bottom-left corner of the barcode graphics area
        barcode.drawOn(c, BARCODE_X_POS, BARCODE_Y_POS)

        # Draw barcode value as text below barcode for human readability
        c.setFont("Helvetica", 10)
        # Calculate center for text under barcode based on its actual drawn width
        # barcode.width gives the calculated width of the barcode graphic
        text_x_pos = BARCODE_X_POS + barcode.width / 2
        c.drawCentredString(text_x_pos, BARCODE_Y_POS - 15, barcode_value)

        # Add a footer with generation date
        generation_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(page_width / 2, 30, f"Generated: {generation_time}")

        c.save()
        return pdf_file_path, barcode_value

    except Exception as e:
        print(f"Error generating booklet PDF '{pdf_filename}': {e}")
        return None, None

if __name__ == '__main__':
    print("Generating sample booklets using the refactored function...")

    # Example 1: Simple unique ID
    timestamp_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_path1, barcode1 = generate_single_booklet(
        unique_id=timestamp_id,
        student_name="John Doe",
        exam_name="Midterm CS101"
    )
    if file_path1:
        print(f"✅ Generated booklet: {file_path1} with barcode: {barcode1}")

    # Example 2: Another unique ID
    file_path2, barcode2 = generate_single_booklet(
        unique_id="STUD007EXAM03",
        barcode_prefix="EXAM",
        student_name="Jane Smith",
        exam_name="Finals PY202"
    )
    if file_path2:
        print(f"✅ Generated booklet: {file_path2} with barcode: {barcode2}")

    # Example 3: Test failure (e.g., by making output_folder unwritable if possible, or just observe)
    # This is harder to simulate directly without changing permissions,
    # but the error handling should catch issues during PDF generation.

    # Example of using it for multiple docs if needed (similar to old script)
    # num_docs_to_gen = 3
    # for i in range(1, num_docs_to_gen + 1):
    #     doc_id = f"DOC{i:03d}_{datetime.datetime.now().strftime('%H%M%S%f')}"
    #     fp, bc = generate_single_booklet(unique_id=doc_id, student_name=f"Student {i}", exam_name="General Exam")
    #     if fp:
    #         print(f"  -> Generated: {fp}, Barcode: {bc}")
    #     else:
    #         print(f"  -> Failed to generate booklet for ID {doc_id}")
