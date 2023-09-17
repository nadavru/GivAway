from span_marker import SpanMarkerModel
from faker import Faker
import re
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from pypdf import PdfReader

class Anonymizer():
    def __init__(self):
        self.model = SpanMarkerModel.from_pretrained("tomaarsen/span-marker-mbert-base-multinerd")
        self.faker = Faker()
        self.months = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
    
    def _replace_months(self, text):
        # Use a regular expression to find month names in the text
        pattern = r'\b(?:' + '|'.join(self.months) + r')\b'
        matches = re.finditer(pattern, text)

        text_parts = []
        last_index = 0

        # Replace each matched month with a random month
        for match in matches:
            random_month = random.choice(self.months)
            text_parts.append(text[last_index:match.start()])
            text_parts.append(random_month)
            last_index = match.end()
        text_parts.append(text[last_index:])
        anonymized_text = "".join(text_parts)

        return anonymized_text
    
    def anonymize(self, text):
        #text = "John Doe resides at 123 Main Street and was diagnosed with Cystic Fibrosis on January 15, 2022."
        entities = self.model.predict(text)
        text_parts = []
        last_index = 0
        for entity in entities:
            if entity["score"]<0.6:
                continue
            if entity["label"]=="PER": # person
                start, end = entity["char_start_index"], entity["char_end_index"]
                text_parts.append(self._replace_months(text[last_index:start]))
                text_parts.append(self.faker.name())
                last_index = end+1
            if entity["label"]=="LOC": # location
                start, end = entity["char_start_index"], entity["char_end_index"]
                text_parts.append(self._replace_months(text[last_index:start]))
                text_parts.append(self.faker.address())
                last_index = end+1
        text_parts.append(self._replace_months(text[last_index:]))
        anonymized_text = "".join(text_parts)
        # remove name, address
        # diseases, age keeps
        # date transformed to year (for statistics)

        return anonymized_text

def anonymize_pdf(pdf_path, output_path):
    anonymizer = Anonymizer()

    # Create a list to store flowables (content elements) for the PDF
    elements = []

    output_pdf = SimpleDocTemplate(output_path, pagesize=letter)

    # Create a stylesheet for text formatting
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']

    reader = PdfReader(pdf_path)
    for page in reader.pages:
        page_text = page.extract_text()
        transformed_text = anonymizer.anonymize(page_text)

        page_paragraph = Paragraph(transformed_text, normal_style)
        elements.extend([page_paragraph, PageBreak()])
    elements = elements[:-1]

    # Build the PDF document
    output_pdf.build(elements)

if __name__=="__main__":
    anonymize_pdf("John_Smith.pdf", "John_Smith_anonymized.pdf")
    exit()

    '''anonymizer = Anonymizer()
    text = "John Doe resides at 123 Main Street and was diagnosed with Cystic Fibrosis on January 15, 2022."
    anonymized_text = anonymizer.anonymize(text)
    print(anonymized_text)'''