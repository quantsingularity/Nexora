import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd
import pytest
from data_pipeline.data_validation import DataValidator

# ---------------------------------------------------------------------------
# MockFHIRConnector mirrors the real FHIRConnector API for offline tests
# ---------------------------------------------------------------------------


class MockFHIRConnector:
    RESOURCE_TYPES = ["Patient", "Observation", "Condition", "MedicationRequest"]

    def __init__(
        self,
        patients=None,
        observations=None,
        conditions=None,
        medications=None,
        connection_error=False,
        auth_error=False,
    ):
        self.patients = patients or []
        self.observations = observations or []
        self.conditions = conditions or []
        self.medications = medications or []
        self.connection_error = connection_error
        self.auth_error = auth_error
        self.resources = {
            "Patient": self.patients,
            "Observation": self.observations,
            "Condition": self.conditions,
            "MedicationRequest": self.medications,
        }

    def search(self, resource_type, params=None, max_count=None):
        if self.connection_error:
            raise Exception("Connection error")
        if self.auth_error:
            raise Exception("Authentication error")
        if resource_type not in self.resources:
            raise ValueError(f"Unknown resource type: {resource_type}")
        resources = list(self.resources[resource_type])
        if params:
            filtered = []
            for r in resources:
                match = True
                for key, value in params.items():
                    if key == "name" and r.get("resourceType") == "Patient":
                        fam = r.get("name", [{}])[0].get("family", "")
                        if value not in fam:
                            match = False
                    elif key == "code":
                        if r.get("resourceType") == "Observation":
                            c = r.get("code", {}).get("coding", [{}])[0].get("code", "")
                            if value != c:
                                match = False
                        elif r.get("resourceType") == "Condition":
                            found = any(
                                coding.get("code") == value
                                for coding in r.get("code", {}).get("coding", [])
                            )
                            if not found:
                                match = False
                if match:
                    filtered.append(r)
            resources = filtered
        if max_count is not None:
            resources = resources[:max_count]
        return resources

    def patients_to_dataframe(self, patients):
        data = []
        for p in patients:
            name = p.get("name", [{}])[0]
            telecom = p.get("telecom", [])
            addr = p.get("address", [{}])[0]
            data.append(
                {
                    "patient_id": p.get("id", ""),
                    "family_name": name.get("family", ""),
                    "given_name": " ".join(name.get("given", [])),
                    "gender": p.get("gender", ""),
                    "birth_date": p.get("birthDate", ""),
                    "address_line": ", ".join(addr.get("line", [])),
                    "city": addr.get("city", ""),
                    "state": addr.get("state", ""),
                    "postal_code": addr.get("postalCode", ""),
                    "country": addr.get("country", ""),
                    "phone": next(
                        (t["value"] for t in telecom if t.get("system") == "phone"), ""
                    ),
                    "email": next(
                        (t["value"] for t in telecom if t.get("system") == "email"), ""
                    ),
                }
            )
        return pd.DataFrame(data)

    def observations_to_dataframe(self, observations):
        data = []
        for obs in observations:
            coding = obs.get("code", {}).get("coding", [{}])[0]
            value, unit = None, ""
            if "valueQuantity" in obs:
                value = obs["valueQuantity"].get("value")
                unit = obs["valueQuantity"].get("unit", "")
            data.append(
                {
                    "observation_id": obs.get("id", ""),
                    "patient_id": obs.get("subject", {})
                    .get("reference", "")
                    .replace("Patient/", ""),
                    "date": obs.get("effectiveDateTime", ""),
                    "code": coding.get("code", ""),
                    "system": coding.get("system", ""),
                    "display": coding.get("display", ""),
                    "value": value,
                    "unit": unit,
                    "status": obs.get("status", ""),
                }
            )
        return pd.DataFrame(data)

    def conditions_to_dataframe(self, conditions):
        data = []
        for cond in conditions:
            code, system, display = "", "", ""
            for coding in cond.get("code", {}).get("coding", []):
                if coding.get("system") == "http://hl7.org/fhir/sid/icd-10-cm":
                    code, system, display = (
                        coding.get("code", ""),
                        coding.get("system", ""),
                        coding.get("display", ""),
                    )
                    break
            if not code and cond.get("code", {}).get("coding"):
                c0 = cond["code"]["coding"][0]
                code, system, display = (
                    c0.get("code", ""),
                    c0.get("system", ""),
                    c0.get("display", ""),
                )
            data.append(
                {
                    "condition_id": cond.get("id", ""),
                    "patient_id": cond.get("subject", {})
                    .get("reference", "")
                    .replace("Patient/", ""),
                    "onset_date": cond.get("onsetDateTime", ""),
                    "code": code,
                    "system": system,
                    "display": display,
                    "clinical_status": cond.get("clinicalStatus", {})
                    .get("coding", [{}])[0]
                    .get("code", ""),
                }
            )
        return pd.DataFrame(data)

    def medications_to_dataframe(self, medications):
        data = []
        for med in medications:
            med_display, code, system = "", "", ""
            if "medicationCodeableConcept" in med:
                mc = med["medicationCodeableConcept"].get("coding", [{}])[0]
                med_display = mc.get("display", "")
                code = mc.get("code", "")
                system = mc.get("system", "")
            dosage_text = ""
            if med.get("dosageInstruction"):
                dosage_text = med["dosageInstruction"][0].get("text", "")
            data.append(
                {
                    "medication_id": med.get("id", ""),
                    "patient_id": med.get("subject", {})
                    .get("reference", "")
                    .replace("Patient/", ""),
                    "authored_date": med.get("authoredOn", ""),
                    "medication_display": med_display,
                    "code": code,
                    "system": system,
                    "dosage_text": dosage_text,
                    "status": med.get("status", ""),
                }
            )
        return pd.DataFrame(data)

    def dataframe_to_patients(self, df):
        patients = []
        for _, row in df.iterrows():
            patient = {
                "resourceType": "Patient",
                "id": row.get("patient_id", ""),
                "name": [
                    {
                        "family": row.get("family_name", ""),
                        "given": (
                            row.get("given_name", "").split()
                            if row.get("given_name")
                            else []
                        ),
                    }
                ],
                "gender": row.get("gender", ""),
                "birthDate": row.get("birth_date", ""),
            }
            patients.append(patient)
        return patients

    def bulk_export(self, resource_types, output_dir, format_type="json"):
        if self.connection_error:
            raise Exception("Connection error")
        os.makedirs(output_dir, exist_ok=True)
        result = {}
        for rt in resource_types:
            if rt not in self.resources or not self.resources[rt]:
                continue
            fp = os.path.join(output_dir, f"{rt}.{format_type}")
            with open(fp, "w") as f:
                json.dump(self.resources[rt], f)
            result[rt] = fp
        return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_patient():
    return {
        "resourceType": "Patient",
        "id": "patient-001",
        "name": [{"use": "official", "family": "Smith", "given": ["John", "Edward"]}],
        "gender": "male",
        "birthDate": "1970-01-25",
        "address": [
            {
                "use": "home",
                "line": ["123 Main St"],
                "city": "Anytown",
                "state": "CA",
                "postalCode": "12345",
                "country": "USA",
            }
        ],
        "telecom": [
            {"system": "phone", "value": "555-123-4567"},
            {"system": "email", "value": "john.smith@example.com"},
        ],
        "identifier": [
            {"system": "http://hl7.org/fhir/sid/us-ssn", "value": "123-45-6789"}
        ],
    }


