import numpy as np\nimport pandas as pd\nfrom synthgauge import generate
from faker import Faker

class ClinicalDataGenerator:
    def __init__(self, seed=42):
        self.faker = Faker()
        self.rng = np.random.default_rng(seed)
        
    def generate_patient_records(self, n=1000):
        schema = {
            "patient_id": "uuid",
            "age": "integer(18,90)",
            "gender": "categorical(M,F,Other)",
            "diagnosis": "icd10_code",
            "medications": "list(ndc_code, max=5)",
            "readmission_risk": "float(0,1)"
        }
        
        data = generate(schema, n_samples=n, rng=self.rng)
        
        # Add realistic temporal patterns
        data["length_of_stay"] = self.rng.lognormal(1.2, 0.3, n)
        data["admission_date"] = [
            self.faker.date_between("-2y") for _ in range(n)]
        
        return pd.DataFrame(data).to_parquet("data/synthetic/synthetic_patients.parquet")