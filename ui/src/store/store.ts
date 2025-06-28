import { configureStore } from '@reduxjs/toolkit';
import { apiSlice } from './api/apiSlice';
import agentReducer from './slices/agentSlice';
import patientReducer from './slices/patientSlice';
import conversationReducer from './slices/conversationSlice';
import agentCommunicationReducer from './slices/agentCommunicationSlice';

export const store = configureStore({
  reducer: {
    api: apiSlice.reducer,
    agents: agentReducer,
    patients: patientReducer,
    conversations: conversationReducer,
    agentCommunication: agentCommunicationReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 