@pytest.fixture
def sample_observation():
    return {
        "resourceType": "Observation",
        "id": "observation-001",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "8480-6",
                    "display": "Systolic blood pressure",
                }
            ]
        },
        "subject": {"reference": "Patient/patient-001"},
        "effectiveDateTime": "2023-05-15T10:25:00Z",
        "valueQuantity": {"value": 120, "unit": "mmHg"},
    }


@pytest.fixture
def sample_condition():
    return {
        "resourceType": "Condition",
        "id": "condition-001",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                }
            ]
        },
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "code": "I10",
                    "display": "Essential (primary) hypertension",
                },
                {
                    "system": "http://snomed.info/sct",
                    "code": "38341003",
                    "display": "Hypertension",
                },
            ]
        },
        "subject": {"reference": "Patient/patient-001"},
        "onsetDateTime": "2022-01-10",
    }


@pytest.fixture
def sample_medication():
    return {
        "resourceType": "MedicationRequest",
        "id": "medication-request-001",
        "status": "active",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197361",
                    "display": "Amlodipine 5 MG Oral Tablet",
                }
            ]
        },
        "subject": {"reference": "Patient/patient-001"},
        "authoredOn": "2023-05-15",
        "dosageInstruction": [{"text": "Take 1 tablet by mouth once daily"}],
    }


@pytest.fixture
def mock_connector(
    sample_patient, sample_observation, sample_condition, sample_medication
):
    return MockFHIRConnector(
        patients=[sample_patient],
        observations=[sample_observation],
        conditions=[sample_condition],
        medications=[sample_medication],
    )


@pytest.fixture
def validator():
    return DataValidator()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_patient_conversion(mock_connector, sample_patient):
    df = mock_connector.patients_to_dataframe([sample_patient])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in ["patient_id", "family_name", "given_name", "gender", "birth_date"]:
        assert col in df.columns
    assert df.iloc[0]["patient_id"] == "patient-001"
    assert df.iloc[0]["family_name"] == "Smith"
    assert df.iloc[0]["gender"] == "male"
    assert df.iloc[0]["birth_date"] == "1970-01-25"


def test_observation_conversion(mock_connector, sample_observation):
    df = mock_connector.observations_to_dataframe([sample_observation])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in [
        "observation_id",
        "patient_id",
        "code",
        "display",
        "value",
        "unit",
        "date",
    ]:
        assert col in df.columns
    assert df.iloc[0]["observation_id"] == "observation-001"
    assert df.iloc[0]["patient_id"] == "patient-001"
    assert df.iloc[0]["code"] == "8480-6"
    assert df.iloc[0]["value"] == 120
    assert df.iloc[0]["unit"] == "mmHg"


