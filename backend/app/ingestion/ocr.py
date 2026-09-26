import easyocr

_reader = None


def _get_reader():
    global _reader

    if _reader is None:
        _reader = easyocr.Reader(["en"])

    return _reader


class OCRExtractor:

    @staticmethod
    def image_to_text(image_path):

        reader = _get_reader()

        results = reader.readtext(image_path)

        text = ""

        for result in results:
            text += result[1] + "\n"

        return text
