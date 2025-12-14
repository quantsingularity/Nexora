import numpy as np
import pandas as pd
from faker import Faker
from synthgauge import generate


class ClinicalDataGenerator:

    def __init__(self, seed: Any = 42) -> Any:
        self.faker = Faker()
        self.rng = np.random.default_rng(seed)

    def generate_patient_records(self, n: Any = 1000) -> Any:
        schema = {
            "patient_id": "uuid",
            "age": "integer(18,90)",
            "gender": "categorical(M,F,Other)",
            "diagnosis": "icd10_code",
            "medications": "list(ndc_code, max=5)",
            "readmission_risk": "float(0,1)",
        }
        data = generate(schema, n_samples=n, rng=self.rng)
        data["length_of_stay"] = self.rng.lognormal(1.2, 0.3, n)
        data["admission_date"] = [self.faker.date_between("-2y") for _ in range(n)]
        return pd.DataFrame(data).to_parquet(
            "data/synthetic/synthetic_patients.parquet"
        )
