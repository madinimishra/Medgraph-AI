import spacy


class EntityExtractor:

    nlp = spacy.load("en_core_web_sm")

    @staticmethod
    def extract_entities(text):

        doc = EntityExtractor.nlp(text)

        entities = []

        for entity in doc.ents:

            entities.append({
                "text": entity.text,
                "label": entity.label_
            })

        return entities