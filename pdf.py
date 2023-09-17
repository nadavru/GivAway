from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageTemplate, Frame, Image
from reportlab.platypus.flowables import Flowable
from reportlab.lib.units import inch
import datetime
from io import BytesIO
from PIL import Image as PILImage

# Convert PIL Image to BytesIO
def pil_to_byte(pil_image):
    byte_io = BytesIO()
    pil_image.save(byte_io, format='PNG')
    byte_io.seek(0)
    return byte_io

# Define a custom frame class to draw the green background for category titles
class CategoryTitleFrame(Flowable):
    def __init__(self, width, height, title):
        super().__init__()
        self.width = width
        self.height = height
        self.title = title

    def draw(self):
        # Zurich Blue!!!
        self.canv.setFillColorRGB(33/255.0, 103/255.0, 174/255.0)  # Set fill color to RGB(128, 128, 128)
        self.canv.rect(0, 0, self.width, self.height, fill=1)  # Draw rectangle with the set fill color
        self.canv.setFont("Helvetica-Bold", 12)
        text_width = self.canv.stringWidth(self.title, "Helvetica-Bold", 12)
        x = (self.width - text_width) / 2
        y = (self.height - 12) / 2
        self.canv.setFillColor(colors.white)
        self.canv.drawString(x, y, self.title)

# Function to create the PDF report
def create_pdf(questions_and_answers, categories, output_filename, image_before, image_after, damage):
    
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    
    def on_draw_page(canvas, doc):
        # Draw the logos
        left_logo = "zurich.jpg"  # Replace with your left logo path
        right_logo = "givaway.jpg"  # Replace with your right logo path
        
        canvas.drawInlineImage(left_logo, doc.leftMargin, doc.height + doc.topMargin - 0.05*inch, width=100, height=24)
        canvas.drawInlineImage(right_logo, doc.width + doc.leftMargin - 1*inch, doc.height + doc.topMargin - 0.05*inch, width=110, height=28)
    styles = getSampleStyleSheet()

    # Define a page template with a title centered at the top
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)
    doc.addPageTemplates([PageTemplate(id="report", frames=frame, onPage=on_draw_page)])
    
    # Create a list of Paragraph objects for questions and answers
    story = []

    title = Paragraph("Car Incident Report", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 12))  # Add spacing

    # Add the date and time of report
    current_datetime = datetime.datetime.now()
    current_date = current_datetime.strftime("%Y-%m-%d")
    current_time = current_datetime.strftime("%H:%M:%S")
    date_of_report = Paragraph(f"Date of Report: {current_date}", styles["Normal"])
    time_of_report = Paragraph(f"Time of Report: {current_time}", styles["Normal"])
    story.append(date_of_report)
    story.append(time_of_report)
    story.append(Spacer(1, 12))  # Add spacing

    for category in categories:
        qa_pairs = questions_and_answers[category]
        # Add the category title with green background and black text
        category_title = CategoryTitleFrame(doc.width, 30, category)
        #category_title = CategoryTitleFrame(doc.width - doc.leftMargin - doc.rightMargin, 30, category)
        story.append(category_title)

        story.append(Spacer(1, 12))

        if category=="The Incident":
            '''left_image_data = image_before.tobytes()
            left_image = Image(
                data=left_image_data,
                width=200,  # Set the width of the image
                height=200,  # Set the height of the image
            )
            right_image_data = image_after.tobytes()
            right_image = Image(
                data=right_image_data,
                width=200,  # Set the width of the image
                height=200,  # Set the height of the image
            )'''
            left_image = Image(pil_to_byte(image_before), width=200, height=200)  # Replace with the path to your left image
            right_image = Image(pil_to_byte(image_after), width=200, height=200)  # Replace with the path to your right image
            image_table = Table([[left_image, right_image]])
            image_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(image_table)
            story.append(Spacer(1, 12))  # Add spacing
            
            story.append(Paragraph(f"Car damage: {damage}", styles['Normal']))
            story.append(Spacer(1, 12))

        # Iterate through questions and answers within the category
        for question, answer in qa_pairs:
            if category=="Person Involved":
                question_text = question
                answer_text = answer
            else:
                question_text = f"Q: {question}"
                answer_text = f"A: {answer}"
            story.append(Paragraph(question_text, styles['Normal']))
            story.append(Paragraph(answer_text, styles['Normal']))
            story.append(Spacer(1, 12))

        # Add spacing between categories
        story.append(Spacer(1, 12))

    # Build the PDF document
    doc.build(story)

def data2pdf(q2a, question2category, categories, name, id, image_before, image_after, damage):

    questions_and_answers = {
        "Person Involved": [
            ("Full Name:", name),
            ("ID:", id),
        ]
    }

    for current_category in categories:
        questions = [question for question, category in question2category.items() if category==current_category]
        answers = [q2a[question] for question in questions]

        questions_and_answers[current_category] = [(question, answer) for question, answer in zip(questions, answers)]

    # Output PDF filename
    output_filename = f"policies/{name}_{id}_incident_report.pdf"

    categories = ["Person Involved"] + categories

    # Create the PDF
    create_pdf(questions_and_answers, categories, output_filename, image_before, image_after, damage)

    print(f"PDF document '{output_filename}' has been created.")

if __name__=="__main__":
    q2a = {"Date and Time of Incident:": "September 20, 2023, 10:30 AM",
                "Location of Incident:": "Main Street near Elm Avenue",
                "Description of Incident:": "The accident occurred due to foggy conditions, resulting in a collision.",
                "Were you injured?": "Yes, I sustained injuries to my neck and back.",
                "Passengers' Injuries:": "No passengers were in the car with me at the time.",
                }
    question2category = {"Date and Time of Incident:": "The Incident",
                "Location of Incident:": "The Incident",
                "Description of Incident:": "The Incident",
                "Were you injured?": "Injuries",
                "Passengers' Injuries:": "Injuries",
                }
    categories = ["The Incident", "Injuries"]
    name = "Nadav Rubinstein"
    id = "1234567890"
    data2pdf(q2a, question2category, categories, name, id)