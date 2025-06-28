import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Patient {
  patient_id: string;
  name: string;
  birth_date: string;
  gender: string;
  age: number;
  phone?: string;
  email?: string;
  address?: string;
}

export interface PatientSummary extends Patient {
  conditions: any[];
  medications: any[];
  vital_signs?: any;
  allergies: string[];
  recent_visits: any[];
  risk_scores?: any;
}

interface PatientState {
  currentPatient: PatientSummary | null;
  searchResults: Patient[];
  searchTerm: string;
  isLoading: boolean;
  error: string | null;
  recentPatients: Patient[];
}

const initialState: PatientState = {
  currentPatient: null,
  searchResults: [],
  searchTerm: '',
  isLoading: false,
  error: null,
  recentPatients: [], // No mock data - will be populated from FHIR server
};

const patientSlice = createSlice({
  name: 'patients',
  initialState,
  reducers: {
    setCurrentPatient: (state, action: PayloadAction<PatientSummary>) => {
      state.currentPatient = action.payload;
      // Add to recent patients if not already there
      const exists = state.recentPatients.find(p => p.patient_id === action.payload.patient_id);
      if (!exists) {
        state.recentPatients.unshift({
          patient_id: action.payload.patient_id,
          name: action.payload.name,
          birth_date: action.payload.birth_date,
          gender: action.payload.gender,
          age: action.payload.age,
          phone: action.payload.phone,
          email: action.payload.email,
          address: action.payload.address,
        });
        // Keep only the 10 most recent
        if (state.recentPatients.length > 10) {
          state.recentPatients.pop();
        }
      }
    },
    clearCurrentPatient: (state) => {
      state.currentPatient = null;
    },
    setSearchResults: (state, action: PayloadAction<Patient[]>) => {
      state.searchResults = action.payload;
    },
    setSearchTerm: (state, action: PayloadAction<string>) => {
      state.searchTerm = action.payload;
    },
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.searchTerm = '';
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setCurrentPatient,
  clearCurrentPatient,
  setSearchResults,
  setSearchTerm,
  clearSearchResults,
  setLoading,
  setError,
  clearError,
} = patientSlice.actions;

export default patientSlice.reducer; 