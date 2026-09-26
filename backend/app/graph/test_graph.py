from app.graph.graph_builder import HospitalGraphBuilder


entities = {
    "hospital": "MedGraph Super Speciality Hospital",
    "department": "Endocrinology",
    "doctor": "Dr. Shreya Sharma",
    "patient": "Priya Verma",

    "diagnosis": [
        "Type 2 Diabetes Mellitus"
    ],

    "symptoms": [
        "Frequent urination",
        "Fatigue",
        "Increased thirst"
    ],

    "medicines": [
        "Metformin 500 mg twice daily"
    ],

    "lab_tests": [
        "HbA1c 8.2%",
        "Fasting Blood Sugar 165 mg/dL"
    ]
}


builder = HospitalGraphBuilder()

result = builder.create_patient_graph(
    entities,
    patient_id="manual-test",
    document_id="manual-test-doc"
)

print("Graph created successfully!")
print(result)