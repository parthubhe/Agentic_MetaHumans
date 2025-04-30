DATABASE_FILE = r"./NA_Utils/patients.txt"

def load_patients():
    """Loads patient data from the database file."""
    patients = {}
    try:
        with open(DATABASE_FILE, "r") as f:
            for line in f:
                data = line.strip().split(",")
                if len(data) >= 4:  # Ensure enough data fields
                    name = data[0]
                    allergies = data[1].split(";") if data[1] else []
                    medications = data[2].split(";") if data[2] else []
                    emergency_contact_phone = data[3] if len(data) > 3 else "Unknown"
                    emergency_contact_name = data[4] if len(data) > 4 else "Unknown"
                    patients[name] = {
                        "allergies": allergies,
                        "medications": medications,
                        "emergency_contact": {"phone": emergency_contact_phone, "name": emergency_contact_name}
                    }
    except FileNotFoundError:
        print("Database file not found. Creating a new one.")
        open(DATABASE_FILE, "w").close()  # Create an empty file
    return patients

def save_patients(patients):
    """Saves patient data to the database file."""
    with open(DATABASE_FILE, "w") as f:
        for name, data in patients.items():
            allergies_str = ";".join(data["allergies"])
            medications_str = ";".join(data["medications"])
            line = f"{name},{allergies_str},{medications_str},{data['emergency_contact']['phone']},{data['emergency_contact']['name']}\n"
            f.write(line)

def validate_patient_data(data):
    """Validates patient data.  Add more validation rules as needed."""
    if not isinstance(data["allergies"], list):
        return False, "Allergies must be a list."
    if not isinstance(data["medications"], list):
        return False, "Medications must be a list."
    if not isinstance(data["emergency_contact"]["phone"], str):
        return False, "Emergency contact phone must be a string."
    return True, None