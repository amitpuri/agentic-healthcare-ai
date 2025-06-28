import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface AgentExecution {
  id: string;
  agentId: string;
  agentName: string;
  agentSpecialty: string;
  executionType: 'assessment' | 'analysis' | 'recommendation' | 'coordination' | 'query';
  status: 'running' | 'completed' | 'failed' | 'pending';
  startTime: string;
  endTime?: string;
  duration?: number;
  patientId?: string;
  patientName?: string;
  inputData: {
    query?: string;
    patientData?: any;
    context?: string;
  };
  outputData?: {
    result?: string;
    recommendations?: string[];
    confidence?: number;
    nextSteps?: string[];
  };
  errorMessage?: string;
  framework: 'autogen' | 'crewai';
  tokens?: {
    input: number;
    output: number;
    total: number;
  };
  cost?: number;
}

export interface AgentCommunication {
  id: string;
  timestamp: string;
  fromAgentId: string;
  fromAgentName: string;
  toAgentId?: string;
  toAgentName?: string;
  communicationType: 'request' | 'response' | 'broadcast' | 'handoff' | 'collaboration';
  message: string;
  context?: string;
  patientId?: string;
  relatedExecutionId?: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'sent' | 'received' | 'processed' | 'failed';
}

interface AgentCommunicationState {
  executions: AgentExecution[];
  communications: AgentCommunication[];
  activeExecutions: string[];
  totalExecutions: number;
  isLoading: boolean;
  error: string | null;
  filters: {
    agentId?: string;
    status?: string;
    dateRange?: { start: string; end: string };
    executionType?: string;
  };
}

// Load state from localStorage
const loadStateFromStorage = (): AgentCommunicationState => {
  try {
    const serializedState = localStorage.getItem('agentCommunicationState');
    if (serializedState === null) {
      return getDefaultState();
    }
    const parsed = JSON.parse(serializedState);
    return {
      ...getDefaultState(),
      ...parsed,
      // Always start with fresh loading states
      isLoading: false,
      error: null
    };
  } catch (err) {
    console.warn('Failed to load agent communication state from localStorage:', err);
    return getDefaultState();
  }
};

const getDefaultState = (): AgentCommunicationState => ({
  executions: [
    {
      id: 'exec-001',
      agentId: 'pcp-1',
      agentName: 'Primary Care Physician',
      agentSpecialty: 'Internal Medicine',
      executionType: 'assessment',
      status: 'completed',
      startTime: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
      endTime: new Date(Date.now() - 3 * 60 * 1000).toISOString(),
      duration: 120, // seconds
      patientId: '597173',
      patientName: 'John Doe',
      inputData: {
        query: 'Comprehensive health assessment for new patient',
        context: 'Initial consultation'
      },
      outputData: {
        result: 'Patient assessment completed successfully',
        recommendations: [
          'Schedule follow-up cardiology consultation',
          'Monitor blood pressure regularly',
          'Consider medication adjustment'
        ],
        confidence: 0.92,
        nextSteps: ['Schedule cardiology referral', 'Lab work in 2 weeks']
      },
      framework: 'autogen',
      tokens: { input: 450, output: 320, total: 770 },
      cost: 0.023
    },
    {
      id: 'exec-002',
      agentId: 'card-1',
      agentName: 'Cardiologist',
      agentSpecialty: 'Cardiology',
      executionType: 'analysis',
      status: 'completed',
      startTime: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
      endTime: new Date(Date.now() - 12 * 60 * 1000).toISOString(),
      duration: 180,
      patientId: '597173',
      patientName: 'John Doe',
      inputData: {
        query: 'Cardiac risk assessment based on recent ECG and lab results',
        context: 'Referral from primary care'
      },
      outputData: {
        result: 'Moderate cardiac risk identified',
        recommendations: [
          'Start ACE inhibitor therapy',
          'Cardiac stress test within 30 days',
          'Lifestyle modifications counseling'
        ],
        confidence: 0.87
      },
      framework: 'autogen',
      tokens: { input: 380, output: 290, total: 670 },
      cost: 0.019
    },
    {
      id: 'exec-003',
      agentId: 'pharm-1',
      agentName: 'Clinical Pharmacist',
      agentSpecialty: 'Pharmacy',
      executionType: 'analysis',
      status: 'running',
      startTime: new Date(Date.now() - 2 * 60 * 1000).toISOString(), // 2 minutes ago
      patientId: '597173',
      patientName: 'John Doe',
      inputData: {
        query: 'Drug interaction analysis for new medication regimen',
        context: 'Following cardiologist recommendations'
      },
      framework: 'autogen'
    }
  ],
  communications: [
    {
      id: 'comm-001',
      timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString(),
      fromAgentId: 'pcp-1',
      fromAgentName: 'Primary Care Physician',
      toAgentId: 'card-1',
      toAgentName: 'Cardiologist',
      communicationType: 'request',
      message: 'Requesting cardiac consultation for patient with elevated BP and family history of CAD',
      context: 'Patient ID 597173 - Initial assessment complete',
      patientId: '597173',
      relatedExecutionId: 'exec-001',
      priority: 'medium',
      status: 'processed'
    },
    {
      id: 'comm-002',
      timestamp: new Date(Date.now() - 8 * 60 * 1000).toISOString(),
      fromAgentId: 'card-1',
      fromAgentName: 'Cardiologist',
      toAgentId: 'pcp-1',
      toAgentName: 'Primary Care Physician',
      communicationType: 'response',
      message: 'Cardiac assessment complete. Moderate risk identified. Recommending ACE inhibitor and stress test.',
      context: 'Response to consultation request',
      patientId: '597173',
      relatedExecutionId: 'exec-002',
      priority: 'medium',
      status: 'received'
    },
    {
      id: 'comm-003',
      timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
      fromAgentId: 'card-1',
      fromAgentName: 'Cardiologist',
      toAgentId: 'pharm-1',
      toAgentName: 'Clinical Pharmacist',
      communicationType: 'handoff',
      message: 'Please review medication regimen for drug interactions with new ACE inhibitor therapy',
      context: 'Medication safety review required',
      patientId: '597173',
      priority: 'high',
      status: 'sent'
    }
  ],
  activeExecutions: ['exec-003'],
  totalExecutions: 3,
  isLoading: false,
  error: null,
  filters: {}
});

