import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  Divider,
  Alert,
  InputAdornment,
  IconButton,
  Paper,
  CircularProgress,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  LocationOn as LocationOnIcon,
  Clear as ClearIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  CloudDownload as CloudDownloadIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../store/store';
import { 
  setCurrentPatient, 
  setSearchResults, 
  setSearchTerm, 
  clearSearchResults,
  setLoading,
  setError,
  clearError 
} from '../store/slices/patientSlice';

const PatientSearch: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { currentPatient, searchResults, searchTerm, recentPatients, isLoading, error } = useSelector((state: RootState) => state.patients);
  
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(currentPatient?.patient_id || null);
  const [fhirExpanded, setFhirExpanded] = useState(false);
  const [fhirPatientId, setFhirPatientId] = useState('');
  const [fhirLoading, setFhirLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionMessage, setConnectionMessage] = useState('');
  const [availablePatientIds, setAvailablePatientIds] = useState<string[]>([]);

  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    
    dispatch(setLoading(true));
    dispatch(clearError());
    
    try {
      // Import FHIR MCP service dynamically to avoid bundling issues
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      const results = await fhirService.searchPatients(searchTerm);
      dispatch(setSearchResults(results));
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to search patients'));
      console.error('Patient search failed:', error);
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleSelectPatient = async (patient: any) => {
    setSelectedPatientId(patient.patient_id);
    dispatch(setLoading(true));
    
    try {
      // Import FHIR MCP service dynamically to avoid bundling issues
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      const comprehensivePatientData = await fhirService.getComprehensivePatientData(patient.patient_id);
      dispatch(setCurrentPatient(comprehensivePatientData));
    } catch (error) {
      dispatch(setError(error instanceof Error ? error.message : 'Failed to load comprehensive patient data'));
      console.error('Failed to load patient data:', error);
      // Fallback to basic patient data if comprehensive fetch fails
      dispatch(setCurrentPatient(patient));
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleClearSearch = () => {
    dispatch(clearSearchResults());
    dispatch(setSearchTerm(''));
  };

  const testFhirConnection = async () => {
    setConnectionStatus('testing');
    setConnectionMessage('Testing connection...');
    
    try {
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      const result = await fhirService.testConnection();
      
      if (result.success) {
        setConnectionStatus('success');
        setConnectionMessage(`${result.message}${result.serverInfo ? ` (${result.serverInfo.software} ${result.serverInfo.version})` : ''}`);
        
        // Load available patient IDs
        try {
          const patientIds = await fhirService.getAvailablePatientIds(20);
          setAvailablePatientIds(patientIds);
        } catch (error) {
          console.warn('Failed to load patient IDs:', error);
        }
      } else {
        setConnectionStatus('error');
        setConnectionMessage(result.message);
      }
    } catch (error) {
      setConnectionStatus('error');
      setConnectionMessage(error instanceof Error ? error.message : 'Connection failed');
    }
  };

  const loadPatientFromFhir = async () => {
    if (!fhirPatientId.trim()) {
      alert('Please enter a patient ID');
      return;
    }

    setFhirLoading(true);
    dispatch(setLoading(true));
    dispatch(clearError());

    try {
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      const comprehensivePatientData = await fhirService.getComprehensivePatientData(fhirPatientId.trim());

      if (comprehensivePatientData.success === false) {
        throw new Error(comprehensivePatientData.message || 'Failed to retrieve complete patient data.');
      }

      dispatch(setCurrentPatient(comprehensivePatientData));
      setSelectedPatientId(comprehensivePatientData.patient_id);
      alert(`Successfully loaded patient: ${comprehensivePatientData.name}`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load patient';
      dispatch(setError(errorMessage));
      alert(`Failed to load patient ${fhirPatientId}: ${errorMessage}`);
    } finally {
      setFhirLoading(false);
      dispatch(setLoading(false));
    }
  };

  const getGenderIcon = (gender: string) => {
    return <PersonIcon />;
  };

  const getAgeColor = (age: number) => {
    if (age < 18) return 'info';
    if (age > 65) return 'warning';
    return 'default';
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Patient Search
      </Typography>

      <Grid container spacing={3}>
        {/* Search Section */}
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Patients
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                  fullWidth
                  placeholder="Search by name, ID, or other identifier..."
                  value={searchTerm}
                  onChange={(e) => dispatch(setSearchTerm(e.target.value))}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch();
                    }
                  }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                    endAdornment: searchTerm && (
                      <InputAdornment position="end">
                        <IconButton onClick={handleClearSearch} size="small">
                          <ClearIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleSearch}
                  disabled={!searchTerm.trim() || isLoading}
                  sx={{ minWidth: 120 }}
                >
                  {isLoading ? <CircularProgress size={24} /> : 'Search'}
                </Button>
              </Box>

              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              {/* Search Results */}
              {searchResults.length > 0 && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Search Results ({searchResults.length})
                  </Typography>
                  <List>
                    {searchResults.map((patient, index) => (
                      <React.Fragment key={patient.patient_id}>
                        <ListItem
                          button
                          onClick={() => handleSelectPatient(patient)}
                          selected={selectedPatientId === patient.patient_id}
                          sx={{ 
                            borderRadius: 1,
                            mb: 1,
                            bgcolor: selectedPatientId === patient.patient_id ? 'action.selected' : 'background.paper',
                          }}
                        >
                          <ListItemAvatar>
                            <Avatar sx={{ bgcolor: 'primary.main' }}>
                              {getGenderIcon(patient.gender)}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                  {patient.name}
                                </Typography>
                                <Chip 
                                  label={`${patient.age}y`} 
                                  size="small" 
                                  color={getAgeColor(patient.age) as any}
                                />
                                <Chip 
                                  label={patient.gender} 
                                  size="small" 
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  ID: {patient.patient_id} • DOB: {patient.birth_date}
                                </Typography>
                                {patient.phone && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                                    <PhoneIcon fontSize="small" />
                                    <Typography variant="body2">{patient.phone}</Typography>
                                  </Box>
                                )}
                                {patient.email && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                    <EmailIcon fontSize="small" />
                                    <Typography variant="body2">{patient.email}</Typography>
                                  </Box>
                                )}
                              </Box>
                            }
                          />
                          {selectedPatientId === patient.patient_id && (
                            <CheckCircleIcon color="primary" />
                          )}
                        </ListItem>
                        {index < searchResults.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </Box>
              )}

              {/* Recent Patients */}
              {searchResults.length === 0 && !searchTerm && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Recent Patients
                  </Typography>
                  <List>
                    {recentPatients.map((patient, index) => (
                      <React.Fragment key={patient.patient_id}>
                        <ListItem
                          button
                          onClick={() => handleSelectPatient(patient)}
                          selected={selectedPatientId === patient.patient_id}
                          sx={{ 
                            borderRadius: 1,
                            mb: 1,
                            bgcolor: selectedPatientId === patient.patient_id ? 'action.selected' : 'background.paper',
                          }}
                        >
                          <ListItemAvatar>
                            <Avatar sx={{ bgcolor: 'secondary.main' }}>
                              {getGenderIcon(patient.gender)}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="subtitle1" fontWeight="bold">
                                  {patient.name}
                                </Typography>
                                <Chip 
                                  label={`${patient.age}y`} 
                                  size="small" 
                                  color={getAgeColor(patient.age) as any}
                                />
                                <Chip 
                                  label={patient.gender} 
                                  size="small" 
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={
                              <Typography variant="body2" color="text.secondary">
                                ID: {patient.patient_id} • DOB: {patient.birth_date}
                              </Typography>
                            }
                          />
                          {selectedPatientId === patient.patient_id && (
                            <CheckCircleIcon color="primary" />
                          )}
                        </ListItem>
                        {index < recentPatients.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* FHIR Data Loader */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CloudDownloadIcon color="primary" />
                  <Typography variant="h6">
                    FHIR Data Loader
                  </Typography>
                </Box>
                <IconButton 
                  onClick={() => setFhirExpanded(!fhirExpanded)}
                  size="small"
                >
                  {fhirExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Load real patient data from FHIR server 
              </Typography>

              <Collapse in={fhirExpanded}>
                <Box sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
                  {/* Connection Test */}
                  <Box sx={{ mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Button
                        variant="outlined"
                        onClick={testFhirConnection}
                        disabled={connectionStatus === 'testing'}
                        startIcon={<SettingsIcon />}
                        size="small"
                      >
                        {connectionStatus === 'testing' ? 'Testing...' : 'Test Connection'}
                      </Button>
                      
                      {connectionStatus === 'success' && (
                        <Chip 
                          label="Connected" 
                          color="success" 
                          size="small" 
                          icon={<CheckCircleIcon />} 
                        />
                      )}
                      {connectionStatus === 'error' && (
                        <Chip 
                          label="Error" 
                          color="error" 
                          size="small" 
                          icon={<WarningIcon />} 
                        />
                      )}
                    </Box>
                    
                    {connectionMessage && (
                      <Alert 
                        severity={connectionStatus === 'success' ? 'success' : connectionStatus === 'error' ? 'error' : 'info'}
                        sx={{ mb: 2 }}
                      >
                        {connectionMessage}
                      </Alert>
                    )}
                  </Box>

                  {/* Patient ID Input */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Load Patient by ID
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Patient ID"
                        value={fhirPatientId}
                        onChange={(e) => setFhirPatientId(e.target.value)}
                        placeholder="e.g., example-patient-1"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            loadPatientFromFhir();
                          }
                        }}
                      />
                      <Button
                        variant="contained"
                        onClick={loadPatientFromFhir}
                        disabled={!fhirPatientId.trim() || fhirLoading}
                        sx={{ minWidth: 100 }}
                      >
                        {fhirLoading ? <CircularProgress size={20} /> : 'Load'}
                      </Button>
                    </Box>
                  </Box>

                  {/* Available Patient IDs */}
                  {availablePatientIds.length > 0 && (
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Available Patient IDs
                      </Typography>
                      <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                        <InputLabel>Select Patient ID</InputLabel>
                        <Select
                          value={fhirPatientId}
                          onChange={(e) => setFhirPatientId(e.target.value)}
                          label="Select Patient ID"
                        >
                          {availablePatientIds.map((id) => (
                            <MenuItem key={id} value={id}>
                              {id}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Box>
                  )}

                  <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      <strong>FHIR Server:</strong> {process.env.REACT_APP_FHIR_BASE_URL || 'https://hapi.fhir.org/baseR4'}
                    </Typography>
                  </Box>
                </Box>
              </Collapse>
            </CardContent>
          </Card>
        </Grid>

        {/* Selected Patient Details */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Selected Patient
              </Typography>
              
              {currentPatient ? (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2, width: 56, height: 56 }}>
                      <PersonIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h6">{currentPatient.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {currentPatient.age} years old • {currentPatient.gender}
                      </Typography>
                    </Box>
                  </Box>

                  <Divider sx={{ mb: 2 }} />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Contact Information
                    </Typography>
                    {currentPatient.phone && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <PhoneIcon fontSize="small" />
                        <Typography variant="body2">{currentPatient.phone}</Typography>
                      </Box>
                    )}
                    {currentPatient.email && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <EmailIcon fontSize="small" />
                        <Typography variant="body2">{currentPatient.email}</Typography>
                      </Box>
                    )}
                    {currentPatient.address && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LocationOnIcon fontSize="small" />
                        <Typography variant="body2">{currentPatient.address}</Typography>
                      </Box>
                    )}
                  </Box>

                  <Divider sx={{ mb: 2 }} />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Clinical Summary
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          Active Conditions: {currentPatient.conditions?.length || 0}
                        </Typography>
                        {currentPatient.conditions?.slice(0, 2).map((condition: any, index: number) => (
                          <Chip
                            key={index}
                            label={condition.display}
                            size="small"
                            sx={{ mr: 0.5, mt: 0.5 }}
                          />
                        ))}
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          Current Medications: {currentPatient.medications?.length || 0}
                        </Typography>
                        {currentPatient.medications?.slice(0, 2).map((medication: any, index: number) => (
                          <Chip
                            key={index}
                            label={medication.name}
                            size="small"
                            variant="outlined"
                            sx={{ mr: 0.5, mt: 0.5 }}
                          />
                        ))}
                      </Box>

                      {currentPatient.allergies?.length > 0 && (
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <WarningIcon fontSize="small" color="warning" />
                          <Typography variant="body2" color="warning.main">
                            Allergies: {currentPatient.allergies.join(', ')}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Box>

                  <Button
                    variant="contained"
                    fullWidth
                    onClick={() => {
                      // Navigate to agent console using React Router (preserves Redux state)
                      navigate('/agents');
                    }}
                  >
                    Start AI Assessment
                  </Button>
                </Box>
              ) : (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  py: 4,
                  color: 'text.secondary' 
                }}>
                  <PersonIcon sx={{ fontSize: 48, mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    No Patient Selected
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    Search for and select a patient to view their details and start an AI assessment
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PatientSearch; 