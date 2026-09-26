import xml.etree.ElementTree as ET


class XMLParser:

    @staticmethod
    def parse_xml(file_path):

        tree = ET.parse(file_path)

        root = tree.getroot()

        text = ""

        for element in root.iter():

            if element.text:

                text += (
                    f"{element.tag}: "
                    f"{element.text.strip()}\n"
                )

        return text