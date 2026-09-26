import os
import fitz
from docx import Document
from pdf2image import convert_from_path
from app.ingestion.tabular_parser import TabularParser
from app.ingestion.ocr import OCRExtractor
from app.ingestion.xml_parser import XMLParser

class DocumentParser:

    @staticmethod
    def parse(file_path: str):

        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":
            return DocumentParser._parse_pdf(file_path)

        elif extension == ".docx":
            return DocumentParser._parse_docx(file_path)

        elif extension == ".txt":
            return DocumentParser._parse_txt(file_path)

        elif extension in [".png", ".jpg", ".jpeg"]:
            return OCRExtractor.image_to_text(file_path)

        elif extension == ".csv":
            return TabularParser.parse_csv(file_path)

        elif extension == ".xlsx":
            return TabularParser.parse_excel(file_path)

        elif extension == ".xls":
            return TabularParser.parse_excel(file_path)

        elif extension == ".xml":
            return XMLParser.parse_xml(file_path)

        else:
            raise Exception(f"Unsupported file type: {extension}")

    @staticmethod
    def _parse_pdf(file_path):

        document = fitz.open(file_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        # If no selectable text exists,
        # treat it as a scanned PDF.

        if text.strip() == "":
            return DocumentParser._parse_scanned_pdf(file_path)

        return text

    @staticmethod
    def _parse_scanned_pdf(file_path):

        pages = convert_from_path(file_path)

        text = ""

        for index, page in enumerate(pages):

            image_path = f"temp_page_{index}.png"

            page.save(image_path, "PNG")

            text += OCRExtractor.image_to_text(image_path)

            if os.path.exists(image_path):
                os.remove(image_path)

        return text

    @staticmethod
    def _parse_docx(file_path):

        document = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        return text

    @staticmethod
    def _parse_txt(file_path):

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return file.read()