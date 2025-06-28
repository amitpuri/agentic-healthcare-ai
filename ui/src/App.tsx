import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './pages/Dashboard';
import PatientSearch from './pages/PatientSearch';
import AgentConsole from './pages/AgentConsole';
import RealAgentConsole from './pages/RealAgentConsole';
import ConversationHistory from './pages/ConversationHistory';
import AgentCommunicationHistory from './pages/AgentCommunicationHistory';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Header />
      <Sidebar />
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          mt: 8, // Account for header height
          ml: { sm: 30 }, // Account for sidebar width
          backgroundColor: 'background.default',
        }}
      >
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/patients" element={<PatientSearch />} />
          <Route path="/agents" element={<AgentConsole />} />
          <Route path="/real-agents" element={<RealAgentConsole />} />
          <Route path="/conversations" element={<ConversationHistory />} />
          <Route path="/agent-communications" element={<AgentCommunicationHistory />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Box>
    </Box>
  );
};

export default App; 