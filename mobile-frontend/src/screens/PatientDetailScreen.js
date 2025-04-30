import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, Dimensions } from 'react-native';
import { LineChart } from 'react-native-chart-kit';

// Mock API service - replace with actual API calls later
const mockApiService = {
  getPatientDetails: async (patientId) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 700));
    // Return mock data based on ID
    if (patientId === 'p001') {
      return {
        id: 'p001',
        name: 'John Doe',
        risk: 0.75,
        predictions: {
          risk: 0.75,
          top_features: ['age', 'previous_admissions', 'diabetes'],
          cohort_size: 120,
          shap_features: ['age', 'prev_adm', 'diabetes', 'htn', 'hf'],
          shap_values: [0.3, 0.25, 0.2, 0.15, 0.1]
        },
        explanations: { method: 'SHAP', values: [0.3, 0.25, 0.2, 0.15, 0.1] },
        uncertainty: { confidence_interval: [0.65, 0.85] },
        timeline: [
          { event: 'Admission', date: '2024-04-10' },
          { event: 'Lab Test', date: '2024-04-11' },
          { event: 'Diagnosis: HF', date: '2024-04-12' },
          { event: 'Discharge', date: '2024-04-18' },
        ]
      };
    } else if (patientId === 'p003') {
        return {
            id: 'p003',
            name: 'Robert Johnson',
            risk: 0.85,
            predictions: {
              risk: 0.85,
              top_features: ['comorbidities', 'age', 'lab_value_x'],
              cohort_size: 95,
              shap_features: ['comorb', 'age', 'lab_x', 'med_y', 'prev_adm'],
              shap_values: [0.4, 0.2, 0.15, 0.05, 0.05]
            },
            explanations: { method: 'SHAP', values: [0.4, 0.2, 0.15, 0.05, 0.05] },
            uncertainty: { confidence_interval: [0.78, 0.92] },
            timeline: [
              { event: 'Admission', date: '2024-04-05' },
              { event: 'Surgery', date: '2024-04-07' },
              { event: 'ICU Stay', date: '2024-04-08' },
              { event: 'Discharge', date: '2024-04-20' },
            ]
          };
    }
    // Default mock data
    return {
      id: patientId,
      name: 'Default Patient',
      risk: 0.55,
      predictions: {
        risk: 0.55,
        top_features: ['feature_a', 'feature_b', 'feature_c'],
        cohort_size: 150,
        shap_features: ['feat_a', 'feat_b', 'feat_c', 'feat_d', 'feat_e'],
        shap_values: [0.2, 0.15, 0.1, 0.05, 0.05]
      },
      explanations: { method: 'SHAP', values: [0.2, 0.15, 0.1, 0.05, 0.05] },
      uncertainty: { confidence_interval: [0.45, 0.65] },
      timeline: []
    };
  }
};

const PatientDetailScreen = ({ route }) => {
  const { patientId, patientName } = route.params;
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDetails = async () => {
      try {
        const patientDetails = await mockApiService.getPatientDetails(patientId);
        setDetails(patientDetails);
      } catch (error) {
        console.error("Failed to load patient details:", error);
        // Handle error display
      } finally {
        setLoading(false);
      }
    };
    loadDetails();
  }, [patientId]);

  if (loading) {
    return (
      <View style={styles.centered}><ActivityIndicator size="large" /></View>
    );
  }

  if (!details) {
    return (
      <View style={styles.centered}><Text>Could not load patient details.</Text></View>
    );
  }

  const chartConfig = {
    backgroundGradientFrom: "#ffffff",
    backgroundGradientTo: "#ffffff",
    decimalPlaces: 2, // optional, defaults to 2dp
    color: (opacity = 1) => `rgba(0, 122, 255, ${opacity})`,
    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
    style: {
      borderRadius: 16
    },
    propsForDots: {
      r: "6",
      strokeWidth: "2",
      stroke: "#007AFF"
    }
  };

  const shapData = {
    labels: details.predictions.shap_features.slice(0, 5), // Top 5 features
    datasets: [
      {
        data: details.predictions.shap_values.slice(0, 5)
      }
    ]
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>{patientName} - Prediction Details</Text>
      
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Overall Risk</Text>
        <Text style={styles.riskText}>{`${(details.risk * 100).toFixed(0)}%`}</Text>
        <Text style={styles.subText}>Confidence Interval: [{details.uncertainty.confidence_interval[0]*100}%, {details.uncertainty.confidence_interval[1]*100}%]</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Top Risk Factors (SHAP Values)</Text>
        <LineChart
          data={shapData}
          width={Dimensions.get("window").width - 30} // from react-native
          height={220}
          yAxisLabel="Impact "
          yAxisSuffix=""
          chartConfig={chartConfig}
          bezier
          style={styles.chart}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Key Contributing Factors</Text>
        {details.predictions.top_features.map((feature, index) => (
          <Text key={index} style={styles.listItem}>- {feature}</Text>
        ))}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Patient Timeline</Text>
        {details.timeline.length > 0 ? (
          details.timeline.map((event, index) => (
            <Text key={index} style={styles.listItem}>{event.date}: {event.event}</Text>
          ))
        ) : (
          <Text style={styles.subText}>No timeline data available.</Text>
        )}
      </View>

    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 15,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  riskText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#007AFF',
    textAlign: 'center',
    marginBottom: 5,
  },
  subText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 10,
  },
  listItem: {
    fontSize: 15,
    color: '#444',
    marginBottom: 5,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
});

export default PatientDetailScreen;

