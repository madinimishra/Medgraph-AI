import json

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from app.core.dependencies import get_current_user
from app.ingestion.fhir_importer import FHIRImporter, FHIRImportError

router = APIRouter(
    prefix="/fhir",
    tags=["FHIR Import"]
)


@router.post("/import")
async def import_fhir_bundle(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):
    """Imports a FHIR R4 Bundle (JSON) - the real interoperability
    standard hospitals/EHR systems use to exchange data - directly
    into the knowledge graph. Patient/Encounter/Condition/Medication/
    Observation resources are mapped onto the same node/relationship
    schema the Synthea CSV pipeline uses, so an imported patient is
    immediately queryable through chat, the patient explorer, and
    network analysis like any other patient in the graph."""

    raw = await file.read()

    try:
        bundle = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Not valid JSON: {e}")

    try:
        counts = FHIRImporter().import_bundle(bundle)
    except FHIRImportError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "filename": file.filename,
        "imported": counts,
    }
