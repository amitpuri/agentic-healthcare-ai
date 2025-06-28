import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ConversationMessage {
  id: string;
  speaker: string;
  role: 'user' | 'assistant' | 'agent';
  content: string;
  timestamp: string;
  metadata?: any;
}

export interface Conversation {
  conversation_id: string;
  patient_id: string;
  patient_name?: string;
  conversation_type: 'comprehensive' | 'emergency' | 'medication_review';
  status: 'active' | 'completed' | 'paused';
  participants: string[];
  messages: ConversationMessage[];
  summary?: any;
  timestamp: string;
  framework: 'autogen' | 'crewai';
  pdfReports?: PDFReportInfo[];
}

export interface PDFReportInfo {
  filename: string;
  pdfUrl: string;
  generatedAt: string;
  assessmentType: string;
  patientName: string;
  size?: number;
}

interface ConversationState {
  activeConversation: Conversation | null;
  conversationHistory: Conversation[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  typingIndicator: string | null;
}

// Helper functions for localStorage persistence
const loadConversationHistoryFromStorage = (): Conversation[] => {
  try {
    const stored = localStorage.getItem('healthcare-ai-conversation-history');
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Failed to load conversation history from localStorage:', error);
    return [];
  }
};

const saveConversationHistoryToStorage = (history: Conversation[]) => {
  try {
    localStorage.setItem('healthcare-ai-conversation-history', JSON.stringify(history));
  } catch (error) {
    console.error('Failed to save conversation history to localStorage:', error);
  }
};

const initialState: ConversationState = {
  activeConversation: null,
  conversationHistory: loadConversationHistoryFromStorage(),
  isConnected: false,
  isLoading: false,
  error: null,
  typingIndicator: null,
};

const conversationSlice = createSlice({
  name: 'conversations',
  initialState,
  reducers: {
    startConversation: (state, action: PayloadAction<Conversation>) => {
      state.activeConversation = action.payload;
      state.error = null;
    },
    addMessage: (state, action: PayloadAction<ConversationMessage>) => {
      if (state.activeConversation) {
        state.activeConversation.messages.push(action.payload);
      }
    },
    updateConversationStatus: (state, action: PayloadAction<{ status: 'active' | 'completed' | 'paused'; summary?: any }>) => {
      if (state.activeConversation) {
        state.activeConversation.status = action.payload.status;
        if (action.payload.summary) {
          state.activeConversation.summary = action.payload.summary;
        }
        if (action.payload.status === 'completed') {
          // Add to history
          state.conversationHistory.push({ ...state.activeConversation });
          saveConversationHistoryToStorage(state.conversationHistory);
          state.activeConversation = null;
        }
      }
    },
    endConversation: (state) => {
      if (state.activeConversation) {
        state.activeConversation.status = 'completed';
        state.conversationHistory.push({ ...state.activeConversation });
        saveConversationHistoryToStorage(state.conversationHistory);
        state.activeConversation = null;
      }
    },
    setConversationHistory: (state, action: PayloadAction<Conversation[]>) => {
      state.conversationHistory = action.payload;
      saveConversationHistoryToStorage(state.conversationHistory);
    },
    setConnected: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
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
    setTypingIndicator: (state, action: PayloadAction<string | null>) => {
      state.typingIndicator = action.payload;
    },
    clearActiveConversation: (state) => {
      state.activeConversation = null;
    },
    addPDFReport: (state, action: PayloadAction<PDFReportInfo>) => {
      if (state.activeConversation) {
        if (!state.activeConversation.pdfReports) {
          state.activeConversation.pdfReports = [];
        }
        state.activeConversation.pdfReports.push(action.payload);
      }
    },
    updateConversationPDFReports: (state, action: PayloadAction<{ conversationId: string; pdfReports: PDFReportInfo[] }>) => {
      const conversation = state.conversationHistory.find(c => c.conversation_id === action.payload.conversationId);
      if (conversation) {
        conversation.pdfReports = action.payload.pdfReports;
        saveConversationHistoryToStorage(state.conversationHistory);
      }
    },
  },
});

export const {
  startConversation,
  addMessage,
  updateConversationStatus,
  endConversation,
  setConversationHistory,
  setConnected,
  setLoading,
  setError,
  clearError,
  setTypingIndicator,
  clearActiveConversation,
  addPDFReport,
  updateConversationPDFReports,
} = conversationSlice.actions;

export default conversationSlice.reducer; 