const initialState: AgentCommunicationState = loadStateFromStorage();

// Save state to localStorage
const saveStateToStorage = (state: AgentCommunicationState) => {
  try {
    const serializedState = JSON.stringify({
      executions: state.executions,
      communications: state.communications,
      totalExecutions: state.totalExecutions,
      filters: state.filters
    });
    localStorage.setItem('agentCommunicationState', serializedState);
  } catch (err) {
    console.warn('Failed to save agent communication state to localStorage:', err);
  }
};

const agentCommunicationSlice = createSlice({
  name: 'agentCommunication',
  initialState,
  reducers: {
    addExecution: (state, action: PayloadAction<Omit<AgentExecution, 'id'>>) => {
      const execution: AgentExecution = {
        ...action.payload,
        id: `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };
      state.executions.unshift(execution);
      if (execution.status === 'running' || execution.status === 'pending') {
        state.activeExecutions.push(execution.id);
      }
      state.totalExecutions += 1;
      saveStateToStorage(state);
    },
    
    updateExecution: (state, action: PayloadAction<{ id: string; updates: Partial<AgentExecution> }>) => {
      const index = state.executions.findIndex(exec => exec.id === action.payload.id);
      if (index !== -1) {
        state.executions[index] = { ...state.executions[index], ...action.payload.updates };
        
        // Update active executions list
        if (action.payload.updates.status === 'completed' || action.payload.updates.status === 'failed') {
          state.activeExecutions = state.activeExecutions.filter(id => id !== action.payload.id);
        }
        saveStateToStorage(state);
      }
    },
    
    addCommunication: (state, action: PayloadAction<Omit<AgentCommunication, 'id'>>) => {
      const communication: AgentCommunication = {
        ...action.payload,
        id: `comm-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      };
      state.communications.unshift(communication);
      saveStateToStorage(state);
    },
    
    updateCommunication: (state, action: PayloadAction<{ id: string; updates: Partial<AgentCommunication> }>) => {
      const index = state.communications.findIndex(comm => comm.id === action.payload.id);
      if (index !== -1) {
        state.communications[index] = { ...state.communications[index], ...action.payload.updates };
      }
    },
    
    setFilters: (state, action: PayloadAction<AgentCommunicationState['filters']>) => {
      state.filters = action.payload;
    },
    
    clearFilters: (state) => {
      state.filters = {};
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
    
    clearHistory: (state) => {
      state.executions = [];
      state.communications = [];
      state.activeExecutions = [];
      state.totalExecutions = 0;
    }
  },
});

export const {
  addExecution,
  updateExecution,
  addCommunication,
  updateCommunication,
  setFilters,
  clearFilters,
  setLoading,
  setError,
  clearError,
  clearHistory
} = agentCommunicationSlice.actions;

export default agentCommunicationSlice.reducer; 