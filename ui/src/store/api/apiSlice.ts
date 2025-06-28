import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

// Types
export interface Patient {
  patient_id: string;
  name: string;
  birth_date: string;
  gender: string;
  age: number;
  conditions: any[];
  medications: any[];
  vital_signs?: any;
}

export interface ConversationRequest {
  patient_id: string;
  conversation_type: 'comprehensive' | 'emergency' | 'medication_review';
  chief_complaint?: string;
  urgency?: string;
  context?: any;
}

export interface ConversationResponse {
  conversation_id: string;
  patient_id: string;
  conversation_type: string;
  status: string;
  participants: string[];
  summary: any;
  full_conversation: any[];
  timestamp: string;
}

export interface AgentStatus {
  agent_name: string;
  status: 'active' | 'idle' | 'busy';
  specialty: string;
  current_patient?: string;
  response_time: number;
}

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NODE_ENV === 'production' 
      ? '/api' 
      : `${process.env.REACT_APP_NETWORK_PROTOCOL || 'http'}://${process.env.REACT_APP_NETWORK_HOST || 'localhost'}:8000`,
    prepareHeaders: (headers) => {
      headers.set('authorization', 'Bearer demo_token_12345');
      return headers;
    },
  }),
  tagTypes: ['Patient', 'Conversation', 'Agent'],
  endpoints: (builder) => ({
    // Health check
    checkHealth: builder.query<any, void>({
      query: () => '/health',
    }),
    
    // Patient endpoints
    getPatientSummary: builder.query<Patient, string>({
      query: (patientId) => `/patient/${patientId}/summary`,
      providesTags: ['Patient'],
    }),
    
    searchPatients: builder.query<Patient[], string>({
      query: (searchTerm) => `/patients/search?q=${searchTerm}`,
      providesTags: ['Patient'],
    }),
    
    // Conversation endpoints
    startComprehensiveConversation: builder.mutation<ConversationResponse, ConversationRequest>({
      query: (request) => ({
        url: '/conversation/comprehensive',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Conversation'],
    }),
    
    startEmergencyConversation: builder.mutation<ConversationResponse, ConversationRequest>({
      query: (request) => ({
        url: '/conversation/emergency',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Conversation'],
    }),
    
    startMedicationReview: builder.mutation<ConversationResponse, ConversationRequest>({
      query: (request) => ({
        url: '/conversation/medication-review',
        method: 'POST',
        body: request,
      }),
      invalidatesTags: ['Conversation'],
    }),
    
    getConversationHistory: builder.query<ConversationResponse[], { patientId?: string; limit?: number }>({
      query: ({ patientId, limit = 10 }) => ({
        url: '/conversations/history',
        params: { patient_id: patientId, limit },
      }),
      providesTags: ['Conversation'],
    }),
    
    // Agent endpoints
    getAgentStatus: builder.query<AgentStatus[], void>({
      query: () => '/agents/status',
      providesTags: ['Agent'],
    }),
    
    // CrewAI specific endpoints
    runCrewAIAssessment: builder.mutation<any, { patient_id: string; assessment_type: string }>({
      query: (request) => ({
        url: '/assessment/comprehensive',
        method: 'POST',
        body: request,
      }),
    }),
    
    runCrewAIEmergency: builder.mutation<any, { patient_id: string; chief_complaint: string; vital_signs: any }>({
      query: (request) => ({
        url: '/assessment/emergency',
        method: 'POST',
        body: request,
      }),
    }),
  }),
});

// Export hooks for usage in functional components
export const {
  useCheckHealthQuery,
  useGetPatientSummaryQuery,
  useSearchPatientsQuery,
  useStartComprehensiveConversationMutation,
  useStartEmergencyConversationMutation,
  useStartMedicationReviewMutation,
  useGetConversationHistoryQuery,
  useGetAgentStatusQuery,
  useRunCrewAIAssessmentMutation,
  useRunCrewAIEmergencyMutation,
} = apiSlice; 