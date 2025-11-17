class HealthcareETL(beam.PTransform):
    def expand(self, pcoll):
        return (
            pcoll
            | "ParseFHIR" >> beam.Map(parse_fhir_bundle)
            | "ValidateClinicalData" >> beam.Map(ClinicalValidator().validate)
            | "EncodeMedicalConcepts"
            >> beam.ParDo(ICD10Encoder(config["coding_systems"]))
            | "TemporalAlignment"
            >> beam.WindowInto(beam.window.SlidingWindows(3600, 900))
            | "FeatureGeneration" >> beam.ParDo(ClinicalFeatureGenerator())
            | "WriteToFeatureStore"
            >> beam.io.WriteToFeast(
                feature_store=config["feature_store"],
                entity_mapping=config["entity_map"],
            )
        )
