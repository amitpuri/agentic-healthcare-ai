import React, { useState, useEffect, useRef } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  Chip,
  Avatar,
  Paper,
  Divider,
  IconButton,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Tab,
  Tabs,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as SmartToyIcon,
  Person as PersonIcon,
  LocalHospital as LocalHospitalIcon,
  Medication as MedicationIcon,
  Psychology as PsychologyIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  LocalHospital as EmergencyIcon,
  Timeline as TimelineIcon,
  Code as CodeIcon,
  Speed as SpeedIcon,
  AttachMoney as AttachMoneyIcon,
  Token as TokenIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  CloudUpload as CloudUploadIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { setFramework, setConversationMode, updateAgentStatus } from '../store/slices/agentSlice';
import { clearCurrentPatient, setCurrentPatient } from '../store/slices/patientSlice';
import { useNavigate } from 'react-router-dom';
import { addExecution, updateExecution, addCommunication } from '../store/slices/agentCommunicationSlice';
import { 
  realAgentService, 
  RealAgentConfig, 
  ScenarioConfig, 
  ScenarioExecution, 
  AgentResponse,
  LLMCommunication 
} from '../services/realAgentService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const RealAgentConsole: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { selectedFramework, activeAgents } = useSelector((state: RootState) => state.agents);
  const { currentPatient } = useSelector((state: RootState) => state.patients);

  // State for real agent execution
  const [activeScenario, setActiveScenario] = useState<ScenarioExecution | null>(null);
  const [scenarioType, setScenarioType] = useState<'comprehensive' | 'emergency' | 'medication_review'>('comprehensive');
  const [isExecuting, setIsExecuting] = useState(false);
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [urgencyLevel, setUrgencyLevel] = useState('routine');
  const [modelName, setModelName] = useState('gpt-4');
  const [temperature, setTemperature] = useState(0.1);
  
  // Communication tracking
  const [communications, setCommunications] = useState<LLMCommunication[]>([]);
  const [communicationStats, setCommunicationStats] = useState<any>({});
  const [selectedCommunication, setSelectedCommunication] = useState<LLMCommunication | null>(null);
  const [communicationDetailOpen, setCommunicationDetailOpen] = useState(false);
  
  // UI state
  const [tabValue, setTabValue] = useState(0);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load communications on mount
    loadCommunications();
    loadCommunicationStats();
    
    // Set up polling for active scenarios
    const interval = setInterval(() => {
      if (activeScenario?.status === 'running') {
        refreshScenarioStatus();
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [activeScenario]);

  const loadCommunications = async () => {
    try {
      const comms = await realAgentService.getCommunications();
      setCommunications(comms);
    } catch (err) {
      console.error('Failed to load communications:', err);
    }
  };

  const loadCommunicationStats = async () => {
    try {
      const stats = await realAgentService.getCommunicationStats();
      setCommunicationStats(stats);
    } catch (err) {
      console.error('Failed to load communication stats:', err);
    }
  };

  const refreshScenarioStatus = async () => {
    if (!activeScenario) return;
    
    try {
      const updated = await realAgentService.getScenario(activeScenario.id);
      if (updated) {
        setActiveScenario(updated);
        
        // Update Redux store with execution data
        updated.agents.forEach(agent => {
          if (agent.status === 'completed' && agent.output) {
            const execution = realAgentService.convertToAgentExecution(agent, updated);
            dispatch(addExecution(execution));
          }
        });
        
        // Update Redux store with communications
        updated.communications.forEach(comm => {
          const communication = realAgentService.convertToAgentCommunication(comm, updated);
          dispatch(addCommunication(communication));
        });
        
        if (updated.status !== 'running') {
          setIsExecuting(false);
          loadCommunications();
          loadCommunicationStats();
        }
      }
    } catch (err) {
      console.error('Failed to refresh scenario status:', err);
    }
  };

  const handleStartScenario = async () => {
    if (!currentPatient) {
      setError('Please select a patient first');
      return;
    }

    setIsExecuting(true);
    setError(null);

    try {
      // Update agent service configuration
      await realAgentService.updateConfig({
        framework: selectedFramework,
        modelName,
        temperature
      });

      // Create scenario configuration
      const scenarioConfig: ScenarioConfig = {
        type: scenarioType,
        patientId: currentPatient.patient_id,
        patientName: currentPatient.name,
        chiefComplaint: chiefComplaint || undefined,
        urgencyLevel: urgencyLevel as any,
        additionalContext: `${selectedFramework} framework execution`
      };

      // Start scenario execution
      const scenario = await realAgentService.startScenario(scenarioConfig);
      setActiveScenario(scenario);

      // Update agent statuses
      scenario.agents.forEach(agent => {
        dispatch(updateAgentStatus({ 
          agentId: agent.agentId, 
          status: 'busy',
          patientId: currentPatient.patient_id 
        }));
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start scenario');
      setIsExecuting(false);
      // Refresh communications to show the failed attempt
      loadCommunications();
      loadCommunicationStats();
    }
  };

  const handleStopScenario = () => {
    setIsExecuting(false);
    setActiveScenario(null);
    
    // Reset agent statuses
    activeAgents.forEach(agent => {
      dispatch(updateAgentStatus({ agentId: agent.id, status: 'idle' }));
    });
  };

  const handleConfigSave = () => {
    setConfigDialogOpen(false);
    setError(null);
  };

  const handleCommunicationClick = (communication: LLMCommunication) => {
    setSelectedCommunication(communication);
    setCommunicationDetailOpen(true);
  };

  const getScenarioTypeInfo = (type: string) => {
    switch (type) {
      case 'comprehensive':
        return {
          icon: <LocalHospitalIcon />,
          color: 'primary',
          description: 'Complete patient assessment with multi-agent collaboration'
        };
      case 'emergency':
        return {
          icon: <EmergencyIcon />,
          color: 'error',
          description: 'Rapid emergency assessment and triage'
        };
      case 'medication_review':
        return {
          icon: <MedicationIcon />,
          color: 'info',
          description: 'Comprehensive medication review and optimization'
        };
      default:
        return {
          icon: <LocalHospitalIcon />,
          color: 'primary',
          description: 'Standard assessment'
        };
    }
  };

  const formatCost = (cost: number) => `$${cost.toFixed(4)}`;
  const formatTokens = (tokens: number) => tokens.toLocaleString();
  const formatDuration = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <PsychologyIcon />
        Real AI Agent Console
        <Chip 
          label={selectedFramework.toUpperCase()} 
          color={selectedFramework === 'autogen' ? 'primary' : 'secondary'}
          size="small"
        />
      </Typography>

      {/* Patient Information Banner */}
      {currentPatient ? (
        <Alert 
          severity="success" 
          sx={{ mb: 3 }}
          icon={<PersonIcon />}
          action={
            <Button 
              color="inherit" 
              size="small"
              onClick={() => dispatch(clearCurrentPatient())}
            >
              Clear Patient
            </Button>
          }
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                Selected Patient: {currentPatient.name}
              </Typography>
              <Typography variant="body2">
                ID: {currentPatient.patient_id} • Age: {currentPatient.age} • Gender: {currentPatient.gender}
              </Typography>
            </Box>
          </Box>
        </Alert>
      ) : (
        <Alert 
          severity="warning" 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small"
              onClick={() => navigate('/patients')}
              variant="outlined"
            >
              Select Patient
            </Button>
          }
        >
          <Typography variant="subtitle1" fontWeight="bold">
            No Patient Selected
          </Typography>
          <Typography variant="body2">
            Please select a patient to begin real AI agent execution.
          </Typography>
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Control Panel */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Framework Configuration
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip
                  label="AutoGen"
                  clickable
                  color={selectedFramework === 'autogen' ? 'primary' : 'default'}
                  onClick={() => dispatch(setFramework('autogen'))}
                  icon={<CodeIcon />}
                />
                <Chip
                  label="CrewAI"
                  clickable
                  color={selectedFramework === 'crewai' ? 'secondary' : 'default'}
                  onClick={() => dispatch(setFramework('crewai'))}
                  icon={<PsychologyIcon />}
                />
              </Box>
              
              <Button
                startIcon={<SettingsIcon />}
                onClick={() => setConfigDialogOpen(true)}
                size="small"
                variant="outlined"
                fullWidth
              >
                Configure API Settings
              </Button>
            </CardContent>
          </Card>

          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scenario Configuration
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Scenario Type</InputLabel>
                <Select
                  value={scenarioType}
                  label="Scenario Type"
                  onChange={(e) => setScenarioType(e.target.value as any)}
                  disabled={isExecuting}
                >
                  <MenuItem value="comprehensive">Comprehensive Assessment</MenuItem>
                  <MenuItem value="emergency">Emergency Assessment</MenuItem>
                  <MenuItem value="medication_review">Medication Review</MenuItem>
                </Select>
              </FormControl>

              {scenarioType === 'emergency' && (
                <TextField
                  fullWidth
                  label="Chief Complaint"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  placeholder="e.g., Chest pain with shortness of breath"
                  sx={{ mb: 2 }}
                  disabled={isExecuting}
                />
              )}

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Urgency Level</InputLabel>
                <Select
                  value={urgencyLevel}
                  label="Urgency Level"
                  onChange={(e) => setUrgencyLevel(e.target.value)}
                  disabled={isExecuting}
                >
                  <MenuItem value="routine">Routine</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                  <MenuItem value="emergent">Emergent</MenuItem>
                  <MenuItem value="stat">STAT</MenuItem>
                </Select>
              </FormControl>

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={isExecuting ? <CircularProgress size={16} /> : <PlayArrowIcon />}
                  onClick={handleStartScenario}
                  disabled={!currentPatient || isExecuting}
                  fullWidth
                >
                  {isExecuting ? 'EXECUTING...' : 'START REAL EXECUTION'}
                </Button>
                {isExecuting && (
                  <Button
                    variant="outlined"
                    startIcon={<StopIcon />}
                    onClick={handleStopScenario}
                    color="error"
                  >
                    Stop
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Active Agents */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Active Agents
              </Typography>
              <List dense>
                {activeAgents.map((agent) => (
                  <ListItem key={agent.id}>
                    <ListItemAvatar>
                      <Avatar
                        sx={{
                          bgcolor: agent.status === 'busy' ? 'error.main' :
                                   agent.status === 'active' ? 'success.main' : 'grey.500',
                          width: 32,
                          height: 32,
                        }}
                      >
                        <SmartToyIcon fontSize="small" />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={agent.name}
                      secondary={`${agent.specialty} • ${agent.status}`}
                      primaryTypographyProps={{ variant: 'body2' }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
              
              <Divider sx={{ my: 2 }} />
              
              <Button
                fullWidth
                variant="outlined"
                startIcon={<TimelineIcon />}
                onClick={() => navigate('/agent-communications')}
                size="small"
              >
                View Communication History
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Main Content Area */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '75vh', display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
                <Tab label="Scenario Execution" />
                <Tab label="LLM Communications" />
                <Tab label="Performance Metrics" />
              </Tabs>
            </Box>

            <TabPanel value={tabValue} index={0}>
              {/* Scenario Execution View */}
              {activeScenario ? (
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      {activeScenario.scenarioType.replace('_', ' ').toUpperCase()} Execution
                    </Typography>
                    <Chip 
                      label={activeScenario.status.toUpperCase()}
                      color={activeScenario.status === 'running' ? 'warning' : 
                             activeScenario.status === 'completed' ? 'success' : 'error'}
                    />
                  </Box>

                  {activeScenario.status === 'running' && (
                    <LinearProgress sx={{ mb: 2 }} />
                  )}

                  {activeScenario.agents.map((agent) => (
                    <Accordion key={agent.agentId} sx={{ mb: 1 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                          <Avatar sx={{ bgcolor: 'primary.main' }}>
                            <SmartToyIcon />
                          </Avatar>
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography variant="subtitle1">{agent.agentName}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {agent.specialty}
                            </Typography>
                          </Box>
                          <Chip
                            label={agent.status.toUpperCase()}
                            color={agent.status === 'running' ? 'warning' : 
                                   agent.status === 'completed' ? 'success' : 
                                   agent.status === 'failed' ? 'error' : 'default'}
                            size="small"
                          />
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Input:</strong> {agent.input}
                        </Typography>
                        {agent.output && (
                          <Typography variant="body2" sx={{ mb: 1 }}>
                            <strong>Output:</strong> {agent.output}
                          </Typography>
                        )}
                        {agent.recommendations && agent.recommendations.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" gutterBottom>Recommendations:</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {agent.recommendations.map((rec, idx) => (
                                <Chip key={idx} label={rec} size="small" variant="outlined" />
                              ))}
                            </Box>
                          </Box>
                        )}
                        {agent.communicationIds.length > 0 && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            LLM Communications: {agent.communicationIds.length}
                          </Typography>
                        )}
                      </AccordionDetails>
                    </Accordion>
                  ))}

                  {activeScenario.summary && (
                    <Paper sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                      <Typography variant="subtitle2" gutterBottom>Scenario Summary</Typography>
                      <Typography variant="body2">{activeScenario.summary}</Typography>
                    </Paper>
                  )}
                </Box>
              ) : (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  height: '100%',
                  color: 'text.secondary' 
                }}>
                  <CloudUploadIcon sx={{ fontSize: 64, mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No Active Scenario
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    Configure your scenario and start execution to see real agent interactions
                  </Typography>
                </Box>
              )}
            </TabPanel>

            <TabPanel value={tabValue} index={1}>
              {/* LLM Communications View */}
              <Box sx={{ height: '100%', overflow: 'auto' }}>
                {communications.length > 0 ? (
                  communications.map((comm) => (
                    <Card key={comm.id} sx={{ mb: 2 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="h6">{comm.agentName}</Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip label={comm.framework.toUpperCase()} size="small" />
                            <Chip label={comm.model} size="small" variant="outlined" />
                          </Box>
                        </Box>
                        
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {comm.finalResponse || 'Communication in progress...'}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                          <Chip 
                            icon={<TokenIcon />}
                            label={`${formatTokens(comm.totalTokens)} tokens`}
                            size="small"
                          />
                          <Chip 
                            icon={<AttachMoneyIcon />}
                            label={formatCost(comm.costEstimate)}
                            size="small"
                            color="success"
                          />
                          <Chip 
                            icon={<SpeedIcon />}
                            label={formatDuration(comm.responseTimeMs)}
                            size="small"
                            color="info"
                          />
                        </Box>
                        
                        <Button
                          startIcon={<VisibilityIcon />}
                          onClick={() => handleCommunicationClick(comm)}
                          size="small"
                          sx={{ mt: 1 }}
                        >
                          View Details
                        </Button>
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <Box sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    height: '100%',
                    color: 'text.secondary' 
                  }}>
                    <CodeIcon sx={{ fontSize: 64, mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      No LLM Communications
                    </Typography>
                    <Typography variant="body2" textAlign="center">
                      Start a scenario to see real-time LLM interactions
                    </Typography>
                  </Box>
                )}
              </Box>
            </TabPanel>

            <TabPanel value={tabValue} index={2}>
              {/* Performance Metrics View */}
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4">{communicationStats.total || 0}</Typography>
                      <Typography variant="body2" color="text.secondary">Total Communications</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4">{formatTokens(communicationStats.total_tokens || 0)}</Typography>
                      <Typography variant="body2" color="text.secondary">Total Tokens</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4">{formatCost(communicationStats.total_cost || 0)}</Typography>
                      <Typography variant="body2" color="text.secondary">Total Cost</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography variant="h4">{communicationStats.average_response_time_ms || 0}ms</Typography>
                      <Typography variant="body2" color="text.secondary">Avg Response Time</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {communicationStats.by_framework && (
                <Card sx={{ mt: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Performance by Framework</Typography>
                    {Object.entries(communicationStats.by_framework).map(([framework, stats]: [string, any]) => (
                      <Box key={framework} sx={{ mb: 2 }}>
                        <Typography variant="subtitle1">{framework.toUpperCase()}</Typography>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                          <Chip label={`${stats.count} communications`} size="small" />
                          <Chip label={`${formatTokens(stats.tokens)} tokens`} size="small" />
                          <Chip label={formatCost(stats.cost)} size="small" />
                        </Box>
                      </Box>
                    ))}
                  </CardContent>
                </Card>
              )}
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      {/* Configuration Dialog */}
      <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>API Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Model Name"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            sx={{ mb: 2 }}
            helperText="e.g., gpt-4, gpt-3.5-turbo"
          />
          <TextField
            fullWidth
            label="Temperature"
            type="number"
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            inputProps={{ min: 0, max: 1, step: 0.1 }}
            helperText="Model temperature (0-1)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleConfigSave} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Communication Detail Dialog */}
      <Dialog 
        open={communicationDetailOpen} 
        onClose={() => setCommunicationDetailOpen(false)} 
        maxWidth="lg" 
        fullWidth
      >
        <DialogTitle>
          LLM Communication Details: {selectedCommunication?.agentName}
        </DialogTitle>
        <DialogContent>
          {selectedCommunication ? (
            <Box>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Framework</Typography>
                  <Typography>{selectedCommunication.framework}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Model</Typography>
                  <Typography>{selectedCommunication.model}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Total Tokens</Typography>
                  <Typography>{formatTokens(selectedCommunication.totalTokens)}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2">Cost Estimate</Typography>
                  <Typography>{formatCost(selectedCommunication.costEstimate)}</Typography>
                </Grid>
              </Grid>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>Messages</Typography>
              <Paper variant="outlined" sx={{ p: 2, maxHeight: '400px', overflowY: 'auto' }}>
                {selectedCommunication.messages?.map((msg, index) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    <Chip 
                      avatar={<Avatar>{msg.role.charAt(0).toUpperCase()}</Avatar>} 
                      label={msg.role} 
                      size="small" 
                      color={msg.role === 'user' ? 'primary' : 'secondary'}
                      sx={{ mb: 1 }}
                    />
                    <Typography 
                      variant="body2" 
                      sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', p: 1, bgcolor: 'grey.100', borderRadius: 1 }}
                    >
                      {msg.content}
                    </Typography>
                  </Box>
                ))}
              </Paper>
            </Box>
          ) : (
            <Typography>No communication selected.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommunicationDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RealAgentConsole; 