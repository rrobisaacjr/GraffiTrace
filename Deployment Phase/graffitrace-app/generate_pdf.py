from reportlab.lib.pagesizes import letter, landscape  # Import landscape
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
from PIL import Image

def generate_pdf_report(pdf_path, project_directory, graffiti_data):
    """
    Generates a PDF report with the graffiti data, including map and details.

    Args:
        pdf_path (str): Path to save the PDF report.
        project_directory (str):  The project directory.
        graffiti_data (pd.DataFrame): DataFrame containing the graffiti data.
    """
    c = canvas.Canvas(pdf_path, pagesize=landscape(letter))  # Changed to landscape
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    title_style = styles['h1']

    # Title
    title = Paragraph("Graffiti Detection Report", title_style)
    title.wrapOn(c, landscape(letter)[0], landscape(letter)[1])
    title.drawOn(c, inch, 7.5 * inch)  # Adjusted for landscape

    # Introduction
    intro_text = "This report provides an overview of the graffiti detected in the target area."
    intro = Paragraph(intro_text, normal_style)
    intro.wrapOn(c, 10 * inch, 1 * inch)  # Adjusted for landscape
    intro.drawOn(c, inch, 7 * inch)  # Adjusted for landscape
    c.showPage()

    # # Map Image
    # c.drawString(inch, 7.5 * inch, "Graffiti Locations:")
    # map_img_path = os.path.join(project_directory, "results", "map_screenshot.png")
    # if os.path.exists(map_img_path):
    #     try:
    #         map_img = Image.open(map_img_path)
    #         aspect_ratio = map_img.width / map_img.height
    #         max_width_pdf = 10 * inch  # Adjusted for landscape
    #         image_width_pdf = min(map_img.width, max_width_pdf)
    #         image_height_pdf = image_width_pdf / aspect_ratio
    #         c.drawImage(map_img_path, inch, 4.5 * inch, width=image_width_pdf,
    #                     height=image_height_pdf)  # Adjusted for landscape
    #     except Exception as e:
    #         print(f"Error including map image: {e}")
    #         c.drawString(inch, 4.5 * inch, "Error loading map image.")  # Adjusted for landscape
    # else:
    #     c.drawString(inch, 4.5 * inch, "Map Image Not Available")  # Adjusted for landscape

    # Create table for graffiti data with pagination
    data = [['Graffiti ID', 'Source File Name', 'Place', 'Latitude', 'Longitude', 'Instances']]
    table_data = [['Graffiti ID', 'Source File Name', 'Place', 'Latitude', 'Longitude', 'Instances']]  # Hold data for current page
    row_count = 0
    y_position = 7 * inch  # start position of table

    for _, row in graffiti_data.iterrows():
        table_data.append([
            row['graffiti_id'],
            row['source_file_name'],
            row['place'],
            row['latitude'],
            row['longitude'],
            row['num_graffiti_instances']
        ])
        row_count += 1

        if row_count >= 25:  # 25 rows per page
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            table_height = table.wrapOn(c, landscape(letter)[0], landscape(letter)[1])[1]
            table.drawOn(c, inch, y_position - table_height)
            c.showPage()
            table_data = [['Graffiti ID', 'Source File Name', 'Place', 'Latitude',
                           'Longitude', 'Instances']]  # reset
            row_count = 0
            y_position = 7 * inch

    # Add any remaining data on the last page
    if len(table_data) > 1:
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        table_height = table.wrapOn(c, landscape(letter)[0], landscape(letter)[1])[1]
        table.drawOn(c, inch, y_position - table_height)

    c.save()
    print(f"PDF Report Generated at {pdf_path}")