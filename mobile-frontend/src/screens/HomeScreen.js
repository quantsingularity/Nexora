import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Button } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock API service - replace with actual API calls later
const mockApiService = {
  getPatients: async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    // Return mock data
    return [
      { id: 'p001', name: 'John Doe', age: 65, risk: 0.75, last_update: '2024-04-28' },
      { id: 'p002', name: 'Jane Smith', age: 72, risk: 0.40, last_update: '2024-04-29' },
      { id: 'p003', name: 'Robert Johnson', age: 58, risk: 0.85, last_update: '2024-04-27' },
      { id: 'p004', name: 'Emily Davis', age: 81, risk: 0.60, last_update: '2024-04-29' },
    ];
  }
};

const HomeScreen = ({ navigation }) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [username, setUsername] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const storedUsername = await AsyncStorage.getItem('username');
        setUsername(storedUsername || 'User');
        const patientData = await mockApiService.getPatients();
        setPatients(patientData);
      } catch (error) {
        console.error("Failed to load data:", error);
        // Handle error display if needed
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const handleLogout = async () => {
    await AsyncStorage.removeItem('userToken');
    await AsyncStorage.removeItem('username');
    navigation.replace('Login');
  };

  const renderPatient = ({ item }) => (
    <TouchableOpacity 
      style={styles.patientItem}
      onPress={() => navigation.navigate('PatientDetail', { patientId: item.id, patientName: item.name })}>
      <View style={styles.patientInfo}>
        <Text style={styles.patientName}>{item.name}</Text>
        <Text style={styles.patientDetails}>Age: {item.age} | Last Update: {item.last_update}</Text>
      </View>
      <Text style={[styles.riskScore, { color: item.risk > 0.7 ? 'red' : (item.risk > 0.5 ? 'orange' : 'green') }]}>
        {`${(item.risk * 100).toFixed(0)}%`}
      </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centered}><ActivityIndicator size="large" /></View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.welcomeText}>Welcome, {username}!</Text>
        <Button title="Logout" onPress={handleLogout} />
      </View>
      <FlatList
        data={patients}
        renderItem={renderPatient}
        keyExtractor={item => item.id}
        ListHeaderComponent={<Text style={styles.listTitle}>Patient Risk Overview</Text>}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  welcomeText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  listTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    margin: 15,
    marginBottom: 10,
  },
  patientItem: {
    backgroundColor: '#fff',
    padding: 15,
    marginVertical: 5,
    marginHorizontal: 10,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    elevation: 1, // for Android shadow
    shadowColor: '#000', // for iOS shadow
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  patientInfo: {
    flex: 1,
  },
  patientName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 3,
  },
  patientDetails: {
    fontSize: 12,
    color: '#666',
  },
  riskScore: {
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});

export default HomeScreen;