def test_condition_conversion(mock_connector, sample_condition):
    df = mock_connector.conditions_to_dataframe([sample_condition])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in [
        "condition_id",
        "patient_id",
        "code",
        "display",
        "onset_date",
        "clinical_status",
    ]:
        assert col in df.columns
    assert df.iloc[0]["condition_id"] == "condition-001"
    assert df.iloc[0]["patient_id"] == "patient-001"
    assert df.iloc[0]["clinical_status"] == "active"
    assert "I10" in df.iloc[0]["code"]


def test_medication_conversion(mock_connector, sample_medication):
    df = mock_connector.medications_to_dataframe([sample_medication])
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in [
        "medication_id",
        "patient_id",
        "medication_display",
        "status",
        "authored_date",
    ]:
        assert col in df.columns
    assert df.iloc[0]["medication_id"] == "medication-request-001"
    assert df.iloc[0]["patient_id"] == "patient-001"
    assert df.iloc[0]["status"] == "active"
    assert "Amlodipine" in df.iloc[0]["medication_display"]


def test_bulk_export(mock_connector, tmp_path):
    result = mock_connector.bulk_export(
        resource_types=["Patient", "Observation", "Condition", "MedicationRequest"],
        output_dir=str(tmp_path),
        format_type="json",
    )
    assert isinstance(result, dict)
    assert len(result) == 4
    for rt in ["Patient", "Observation", "Condition", "MedicationRequest"]:
        fp = os.path.join(str(tmp_path), f"{rt}.json")
        assert os.path.exists(fp)
        with open(fp) as f:
            content = json.load(f)
        assert isinstance(content, list)
        assert len(content) > 0


def test_dataframe_to_fhir(mock_connector, sample_patient):
    df = mock_connector.patients_to_dataframe([sample_patient])
    fhir_patients = mock_connector.dataframe_to_patients(df)
    assert isinstance(fhir_patients, list)
    assert len(fhir_patients) > 0
    assert fhir_patients[0]["resourceType"] == "Patient"
    assert fhir_patients[0]["id"] == "patient-001"


def test_data_validation_integration(mock_connector, sample_patient, validator):
    df = mock_connector.patients_to_dataframe([sample_patient])
    schema = {
        "patient_id": {"type": "string", "required": True, "unique": True},
        "family_name": {"type": "string", "required": True},
        "given_name": {"type": "string", "required": True},
        "gender": {
            "type": "category",
            "required": True,
            "categories": ["male", "female", "other", "unknown"],
        },
        "birth_date": {"type": "string", "required": True},
    }
    result = validator.validate_schema(df, schema)
    assert isinstance(result, dict)
    assert result["valid"]
    assert len(result.get("errors", [])) == 0


def test_search_functionality(mock_connector):
    patients = mock_connector.search("Patient", {"name": "Smith"})
    assert isinstance(patients, list)
    assert len(patients) > 0
    obs = mock_connector.search("Observation", {"code": "8480-6"})
    assert len(obs) > 0
    conds = mock_connector.search("Condition", {"code": "I10"})
    assert len(conds) > 0


def test_error_handling_invalid_resource(mock_connector):
    with pytest.raises(ValueError):
        mock_connector.search("InvalidResourceType")


def test_error_handling_connection_error():
    conn = MockFHIRConnector(connection_error=True)
    with pytest.raises(Exception):
        conn.search("Patient")


def test_error_handling_auth_error():
    conn = MockFHIRConnector(auth_error=True)
    with pytest.raises(Exception):
        conn.search("Patient")


def test_pagination(sample_patient):
    many = [dict(sample_patient, id=f"patient-{i:03d}") for i in range(20)]
    conn = MockFHIRConnector(patients=many)
    ten = conn.search("Patient", max_count=10)
    assert len(ten) == 10
    all_p = conn.search("Patient")
    assert len(all_p) == 20


def test_data_integration(
    mock_connector,
    sample_patient,
    sample_observation,
    sample_condition,
    sample_medication,
):
    patients_df = mock_connector.patients_to_dataframe([sample_patient])
    obs_df = mock_connector.observations_to_dataframe([sample_observation])
    cond_df = mock_connector.conditions_to_dataframe([sample_condition])
    med_df = mock_connector.medications_to_dataframe([sample_medication])

    po = pd.merge(patients_df, obs_df, on="patient_id", how="inner")
    pc = pd.merge(patients_df, cond_df, on="patient_id", how="inner")
    pm = pd.merge(patients_df, med_df, on="patient_id", how="inner")

    assert len(po) > 0
    assert len(pc) > 0
    assert len(pm) > 0
    assert po.iloc[0]["family_name"] == "Smith"
    assert pc.iloc[0]["family_name"] == "Smith"
    assert pm.iloc[0]["family_name"] == "Smith"
