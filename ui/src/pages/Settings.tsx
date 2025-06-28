import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon,
  RestoreFromTrash as RestoreIcon,
  Security as SecurityIcon,
  Api as ApiIcon,
  Notifications as NotificationsIcon,
  Psychology as PsychologyIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [mcpTestStatus, setMcpTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [mcpTestMessage, setMcpTestMessage] = useState('');
  const [patientTestData, setPatientTestData] = useState<any>(null);
  const [settings, setSettings] = useState({
    autoSave: true,
    darkMode: false,
    language: 'en',
    timezone: 'UTC',
    defaultFramework: 'autogen',
    multiAgentMode: true,
    responseTimeout: 30,
    maxConversationLength: 100,
    fhirServerUrl: 'https://hapi.fhir.org/baseR4',
    fhirClientId: 'agentic-healthcare-ai ',
    enableSmartAuth: true,
    useFhirMcp: true,
    fhirMcpUrl: `${process.env.REACT_APP_NETWORK_PROTOCOL || 'http'}://${process.env.REACT_APP_NETWORK_HOST || 'localhost'}:8004`,
    // MCP Inspector Configuration
    mcpServerRequestTimeout: 10000,
    mcpRequestTimeoutResetOnProgress: true,
    mcpRequestMaxTotalTimeout: 60000,
    mcpProxyFullAddress: process.env.REACT_APP_NETWORK_HOST || 'localhost',
    clientPort: 6274,
    serverPort: 6277,
    emailNotifications: true,
    pushNotifications: false,
    alertSounds: true,
    clinicalAlerts: true,
  });

  // Load settings from localStorage on component mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('healthcare-ai-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prevSettings => ({ ...prevSettings, ...parsed }));
      } catch (error) {
        console.error('Failed to load settings from localStorage:', error);
      }
    }
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSettings = async () => {
    setSaveStatus('saving');
    
    try {
      // Save to localStorage
      localStorage.setItem('healthcare-ai-settings', JSON.stringify(settings));
      
      // Update FHIR service configuration
      if (settings.fhirServerUrl) {
        // Store FHIR URL in localStorage for FHIR service to use
        localStorage.setItem('REACT_APP_FHIR_BASE_URL', settings.fhirServerUrl);
        
        // Update FHIR MCP service instance with new configuration
        try {
          const { FHIRMcpService } = await import('../services/fhirMcpService');
          const fhirService = FHIRMcpService.getService();
          fhirService.updateBaseUrl(settings.fhirServerUrl);
          
          if (settings.fhirMcpUrl) {
            fhirService.updateMcpUrl(settings.fhirMcpUrl);
          }
          
          fhirService.setUseMcp(settings.useFhirMcp);
          
          // Update MCP configuration
          fhirService.updateMcpConfig({
            mcpServerRequestTimeout: settings.mcpServerRequestTimeout,
            mcpRequestTimeoutResetOnProgress: settings.mcpRequestTimeoutResetOnProgress,
            mcpRequestMaxTotalTimeout: settings.mcpRequestMaxTotalTimeout,
            mcpProxyFullAddress: settings.mcpProxyFullAddress,
            clientPort: settings.clientPort,
            serverPort: settings.serverPort,
          });
          
          // Re-initialize the MCP service with new settings
          FHIRMcpService.initialize();
        } catch (error) {
          console.warn('Could not update FHIR MCP service configuration:', error);
        }
      }
      
      // Simulate API call to save settings to backend (replace with actual API call)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSaveStatus('success');
      
      // Reset status after 3 seconds
      setTimeout(() => setSaveStatus('idle'), 3000);
      
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus('error');
      
      // Reset status after 3 seconds
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const handleResetSettings = () => {
    if (window.confirm('Are you sure you want to reset all settings to default?')) {
      const defaultSettings = {
        autoSave: true,
        darkMode: false,
        language: 'en',
        timezone: 'UTC',
        defaultFramework: 'autogen',
        multiAgentMode: true,
        responseTimeout: 30,
        maxConversationLength: 100,
        fhirServerUrl: 'https://hapi.fhir.org/baseR4',
        fhirClientId: 'agentic-healthcare-ai ',
        enableSmartAuth: true,
        useFhirMcp: true,
        fhirMcpUrl: `${process.env.REACT_APP_NETWORK_PROTOCOL || 'http'}://${process.env.REACT_APP_NETWORK_HOST || 'localhost'}:8004/rpc`,
        // MCP Inspector Configuration defaults
        mcpServerRequestTimeout: 10000,
        mcpRequestTimeoutResetOnProgress: true,
        mcpRequestMaxTotalTimeout: 60000,
        mcpProxyFullAddress: process.env.REACT_APP_NETWORK_HOST || 'localhost',
        clientPort: 6274,
        serverPort: 6277,
        emailNotifications: true,
        pushNotifications: false,
        alertSounds: true,
        clinicalAlerts: true,
      };
      
      setSettings(defaultSettings);
      
      // Clear localStorage
      localStorage.removeItem('healthcare-ai-settings');
      localStorage.removeItem('REACT_APP_FHIR_BASE_URL');
      
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestMessage('Testing connection to FHIR server...');
    
    try {
      // Update FHIR MCP service with current configuration first
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      fhirService.updateBaseUrl(settings.fhirServerUrl);
      fhirService.updateMcpUrl(settings.fhirMcpUrl);
      fhirService.setUseMcp(settings.useFhirMcp);
      
      // Test the connection
      const result = await fhirService.testConnection();
      
      if (result.success) {
        setTestStatus('success');
        const methodInfo = result.serverInfo?.method ? ` via ${result.serverInfo.method}` : '';
        const serverInfo = result.serverInfo?.software ? ` (${result.serverInfo.software})` : '';
        setTestMessage(`✅ ${result.message}${methodInfo}${serverInfo}`);
      } else {
        setTestStatus('error');
        setTestMessage(`❌ ${result.message}`);
      }
    } catch (error) {
      setTestStatus('error');
      setTestMessage(`❌ Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    
    // Reset test status after 5 seconds
    setTimeout(() => {
      setTestStatus('idle');
      setTestMessage('');
    }, 5000);
  };

  const handleTestMcpWithPatientData = async () => {
    setMcpTestStatus('testing');
    setMcpTestMessage('Testing MCP connection with patient data...');
    setPatientTestData(null);
    
    try {
      // Update FHIR MCP service with current configuration first
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      fhirService.updateBaseUrl(settings.fhirServerUrl);
      fhirService.updateMcpUrl(settings.fhirMcpUrl);
      fhirService.setUseMcp(true); // Force MCP for this test
      
      // First test MCP health
      const healthResult = await FHIRMcpService.testMcpConnection();
      if (!healthResult.success) {
        throw new Error(`MCP Health Check Failed: ${healthResult.message}`);
      }
      
      // Try predefined patient IDs first, then fallback to getting available ones
      setMcpTestMessage('Trying predefined patient IDs...');
      const predefinedPatientIds = ['597179', '597217', '597213', '597173', '597220'];
      let patientData = null;
      let firstPatientId = null;
      let triedPatientIds = [];
      
      // Try each predefined patient ID
      for (const patientId of predefinedPatientIds) {
        try {
          setMcpTestMessage(`Trying patient ID: ${patientId}... (${triedPatientIds.length + 1}/${predefinedPatientIds.length})`);
          triedPatientIds.push(patientId);
          
          // Add a small delay for better UX
          await new Promise(resolve => setTimeout(resolve, 500));
          
          patientData = await fhirService.getComprehensivePatientData(patientId);
          if (patientData) {
            firstPatientId = patientId;
            setMcpTestMessage(`✅ Found patient data for ID: ${patientId}!`);
            break;
          }
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : 'Unknown error';
          console.warn(`Patient ${patientId} failed: ${errorMsg}`);
          
          // Continue to next patient ID
          if (triedPatientIds.length < predefinedPatientIds.length) {
            setMcpTestMessage(`❌ Patient ${patientId} not found, trying next...`);
            continue;
          }
        }
      }
      
      // If none of the predefined IDs worked, get available patient IDs from server
      if (!patientData) {
        setMcpTestMessage(`❌ None of predefined patient IDs found. Tried: [${triedPatientIds.join(', ')}]. Getting available patients from server...`);
        
        try {
          const availablePatientIds = await fhirService.getAvailablePatientIds(5);
          
          if (availablePatientIds.length === 0) {
            throw new Error('No patients found in FHIR server');
          }
          
          firstPatientId = availablePatientIds[0];
          setMcpTestMessage(`🔍 Found ${availablePatientIds.length} available patients. Trying ID: ${firstPatientId}...`);
          patientData = await fhirService.getComprehensivePatientData(firstPatientId);
        } catch (fallbackError) {
          throw new Error(`Failed to get patient data from server. Tried predefined IDs: [${triedPatientIds.join(', ')}]. Server error: ${fallbackError instanceof Error ? fallbackError.message : 'Unknown error'}`);
        }
      }
      
      if (patientData) {
        setMcpTestStatus('success');
        setPatientTestData(patientData);
        setMcpTestMessage(`✅ Successfully retrieved patient data via MCP! Patient: ${patientData.name || 'Unknown'} (ID: ${firstPatientId})`);
      } else {
        throw new Error('No patient data returned');
      }
      
    } catch (error) {
      setMcpTestStatus('error');
      setMcpTestMessage(`❌ MCP Patient Test Failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setPatientTestData(null);
    }
    
    // Reset test status after 10 seconds (longer for patient data review)
    setTimeout(() => {
      setMcpTestStatus('idle');
      setMcpTestMessage('');
      setPatientTestData(null);
    }, 10000);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label="General" icon={<SettingsIcon />} />
            <Tab label="AI Agents" icon={<PsychologyIcon />} />
            <Tab label="FHIR Configuration" icon={<ApiIcon />} />
            <Tab label="Notifications" icon={<NotificationsIcon />} />
            <Tab label="Security" icon={<SecurityIcon />} />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={activeTab} index={0}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              General Settings
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoSave}
                      onChange={(e) => handleSettingChange('autoSave', e.target.checked)}
                    />
                  }
                  label="Auto-save conversations"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.darkMode}
                      onChange={(e) => handleSettingChange('darkMode', e.target.checked)}
                    />
                  }
                  label="Dark mode"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={settings.language}
                    label="Language"
                    onChange={(e) => handleSettingChange('language', e.target.value)}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="es">Spanish</MenuItem>
                    <MenuItem value="fr">French</MenuItem>
                    <MenuItem value="de">German</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={settings.timezone}
                    label="Timezone"
                    onChange={(e) => handleSettingChange('timezone', e.target.value)}
                  >
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="America/New_York">Eastern Time</MenuItem>
                    <MenuItem value="America/Chicago">Central Time</MenuItem>
                    <MenuItem value="America/Denver">Mountain Time</MenuItem>
                    <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </TabPanel>

        {/* AI Agent Settings */}
        <TabPanel value={activeTab} index={1}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              AI Agent Configuration
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Default Framework</InputLabel>
                  <Select
                    value={settings.defaultFramework}
                    label="Default Framework"
                    onChange={(e) => handleSettingChange('defaultFramework', e.target.value)}
                  >
                    <MenuItem value="autogen">Microsoft Autogen</MenuItem>
                    <MenuItem value="crewai">CrewAI</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.multiAgentMode}
                      onChange={(e) => handleSettingChange('multiAgentMode', e.target.checked)}
                    />
                  }
                  label="Enable multi-agent collaboration"
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Response Timeout (seconds)"
                  type="number"
                  value={settings.responseTimeout}
                  onChange={(e) => handleSettingChange('responseTimeout', parseInt(e.target.value))}
                  inputProps={{ min: 10, max: 120 }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Max Conversation Length"
                  type="number"
                  value={settings.maxConversationLength}
                  onChange={(e) => handleSettingChange('maxConversationLength', parseInt(e.target.value))}
                  inputProps={{ min: 20, max: 500 }}
                />
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>
              Agent Specialties
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText
                  primary="Primary Care Physician"
                  secondary="General medical assessment and care coordination"
                />
                <ListItemSecondaryAction>
                  <Chip label="Active" color="success" size="small" />
                  <IconButton edge="end">
                    <EditIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText
                  primary="Cardiologist"
                  secondary="Cardiovascular assessment and risk stratification"
                />
                <ListItemSecondaryAction>
                  <Chip label="Active" color="success" size="small" />
                  <IconButton edge="end">
                    <EditIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
              
              <ListItem>
                <ListItemText
                  primary="Clinical Pharmacist"
                  secondary="Medication review and drug interaction analysis"
                />
                <ListItemSecondaryAction>
                  <Chip label="Active" color="success" size="small" />
                  <IconButton edge="end">
                    <EditIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </CardContent>
        </TabPanel>

        {/* FHIR Configuration */}
        <TabPanel value={activeTab} index={2}>
          <CardContent>
            {/* MCP Configuration Section */}
            <Typography variant="h6" gutterBottom>
              MCP Configuration
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              Configure your FHIR server connection for real patient data integration.
            </Alert>
            
            <Divider sx={{ my: 3 }} />
            
            <Typography variant="h6" gutterBottom>
              FHIR Server Configuration
            </Typography>
            
            <Alert severity={settings.useFhirMcp ? "success" : "warning"} sx={{ mb: 3 }}>
              {settings.useFhirMcp 
                ? "✅ Using Model Context Protocol (MCP) for secure FHIR communication"
                : "⚠️ Using direct FHIR communication (consider enabling MCP for enhanced security)"
              }
            </Alert>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.useFhirMcp}
                        onChange={(e) => handleSettingChange('useFhirMcp', e.target.checked)}
                        color="success"
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="subtitle1" component="div">
                          Use FHIR MCP Server (Model Context Protocol)
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {settings.useFhirMcp 
                            ? "MCP provides standardized, secure access to FHIR resources with enhanced tooling support"
                            : "Enable for standardized FHIR access through the Model Context Protocol"
                          }
                        </Typography>
                      </Box>
                    }
                  />
                  
                  {settings.useFhirMcp && (
                    <Box sx={{ mt: 2, pl: 4 }}>
                      <Typography variant="body2" color="success.main">
                        • Enhanced security through standardized protocol<br/>
                        • Better error handling and logging<br/>
                        • Optimized for AI agent communication<br/>
                        • Centralized FHIR connection management
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Grid>

              {settings.useFhirMcp && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="FHIR MCP Server URL"
                    value={settings.fhirMcpUrl}
                    onChange={(e) => handleSettingChange('fhirMcpUrl', e.target.value)}
                    placeholder={`${process.env.REACT_APP_NETWORK_PROTOCOL || 'http'}://${process.env.REACT_APP_NETWORK_HOST || 'localhost'}:8004`}
                    helperText="URL of the FHIR MCP server that will handle all FHIR communication"
                    InputProps={{
                      startAdornment: (
                        <Box sx={{ mr: 1, color: 'success.main' }}>🔗</Box>
                      ),
                    }}
                  />
                </Grid>
              )}
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="FHIR Server URL"
                  value={settings.fhirServerUrl}
                  onChange={(e) => handleSettingChange('fhirServerUrl', e.target.value)}
                  placeholder="https://your-fhir-server.com/fhir"
                  helperText={settings.useFhirMcp 
                    ? "Target FHIR server that the MCP server will connect to"
                    : "Direct connection endpoint for FHIR server"
                  }
                  InputProps={{
                    startAdornment: (
                      <Box sx={{ mr: 1, color: settings.useFhirMcp ? 'info.main' : 'warning.main' }}>
                        {settings.useFhirMcp ? '🏥' : '🔗'}
                      </Box>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Client ID"
                  value={settings.fhirClientId}
                  onChange={(e) => handleSettingChange('fhirClientId', e.target.value)}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.enableSmartAuth}
                      onChange={(e) => handleSettingChange('enableSmartAuth', e.target.checked)}
                    />
                  }
                  label="Enable SMART on FHIR Authentication"
                />
              </Grid>
              
              {/* MCP Inspector Configuration */}
              {settings.useFhirMcp && (
                <Grid item xs={12}>
                  <Divider sx={{ my: 3 }} />
                  <Typography variant="h6" gutterBottom color="primary">
                    🔧 MCP Inspector Configuration
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
                    Advanced timeout and connection settings for the Model Context Protocol interface
                  </Typography>
                  
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="MCP Server Request Timeout (ms)"
                        type="number"
                        value={settings.mcpServerRequestTimeout}
                        onChange={(e) => handleSettingChange('mcpServerRequestTimeout', parseInt(e.target.value))}
                        inputProps={{ min: 1000, max: 120000, step: 1000 }}
                        helperText="Timeout for individual MCP requests (1-120 seconds)"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="MCP Max Total Timeout (ms)"
                        type="number"
                        value={settings.mcpRequestMaxTotalTimeout}
                        onChange={(e) => handleSettingChange('mcpRequestMaxTotalTimeout', parseInt(e.target.value))}
                        inputProps={{ min: 10000, max: 300000, step: 5000 }}
                        helperText="Maximum total timeout for complex operations (10-300 seconds)"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="MCP Proxy Address"
                        value={settings.mcpProxyFullAddress}
                        onChange={(e) => handleSettingChange('mcpProxyFullAddress', e.target.value)}
                        placeholder={process.env.REACT_APP_NETWORK_HOST || 'localhost'}
                        helperText="Address for the MCP proxy server"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={3}>
                      <TextField
                        fullWidth
                        label="Client Port"
                        type="number"
                        value={settings.clientPort}
                        onChange={(e) => handleSettingChange('clientPort', parseInt(e.target.value))}
                        inputProps={{ min: 1024, max: 65535 }}
                        helperText="MCP Client UI port (standard: 6274)"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={3}>
                      <TextField
                        fullWidth
                        label="Server Port"
                        type="number"
                        value={settings.serverPort}
                        onChange={(e) => handleSettingChange('serverPort', parseInt(e.target.value))}
                        inputProps={{ min: 1024, max: 65535 }}
                        helperText="MCP Proxy port (standard: 6277)"
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={settings.mcpRequestTimeoutResetOnProgress}
                            onChange={(e) => handleSettingChange('mcpRequestTimeoutResetOnProgress', e.target.checked)}
                            color="success"
                          />
                        }
                        label={
                          <Box>
                            <Typography variant="subtitle2" component="div">
                              Reset Timeout on Progress
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Automatically reset request timeouts when progress notifications are received
                            </Typography>
                          </Box>
                        }
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Box sx={{ p: 2, border: '1px solid', borderColor: 'info.main', borderRadius: 1, bgcolor: 'info.main', opacity: 0.05 }}>
                        <Typography variant="body2" color="info.main">
                          <strong>ℹ️ Standard MCP Inspector Ports:</strong><br/>
                          • Client Port 6274 (T9 mapping of MCPI)<br/>
                          • Server Port 6277 (T9 mapping of MCPP)<br/>
                          • Current timeouts: {settings.mcpServerRequestTimeout}ms request, {settings.mcpRequestMaxTotalTimeout}ms total
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Grid>
              )}
              
              <Grid item xs={12}>
                {testMessage && (
                  <Alert 
                    severity={testStatus === 'testing' ? 'info' : testStatus === 'success' ? 'success' : 'error'}
                    sx={{ mb: 2 }}
                  >
                    {testMessage}
                  </Alert>
                )}
                
                {mcpTestMessage && (
                  <Alert 
                    severity={mcpTestStatus === 'testing' ? 'info' : mcpTestStatus === 'success' ? 'success' : 'error'}
                    sx={{ mb: 2 }}
                  >
                    {mcpTestMessage}
                  </Alert>
                )}
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
                  <Button 
                    variant="outlined" 
                    onClick={handleTestConnection}
                    disabled={testStatus === 'testing' || !settings.fhirServerUrl}
                  >
                    {testStatus === 'testing' ? 'Testing...' : `Test ${settings.useFhirMcp ? 'MCP' : 'Proxy'} Connection`}
                  </Button>
                  
                  {settings.useFhirMcp && (
                    <Button 
                      variant="outlined" 
                      onClick={async () => {
                        setTestStatus('testing');
                        setTestMessage('Testing MCP server health...');
                        
                        try {
                          const { FHIRMcpService } = await import('../services/fhirMcpService');
                          const result = await FHIRMcpService.testMcpConnection();
                          
                          if (result.success) {
                            setTestStatus('success');
                            setTestMessage(`✅ MCP Health Check: ${result.message}`);
                          } else {
                            setTestStatus('error');
                            setTestMessage(`❌ MCP Health Check Failed: ${result.message}`);
                          }
                        } catch (error) {
                          setTestStatus('error');
                          setTestMessage(`❌ MCP Health Check Failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
                        }
                        
                        setTimeout(() => {
                          setTestStatus('idle');
                          setTestMessage('');
                        }, 5000);
                      }}
                      disabled={testStatus === 'testing' || !settings.fhirMcpUrl}
                    >
                      Test MCP Health
                    </Button>
                  )}
                  
                  {settings.useFhirMcp && (
                    <Button 
                      variant="contained" 
                      color="primary"
                      onClick={handleTestMcpWithPatientData}
                      disabled={mcpTestStatus === 'testing' || !settings.fhirMcpUrl || !settings.fhirServerUrl}
                    >
                      {mcpTestStatus === 'testing' ? 'Fetching Patient...' : 'Test MCP with Patient Data'}
                    </Button>
                  )}
                  
                  <Button variant="outlined" disabled>
                    Validate Configuration (Coming Soon)
                  </Button>
                </Box>
                
                {/* Patient Test Data Display */}
                {patientTestData && (
                  <Box sx={{ 
                    mt: 3, 
                    p: 3, 
                    border: '2px solid', 
                    borderColor: 'success.main', 
                    borderRadius: 2, 
                    bgcolor: 'success.light', 
                    opacity: 1,
                    boxShadow: 2
                  }}>
                    <Typography variant="h6" gutterBottom color="success.dark" sx={{ fontWeight: 'bold' }}>
                      🎉 MCP Patient Data Test - Success!
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>
                          Patient Information:
                        </Typography>
                        <Typography variant="body1" sx={{ color: 'text.primary', lineHeight: 1.8 }}>
                          <strong>Name:</strong> {patientTestData.name || 'N/A'}<br/>
                          <strong>ID:</strong> {patientTestData.id || 'N/A'}<br/>
                          <strong>Gender:</strong> {patientTestData.gender || 'N/A'}<br/>
                          <strong>Birth Date:</strong> {patientTestData.birthDate || 'N/A'}<br/>
                          <strong>Age:</strong> {patientTestData.age || 'N/A'}
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Typography variant="subtitle2" gutterBottom>
                          Clinical Summary:
                        </Typography>
                        <Typography variant="body1" sx={{ color: 'text.primary', lineHeight: 1.8 }}>
                          <strong>Conditions:</strong> {patientTestData.conditions?.length || 0} found<br/>
                          <strong>Medications:</strong> {patientTestData.medications?.length || 0} found<br/>
                          <strong>Observations:</strong> {patientTestData.observations?.length || 0} found<br/>
                          <strong>Via:</strong> FHIR MCP Server 🔗
                        </Typography>
                      </Grid>
                      
                      {patientTestData.conditions && patientTestData.conditions.length > 0 && (
                        <Grid item xs={12}>
                          <Typography variant="subtitle2" gutterBottom>
                            Recent Conditions:
                          </Typography>
                          <Typography variant="body1" sx={{ color: 'text.primary', lineHeight: 1.8 }}>
                            {patientTestData.conditions.slice(0, 3).map((condition: any, index: number) => (
                              <span key={index}>
                                • {condition.condition || condition.display || ''}
                                {index < Math.min(2, patientTestData.conditions.length - 1) ? '<br/>' : ''}
                              </span>
                            ))}
                          </Typography>
                        </Grid>
                      )}
                    </Grid>
                  </Box>
                )}
              </Grid>
            </Grid>
          </CardContent>
        </TabPanel>

        {/* Notifications */}
        <TabPanel value={activeTab} index={3}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Notification Preferences
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.emailNotifications}
                      onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                    />
                  }
                  label="Email notifications"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.pushNotifications}
                      onChange={(e) => handleSettingChange('pushNotifications', e.target.checked)}
                    />
                  }
                  label="Push notifications"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.alertSounds}
                      onChange={(e) => handleSettingChange('alertSounds', e.target.checked)}
                    />
                  }
                  label="Alert sounds"
                />
              </Grid>
              
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.clinicalAlerts}
                      onChange={(e) => handleSettingChange('clinicalAlerts', e.target.checked)}
                    />
                  }
                  label="Clinical alerts (drug interactions, contraindications)"
                />
              </Grid>
            </Grid>
          </CardContent>
        </TabPanel>

        {/* Security */}
        <TabPanel value={activeTab} index={4}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Security & Privacy
            </Typography>
            
            <Alert severity="warning" sx={{ mb: 3 }}>
              Security settings affect data access and user authentication.
            </Alert>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Session Management
                </Typography>
                <TextField
                  fullWidth
                  label="Session Timeout (minutes)"
                  type="number"
                  defaultValue={30}
                  inputProps={{ min: 5, max: 480 }}
                  sx={{ mb: 2 }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Data Retention
                </Typography>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Conversation History Retention</InputLabel>
                  <Select defaultValue="30">
                    <MenuItem value="7">7 days</MenuItem>
                    <MenuItem value="30">30 days</MenuItem>
                    <MenuItem value="90">90 days</MenuItem>
                    <MenuItem value="365">1 year</MenuItem>
                    <MenuItem value="forever">Forever</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Audit Logging
                </Typography>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Log all user activities"
                />
              </Grid>
            </Grid>
          </CardContent>
        </TabPanel>

        <Divider />
        
        <CardContent>
          {/* Save Status Alert */}
          {saveStatus !== 'idle' && (
            <Alert 
              severity={
                saveStatus === 'saving' ? 'info' : 
                saveStatus === 'success' ? 'success' : 'error'
              } 
              sx={{ mb: 2 }}
            >
              {saveStatus === 'saving' && 'Saving settings...'}
              {saveStatus === 'success' && 'Settings saved successfully! Changes will take effect immediately.'}
              {saveStatus === 'error' && 'Failed to save settings. Please try again.'}
            </Alert>
          )}
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              startIcon={<RestoreIcon />}
              onClick={handleResetSettings}
              disabled={saveStatus === 'saving'}
            >
              Reset to Defaults
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSaveSettings}
              disabled={saveStatus === 'saving'}
              color={saveStatus === 'success' ? 'success' : 'primary'}
            >
              {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Settings; 
