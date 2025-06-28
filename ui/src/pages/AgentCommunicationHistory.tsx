import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Tab,
  Tabs,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  LinearProgress,
  Avatar,
  Badge,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayArrowIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  Refresh as RefreshIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  Timeline as TimelineIcon,
  Psychology as PsychologyIcon,
  Message as MessageIcon,
  TrendingUp as TrendingUpIcon,
  AccessTime as AccessTimeIcon,
  AttachMoney as AttachMoneyIcon,
  Person as PersonIcon,
  Launch as LaunchIcon,
} from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store/store';
import { AgentExecution, AgentCommunication } from '../store/slices/agentCommunicationSlice';

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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const AgentCommunicationHistory: React.FC = () => {
  const dispatch = useDispatch();
  const { executions, communications, activeExecutions, totalExecutions } = useSelector(
    (state: RootState) => state.agentCommunication
  );

  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [agentFilter, setAgentFilter] = useState('all');
  const [selectedExecution, setSelectedExecution] = useState<AgentExecution | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  // Filter executions based on search and filters
  const filteredExecutions = useMemo(() => {
    return executions.filter(execution => {
      const matchesSearch = searchTerm === '' || 
        execution.agentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        execution.inputData.query?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        execution.patientName?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || execution.status === statusFilter;
      const matchesAgent = agentFilter === 'all' || execution.agentId === agentFilter;
      
      return matchesSearch && matchesStatus && matchesAgent;
    });
  }, [executions, searchTerm, statusFilter, agentFilter]);

  // Filter communications
  const filteredCommunications = useMemo(() => {
    return communications.filter(comm => {
      const matchesSearch = searchTerm === '' || 
        comm.fromAgentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comm.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comm.toAgentName?.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesSearch;
    });
  }, [communications, searchTerm]);

  // Get unique agents for filter dropdown
  const uniqueAgents = useMemo(() => {
    const agents = new Set(executions.map(exec => ({ id: exec.agentId, name: exec.agentName })));
    return Array.from(agents);
  }, [executions]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'pending':
        return <ScheduleIcon color="warning" />;
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <ScheduleIcon />;
    }
  };

  const getStatusColor = (status: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (status) {
      case 'running':
      case 'pending':
        return 'warning';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string): "default" | "primary" | "secondary" | "error" | "info" | "success" | "warning" => {
    switch (priority) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const handleExecutionClick = (execution: AgentExecution) => {
    setSelectedExecution(execution);
    setDetailDialogOpen(true);
  };

  // Statistics
  const completedExecutions = executions.filter(e => e.status === 'completed').length;
  const failedExecutions = executions.filter(e => e.status === 'failed').length;
  const avgDuration = executions
    .filter(e => e.duration)
    .reduce((sum, e) => sum + (e.duration || 0), 0) / Math.max(1, executions.filter(e => e.duration).length);
  const totalCost = executions.reduce((sum, e) => sum + (e.cost || 0), 0);

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TimelineIcon />
        Agent Communication History
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6">{totalExecutions}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Executions</Typography>
                </Box>
                <TrendingUpIcon color="primary" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6">{activeExecutions.length}</Typography>
                  <Typography variant="body2" color="text.secondary">Active Executions</Typography>
                </Box>
                <Badge badgeContent={activeExecutions.length} color="warning">
                  <PlayArrowIcon color="warning" />
                </Badge>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6">{formatDuration(Math.round(avgDuration))}</Typography>
                  <Typography variant="body2" color="text.secondary">Avg Duration</Typography>
                </Box>
                <AccessTimeIcon color="info" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h6">${totalCost.toFixed(3)}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Cost</Typography>
                </Box>
                <AttachMoneyIcon color="success" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search executions, agents, or patients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ minWidth: 300 }}
          />
          
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="running">Running</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Agent</InputLabel>
            <Select
              value={agentFilter}
              label="Agent"
              onChange={(e) => setAgentFilter(e.target.value)}
            >
              <MenuItem value="all">All Agents</MenuItem>
              {uniqueAgents.map((agent) => (
                <MenuItem key={agent.id} value={agent.id}>{agent.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <IconButton onClick={() => {
            setSearchTerm('');
            setStatusFilter('all');
            setAgentFilter('all');
          }}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label={`Executions (${filteredExecutions.length})`} />
          <Tab label={`Communications (${filteredCommunications.length})`} />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          {/* Executions List */}
          {filteredExecutions.map((execution) => (
            <Accordion key={execution.id} sx={{ mb: 1 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                  <Avatar sx={{ bgcolor: 'primary.main' }}>
                    <PsychologyIcon />
                  </Avatar>
                  
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">{execution.agentName}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {execution.inputData.query}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip
                      icon={getStatusIcon(execution.status)}
                      label={execution.status.toUpperCase()}
                      color={getStatusColor(execution.status)}
                      size="small"
                    />
                    {execution.patientName && (
                      <Chip
                        icon={<PersonIcon />}
                        label={execution.patientName}
                        size="small"
                        variant="outlined"
                      />
                    )}
                    <Typography variant="caption" color="text.secondary">
                      {formatTimestamp(execution.startTime)}
                    </Typography>
                  </Box>
                </Box>
              </AccordionSummary>
              
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>Execution Details</Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText
                          primary="Type"
                          secondary={execution.executionType}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Framework"
                          secondary={execution.framework.toUpperCase()}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Duration"
                          secondary={formatDuration(execution.duration)}
                        />
                      </ListItem>
                      {execution.cost && (
                        <ListItem>
                          <ListItemText
                            primary="Cost"
                            secondary={`$${execution.cost.toFixed(4)}`}
                          />
                        </ListItem>
                      )}
                    </List>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>Input Data</Typography>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {execution.inputData.query}
                    </Typography>
                    {execution.inputData.context && (
                      <Typography variant="caption" color="text.secondary">
                        Context: {execution.inputData.context}
                      </Typography>
                    )}
                  </Grid>
                  
                  {execution.outputData && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>Output & Recommendations</Typography>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        {execution.outputData.result}
                      </Typography>
                      {execution.outputData.recommendations && execution.outputData.recommendations.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="subtitle2" gutterBottom>Recommendations:</Typography>
                          {execution.outputData.recommendations.map((rec, index) => (
                            <Chip key={index} label={rec} size="small" sx={{ mr: 1, mb: 1 }} />
                          ))}
                        </Box>
                      )}
                      {execution.outputData.confidence && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption">
                            Confidence: {(execution.outputData.confidence * 100).toFixed(1)}%
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={execution.outputData.confidence * 100}
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      )}
                    </Grid>
                  )}
                  
                  <Grid item xs={12}>
                    <Button
                      startIcon={<LaunchIcon />}
                      onClick={() => handleExecutionClick(execution)}
                      size="small"
                    >
                      View Full Details
                    </Button>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
          
          {filteredExecutions.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary">
                No executions found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your search criteria or filters
              </Typography>
            </Box>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {/* Communications List */}
          {filteredCommunications.map((communication) => (
            <Card key={communication.id} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <MessageIcon color="primary" />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">
                      {communication.fromAgentName}
                      {communication.toAgentName && ` → ${communication.toAgentName}`}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatTimestamp(communication.timestamp)}
                    </Typography>
                  </Box>
                  <Chip
                    label={communication.communicationType.toUpperCase()}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    label={communication.priority.toUpperCase()}
                    color={getPriorityColor(communication.priority)}
                    size="small"
                  />
                </Box>
                
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {communication.message}
                </Typography>
                
                {communication.context && (
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    {communication.context}
                  </Typography>
                )}
                
                {communication.patientId && (
                  <Chip
                    icon={<PersonIcon />}
                    label={`Patient ID: ${communication.patientId}`}
                    size="small"
                    variant="outlined"
                    sx={{ mt: 1 }}
                  />
                )}
              </CardContent>
            </Card>
          ))}
          
          {filteredCommunications.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary">
                No communications found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Try adjusting your search criteria
              </Typography>
            </Box>
          )}
        </TabPanel>
      </Paper>

      {/* Execution Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Execution Details: {selectedExecution?.agentName}
        </DialogTitle>
        <DialogContent>
          {selectedExecution && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Basic Information</Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Agent" secondary={selectedExecution.agentName} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Specialty" secondary={selectedExecution.agentSpecialty} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Type" secondary={selectedExecution.executionType} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Framework" secondary={selectedExecution.framework.toUpperCase()} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Status" secondary={
                      <Chip
                        icon={getStatusIcon(selectedExecution.status)}
                        label={selectedExecution.status.toUpperCase()}
                        color={getStatusColor(selectedExecution.status)}
                        size="small"
                      />
                    } />
                  </ListItem>
                </List>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>Performance Metrics</Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Start Time" secondary={formatTimestamp(selectedExecution.startTime)} />
                  </ListItem>
                  {selectedExecution.endTime && (
                    <ListItem>
                      <ListItemText primary="End Time" secondary={formatTimestamp(selectedExecution.endTime)} />
                    </ListItem>
                  )}
                  <ListItem>
                    <ListItemText primary="Duration" secondary={formatDuration(selectedExecution.duration)} />
                  </ListItem>
                  {selectedExecution.tokens && (
                    <>
                      <ListItem>
                        <ListItemText primary="Input Tokens" secondary={selectedExecution.tokens.input.toLocaleString()} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Output Tokens" secondary={selectedExecution.tokens.output.toLocaleString()} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Total Tokens" secondary={selectedExecution.tokens.total.toLocaleString()} />
                      </ListItem>
                    </>
                  )}
                  {selectedExecution.cost && (
                    <ListItem>
                      <ListItemText primary="Cost" secondary={`$${selectedExecution.cost.toFixed(4)}`} />
                    </ListItem>
                  )}
                </List>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>Input Data</Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <Typography variant="body2">{selectedExecution.inputData.query}</Typography>
                  {selectedExecution.inputData.context && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Context: {selectedExecution.inputData.context}
                    </Typography>
                  )}
                </Paper>
              </Grid>
              
              {selectedExecution.outputData && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Output Data</Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {selectedExecution.outputData.result}
                    </Typography>
                    
                    {selectedExecution.outputData.recommendations && selectedExecution.outputData.recommendations.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Recommendations:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {selectedExecution.outputData.recommendations.map((rec, index) => (
                            <Chip key={index} label={rec} size="small" />
                          ))}
                        </Box>
                      </Box>
                    )}
                    
                    {selectedExecution.outputData.nextSteps && selectedExecution.outputData.nextSteps.length > 0 && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>Next Steps:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {selectedExecution.outputData.nextSteps.map((step, index) => (
                            <Chip key={index} label={step} size="small" color="primary" variant="outlined" />
                          ))}
                        </Box>
                      </Box>
                    )}
                    
                    {selectedExecution.outputData.confidence && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Confidence: {(selectedExecution.outputData.confidence * 100).toFixed(1)}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={selectedExecution.outputData.confidence * 100}
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    )}
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentCommunicationHistory; 