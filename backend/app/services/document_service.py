import os
import uuid
from datetime import datetime, timezone

from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import TextChunker
from app.extraction.llm_extractor import LLMExtractor

from app.database.session import SessionLocal

from app.services.document_save_service import DocumentSaveService
from app.graph.graph_builder import HospitalGraphBuilder
from app.vectorstore.chroma_manager import ChromaManager
from app.ingestion.deidentification import Deidentifier


class DocumentService:

    @staticmethod
    def process_document(file_path, document_id: str = None, deidentify: bool = False):
        """`deidentify` only affects the vector store (semantic search
        index) and what's returned to the caller for display - the
        Postgres record and graph entry created below still use the
        real, identified entities, since those power the clinical
        record-lookup features (patient search, journey timeline) that
        genuinely need a real identity to look someone up by. This
        mirrors how real de-identification is applied in practice: to
        the copy of the data used for broader search/analytics, not to
        the operational system of record."""

        document_id = document_id or str(uuid.uuid4())

        # -------------------------
        # Parse PDF
        # -------------------------
        text = DocumentParser.parse(file_path)

        # -------------------------
        # Chunk
        # -------------------------
        chunks = TextChunker.chunk_text(text)

        # -------------------------
        # Extract entities using Gemini
        # -------------------------
        entities = LLMExtractor.extract(text)

        # -------------------------
        # Save into PostgreSQL
        # -------------------------
        db = SessionLocal()

        try:

            patient = DocumentSaveService.save(
                db=db,
                entities=entities
            )

            patient_id = patient.id

        finally:
            db.close()

        # -------------------------
        # Embed chunks into the vector store for semantic search
        # -------------------------
        filename = os.path.basename(file_path)

        names = [entities.get("patient") or "", entities.get("doctor") or ""]

        stored_chunks = (
            [Deidentifier.deidentify_text(c, names=names) for c in chunks]
            if deidentify else chunks
        )

        chunk_ids = [
            f"{document_id}_{index}"
            for index in range(len(chunks))
        ]

        uploaded_at = datetime.now(timezone.utc).isoformat()

        # -------------------------
        # Create Knowledge Graph
        # -------------------------
        graph_builder = HospitalGraphBuilder()

        graph_builder.create_patient_graph(
            {**entities, "uploaded_at": uploaded_at},
            patient_id=patient_id,
            document_id=document_id,
        )

        chunk_metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
                "patient_id": patient_id,
                "patient": "[NAME]" if deidentify and entities.get("patient") else (entities.get("patient") or ""),
                "hospital": entities.get("hospital") or "",
                "doctor": "[NAME]" if deidentify and entities.get("doctor") else (entities.get("doctor") or ""),
                "department": entities.get("department") or "",
                "uploaded_at": uploaded_at,
                "deidentified": deidentify,
            }
            for index in range(len(chunks))
        ]

        ChromaManager.add_chunks(
            ids=chunk_ids,
            texts=stored_chunks,
            metadatas=chunk_metadatas
        )

        # -------------------------
        # Return response
        # -------------------------
        display_entities = (
            Deidentifier.deidentify_entities(entities) if deidentify else entities
        )

        return {

            "document_id": document_id,

            "characters": len(text),

            "total_chunks": len(chunks),

            "entities": display_entities,

            "patient_id": patient_id,

            "preview": stored_chunks[0] if stored_chunks else "",

            "deidentified": deidentify,

        }