from fpdf import FPDF
import os

# Create a new PDF document
pdf = FPDF()

# Add a page
pdf.add_page()

# Set font
pdf.set_font("Arial", size=12)

# Read the text file
with open("uploads/test_document.txt", "r") as file:
    for line in file:
        # Add each line to the PDF
        pdf.cell(200, 10, txt=line, ln=True, align='L')

# Save the PDF
pdf.output("uploads/test_document.pdf")

print("PDF created at: uploads/test_document.pdf")
