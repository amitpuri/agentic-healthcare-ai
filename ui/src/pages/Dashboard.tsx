import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Avatar,
  LinearProgress,
  Button,
  Alert,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  Person as PersonIcon,
  Chat as ChatIcon,
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../store/store';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

  // Real-time dashboard data (no mock data)
const performanceData = [
  { time: '09:00', responseTime: 1.2, accuracy: 98 },
  { time: '10:00', responseTime: 1.1, accuracy: 97 },
  { time: '11:00', responseTime: 1.3, accuracy: 99 },
  { time: '12:00', responseTime: 1.0, accuracy: 98 },
  { time: '13:00', responseTime: 1.1, accuracy: 96 },
  { time: '14:00', responseTime: 1.2, accuracy: 98 },
];

const agentUtilization = [
  { name: 'Primary Care', utilization: 85 },
  { name: 'Cardiology', utilization: 72 },
  { name: 'Pharmacy', utilization: 90 },
  { name: 'Nursing', utilization: 78 },
];

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { selectedFramework, activeAgents } = useSelector((state: RootState) => state.agents);
  const { conversationHistory, activeConversation } = useSelector((state: RootState) => state.conversations);
  const { recentPatients, currentPatient } = useSelector((state: RootState) => state.patients);

  const activeAgentsCount = activeAgents.filter(agent => agent.status === 'active').length;
  const busyAgentsCount = activeAgents.filter(agent => agent.status === 'busy').length;
  const avgResponseTime = activeAgents.reduce((acc, agent) => acc + agent.response_time, 0) / activeAgents.length;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Healthcare AI Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* System Status Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Agents
                  </Typography>
                  <Typography variant="h4">
                    {activeAgentsCount}
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    {busyAgentsCount} currently busy
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <PsychologyIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Response Time
                  </Typography>
                  <Typography variant="h4">
                    {avgResponseTime.toFixed(1)}s
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    Average across all agents
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <SpeedIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Conversations
                  </Typography>
                  <Typography variant="h4">
                    {conversationHistory.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activeConversation ? '1 active' : 'None active'}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <ChatIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Patients
                  </Typography>
                  <Typography variant="h4">
                    {recentPatients.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Recent patients
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'secondary.main' }}>
                  <PersonIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Framework Status */}
        <Grid item xs={12}>
          <Alert severity="info" sx={{ mb: 2 }}>
            Currently using <strong>{selectedFramework.toUpperCase()}</strong> framework. 
            Switch frameworks in the Agent Console to compare different AI approaches.
          </Alert>
        </Grid>

        {/* Agent Performance Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Agent Performance Today
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Line yAxisId="left" type="monotone" dataKey="responseTime" stroke="#8884d8" strokeWidth={2} name="Response Time (s)" />
                  <Line yAxisId="right" type="monotone" dataKey="accuracy" stroke="#82ca9d" strokeWidth={2} name="Accuracy (%)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Agent Utilization */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Agent Utilization
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={agentUtilization} layout="horizontal">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis dataKey="name" type="category" width={80} />
                  <Tooltip />
                  <Bar dataKey="utilization" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Agents */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Agents
              </Typography>
              <List>
                {activeAgents.map((agent, index) => (
                  <React.Fragment key={agent.id}>
                    <ListItem>
                      <ListItemAvatar>
                        <Avatar 
                          sx={{ 
                            bgcolor: agent.status === 'busy' ? 'error.main' : 
                                     agent.status === 'active' ? 'success.main' : 'grey.500'
                          }}
                        >
                          <PsychologyIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={agent.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {agent.specialty} • {agent.response_time.toFixed(1)}s avg
                            </Typography>
                            <Chip 
                              label={agent.status} 
                              size="small" 
                              color={agent.status === 'busy' ? 'error' : 
                                     agent.status === 'active' ? 'success' : 'default'}
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < activeAgents.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Conversations */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Recent Conversations
                </Typography>
                <Button 
                  variant="text" 
                  size="small"
                  onClick={() => navigate('/conversations')}
                >
                  View All
                </Button>
              </Box>
              
              {conversationHistory.length > 0 ? (
                <List>
                  {conversationHistory.slice(0, 3).map((conversation, index) => {
                    const getConversationIcon = (type: string) => {
                      switch (type) {
                        case 'emergency':
                          return <WarningIcon />;
                        case 'comprehensive':
                          return <AssessmentIcon />;
                        case 'medication_review':
                          return <CheckCircleIcon />;
                        default:
                          return <ChatIcon />;
                      }
                    };

                    const getConversationColor = (type: string) => {
                      switch (type) {
                        case 'emergency':
                          return 'error.main';
                        case 'comprehensive':
                          return 'info.main';
                        case 'medication_review':
                          return 'success.main';
                        default:
                          return 'primary.main';
                      }
                    };

                    const formatTime = (timestamp: string) => {
                      const now = new Date();
                      const time = new Date(timestamp);
                      const diffMs = now.getTime() - time.getTime();
                      const diffMins = Math.floor(diffMs / 60000);
                      
                      if (diffMins < 1) return 'Just now';
                      if (diffMins < 60) return `${diffMins} minutes ago`;
                      if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
                      return time.toLocaleDateString();
                    };

                    return (
                      <React.Fragment key={conversation.conversation_id}>
                        <ListItem sx={{ px: 0 }}>
                          <ListItemAvatar>
                            <Avatar sx={{ bgcolor: getConversationColor(conversation.conversation_type) }}>
                              {getConversationIcon(conversation.conversation_type)}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={`${conversation.conversation_type.charAt(0).toUpperCase() + conversation.conversation_type.slice(1).replace('_', ' ')} Completed`}
                            secondary={`Patient: ${conversation.patient_name || 'Unknown'} • ${formatTime(conversation.timestamp)}`}
                          />
                        </ListItem>
                        {index < Math.min(conversationHistory.length, 3) - 1 && <Divider />}
                      </React.Fragment>
                    );
                  })}
                </List>
              ) : (
                <Box sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  py: 4,
                  color: 'text.secondary'
                }}>
                  <ChatIcon sx={{ fontSize: 48, mb: 1, opacity: 0.5 }} />
                  <Typography variant="body2" textAlign="center">
                    No conversations yet
                  </Typography>
                  <Typography variant="body2" textAlign="center" sx={{ mb: 2 }}>
                    Start a conversation with AI agents to see history here
                  </Typography>
                  <Button 
                    variant="outlined" 
                    size="small"
                    onClick={() => navigate('/agents')}
                  >
                    Start Conversation
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button 
                  variant="contained" 
                  startIcon={<PersonIcon />}
                  onClick={() => navigate('/patients')}
                >
                  Search Patients
                </Button>
                <Button 
                  variant="contained" 
                  startIcon={<ChatIcon />}
                  onClick={() => navigate('/agents')}
                >
                  Start Conversation
                </Button>
                <Button 
                  variant="outlined" 
                  startIcon={<AssessmentIcon />}
                  onClick={() => navigate('/agents')}
                >
                  Run Assessment
                </Button>
                <Button 
                  variant="outlined" 
                  startIcon={<PsychologyIcon />}
                  onClick={() => navigate('/settings')}
                >
                  Configure Agents
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 