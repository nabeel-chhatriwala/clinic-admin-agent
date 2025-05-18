from pipecat.adapters.schemas.function_schema import FunctionSchema

available_doctors = ["Dr. Patel", "Dr. Rivera", "Dr. Kim"]

schedule_appointment_function = FunctionSchema(
    name="schedule_appointment",
    description="Schedule a healthcare appointment for a patient",
    properties={
        "first_name": {
            "type": "string",
            "description": "First name of the patient. It must be exactly as how the user spelled it.",
        },
        "last_name": {
            "type": "string",
            "description": "Last name of the patient. It must be exactly as how the user spelled it.",
        },
        "preferred_date": {
            "type": "string",
            "description": "Preferred appointment date in YYYY-MM-DD format",
        },
        "preferred_time": {
            "type": "string",
            "description": "Preferred appointment time in HH:MM format (24-hour clock)",
        },
        "reason_for_visit": {
            "type": "string",
            "description": "Reason for the visit, e.g. check-up, rash, flu symptoms",
        },
        "doctor_preference": {
            "type": "string",
            "description": "Optional doctor name the patient would prefer to see",
            "enum": available_doctors
        }
    },
    required=["first_name", "last_name", "preferred_date", "preferred_time", "reason_for_visit"]
)
verify_insurance_function = FunctionSchema(
    name="verify_insurance",
    description="Verify if the patient's insurance is accepted and active",
    properties={
        "first_name": {
            "type": "string",
            "description": "First name of the patient. It must be exactly as how the user spelled it.",
        },
        "last_name": {
            "type": "string",
            "description": "Last name of the patient. It must be exactly as how the user spelled it.",
        },
        "provider": {
            "type": "string",
            "description": "Name of the patient's insurance provider",
            "enum": ["blue cross", "blue shield", "aetna"]
        },
        "policy_number": {
            "type": "integer",
            "description": "Insurance policy number provided by the patient",
        },
        "procedure": {
            "type": "string",
            "description": "Procedure that the patient wants to be covered",
            "enum": ["Routine check-up", "Flu shot", "Blood test", "X-ray", "Cholesterol screening", "MRI", "Pap smear"]
        }
    },
    required=["first_name", "last_name", "provider", "policy_number", "procedure"]
)


end_conversation_function = FunctionSchema(
    name="end_conversation",
    description="End the conversation politely when the user has no further questions or is finished.",
    properties={
        "closing_message": {
            "type": "string",
            "description": "A polite closing message for the conversation that mentions the user's first name and last name.  Something that thanks the user for calling Windermere Medical Clinic.",
        }
    },
    required=["closing_message"],
)