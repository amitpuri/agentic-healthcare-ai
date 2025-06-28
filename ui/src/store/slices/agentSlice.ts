import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Agent {
  id: string;
  name: string;
  specialty: string;
  status: 'active' | 'idle' | 'busy';
  framework: 'autogen' | 'crewai';
  description: string;
  capabilities: string[];
  current_patient?: string;
  response_time: number;
}

interface AgentState {
  selectedFramework: 'autogen' | 'crewai';
  activeAgents: Agent[];
  conversationMode: 'single' | 'multi';
  isLoading: boolean;
  error: string | null;
}

const initialState: AgentState = {
  selectedFramework: 'autogen',
  activeAgents: [
    {
      id: 'pcp-1',
      name: 'Primary Care Physician',
      specialty: 'Internal Medicine',
      status: 'idle',
      framework: 'autogen',
      description: 'Comprehensive primary care assessment and coordination',
      capabilities: ['Patient Assessment', 'Care Coordination', 'Risk Assessment'],
      response_time: 1.2,
    },
    {
      id: 'card-1',
      name: 'Cardiologist',
      specialty: 'Cardiology',
      status: 'idle',
      framework: 'autogen',
      description: 'Cardiovascular risk assessment and management',
      capabilities: ['Cardiac Assessment', 'Risk Stratification', 'Treatment Planning'],
      response_time: 1.5,
    },
    {
      id: 'pharm-1',
      name: 'Clinical Pharmacist',
      specialty: 'Pharmacy',
      status: 'idle',
      framework: 'autogen',
      description: 'Medication review and drug interaction analysis',
      capabilities: ['Medication Review', 'Drug Interactions', 'Dosing Optimization'],
      response_time: 0.8,
    },
    {
      id: 'nurse-1',
      name: 'Nurse Care Coordinator',
      specialty: 'Nursing',
      status: 'idle',
      framework: 'autogen',
      description: 'Care coordination and patient education',
      capabilities: ['Care Planning', 'Patient Education', 'Follow-up Coordination'],
      response_time: 1.0,
    },
  ],
  conversationMode: 'multi',
  isLoading: false,
  error: null,
};

const agentSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    setFramework: (state, action: PayloadAction<'autogen' | 'crewai'>) => {
      state.selectedFramework = action.payload;
    },
    setConversationMode: (state, action: PayloadAction<'single' | 'multi'>) => {
      state.conversationMode = action.payload;
    },
    updateAgentStatus: (state, action: PayloadAction<{ agentId: string; status: 'active' | 'idle' | 'busy'; patientId?: string }>) => {
      const agent = state.activeAgents.find(a => a.id === action.payload.agentId);
      if (agent) {
        agent.status = action.payload.status;
        agent.current_patient = action.payload.patientId;
      }
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
  setFramework,
  setConversationMode,
  updateAgentStatus,
  setLoading,
  setError,
  clearError,
} = agentSlice.actions;

export default agentSlice.reducer; 