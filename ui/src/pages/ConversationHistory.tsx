import React, { useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Avatar,
  Chip,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Person as PersonIcon,
  SmartToy as SmartToyIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  LocalHospital as LocalHospitalIcon,
  LocalHospital as EmergencyIcon,
  Medication as MedicationIcon,
  PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { pdfService } from '../services/pdfService';
import PDFViewer from '../components/PDFViewer';

const ConversationHistory: React.FC = () => {
  const { conversationHistory } = useSelector((state: RootState) => state.conversations);
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // PDF-related state
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [currentPdfData, setCurrentPdfData] = useState<any>(null);

  // Use only real conversation history from Redux store (no mock data)
  const allConversations = conversationHistory;

  const filteredConversations = allConversations.filter(conversation =>
    conversation.patient_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    conversation.conversation_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleViewConversation = (conversation: any) => {
    setSelectedConversation(conversation);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedConversation(null);
  };

  const getConversationTypeInfo = (type: string) => {
    switch (type) {
      case 'comprehensive':
        return { icon: <LocalHospitalIcon />, color: 'primary', label: 'Comprehensive' };
      case 'emergency':
        return { icon: <EmergencyIcon />, color: 'error', label: 'Emergency' };
      case 'medication_review':
        return { icon: <MedicationIcon />, color: 'info', label: 'Medication Review' };
      default:
        return { icon: <ChatIcon />, color: 'default', label: 'Assessment' };
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const handleDownloadPDF = async (pdfReport: any) => {
    try {
      const success = await pdfService.downloadPDF(pdfReport.pdfUrl, pdfReport.filename);
      if (!success) {
        alert('Failed to download PDF report');
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Failed to download PDF report');
    }
  };

  const handleViewPDF = (pdfReport: any) => {
    setCurrentPdfData({
      success: true,
      pdfUrl: pdfReport.pdfUrl,
      filename: pdfReport.filename,
      metadata: {
        patientId: pdfReport.patientId || 'Unknown',
        patientName: pdfReport.patientName,
        assessmentType: pdfReport.assessmentType,
        generatedAt: pdfReport.generatedAt,
        size: pdfReport.size || 0
      }
    });
    setPdfViewerOpen(true);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Conversation History
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <TextField
                  placeholder="Search conversations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                  sx={{ flexGrow: 1 }}
                />
                <Button variant="outlined" startIcon={<DownloadIcon />}>
                  Export
                </Button>
              </Box>

              <Typography variant="h6" gutterBottom>
                Recent Conversations ({filteredConversations.length})
              </Typography>

              <List>
                {filteredConversations.map((conversation, index) => {
                  const typeInfo = getConversationTypeInfo(conversation.conversation_type);
                  return (
                    <React.Fragment key={conversation.conversation_id}>
                      <ListItem
                        sx={{
                          bgcolor: 'background.paper',
                          borderRadius: 1,
                          mb: 1,
                          border: '1px solid',
                          borderColor: 'divider',
                        }}
                      >
                        <Avatar sx={{ bgcolor: `${typeInfo.color}.main`, mr: 2 }}>
                          {typeInfo.icon}
                        </Avatar>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle1" fontWeight="bold">
                                {conversation.patient_name || `Patient ID: ${conversation.patient_id}`}
                              </Typography>
                              <Chip
                                label={typeInfo.label}
                                color={typeInfo.color as any}
                                size="small"
                              />
                              <Chip
                                label={conversation.framework.toUpperCase()}
                                size="small"
                                variant="outlined"
                              />
                              <Chip
                                label={conversation.status}
                                color={conversation.status === 'completed' ? 'success' : 'warning'}
                                size="small"
                              />
                              {conversation.pdfReports && conversation.pdfReports.length > 0 && (
                                <Chip
                                  icon={<PdfIcon />}
                                  label={`${conversation.pdfReports.length} PDF${conversation.pdfReports.length > 1 ? 's' : ''}`}
                                  color="error"
                                  size="small"
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {formatDate(conversation.timestamp)}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                Participants: {conversation.participants.join(', ')}
                              </Typography>
                              {conversation.summary && (
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                                  {conversation.summary.assessment}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<VisibilityIcon />}
                            onClick={() => handleViewConversation(conversation)}
                          >
                            View
                          </Button>
                          
                          {/* PDF Reports Section */}
                          {conversation.pdfReports && conversation.pdfReports.length > 0 && (
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {conversation.pdfReports.map((pdfReport: any, pdfIndex: number) => (
                                <Box key={pdfIndex} sx={{ display: 'flex', gap: 0.5 }}>
                                  <Button
                                    variant="outlined"
                                    size="small"
                                    startIcon={<PdfIcon />}
                                    onClick={() => handleViewPDF(pdfReport)}
                                    sx={{ 
                                      fontSize: '0.7rem',
                                      minWidth: 'auto',
                                      px: 1,
                                      color: 'error.main',
                                      borderColor: 'error.main'
                                    }}
                                  >
                                    View PDF
                                  </Button>
                                  <Button
                                    variant="text"
                                    size="small"
                                    startIcon={<DownloadIcon />}
                                    onClick={() => handleDownloadPDF(pdfReport)}
                                    sx={{ 
                                      fontSize: '0.7rem',
                                      minWidth: 'auto',
                                      px: 1
                                    }}
                                  >
                                    Download
                                  </Button>
                                </Box>
                              ))}
                            </Box>
                          )}
                        </Box>
                      </ListItem>
                      {index < filteredConversations.length - 1 && <Divider />}
                    </React.Fragment>
                  );
                })}
              </List>

              {filteredConversations.length === 0 && (
                <Box sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  py: 8,
                  color: 'text.secondary'
                }}>
                  <ChatIcon sx={{ fontSize: 64, mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No Conversations Found
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    {searchTerm ? 'No conversations match your search criteria' : 'Start a conversation with AI agents to see history here'}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Conversation Detail Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: { minHeight: '60vh' }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main' }}>
              <ChatIcon />
            </Avatar>
            <Box>
              <Typography variant="h6">
                {selectedConversation?.patient_name || `Patient ID: ${selectedConversation?.patient_id}`} - {getConversationTypeInfo(selectedConversation?.conversation_type || '').label}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedConversation && formatDate(selectedConversation.timestamp)}
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedConversation && (
            <Box>
              {/* Summary Section */}
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Summary</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Assessment
                      </Typography>
                      <Typography variant="body2">
                        {selectedConversation.summary?.assessment || 'No summary available'}
                      </Typography>
                    </Box>
                    
                    {selectedConversation.summary?.recommendations && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Recommendations
                        </Typography>
                        <List dense>
                          {selectedConversation.summary.recommendations.map((rec: string, index: number) => (
                            <ListItem key={index} sx={{ py: 0.5 }}>
                              <Typography variant="body2">• {rec}</Typography>
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>

              {/* Messages Section */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Full Conversation</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                    {selectedConversation.messages?.map((message: any) => (
                      <Box key={message.id} sx={{ mb: 2 }}>
                        <Paper
                          sx={{
                            p: 2,
                            bgcolor: message.role === 'user' ? 'primary.light' : 'background.paper',
                            color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                            ml: message.role === 'user' ? 4 : 0,
                            mr: message.role === 'user' ? 0 : 4,
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Avatar sx={{ width: 24, height: 24, mr: 1 }}>
                              {message.role === 'user' ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
                            </Avatar>
                            <Typography variant="caption" fontWeight="bold">
                              {message.speaker}
                            </Typography>
                            <Typography variant="caption" sx={{ ml: 'auto', opacity: 0.7 }}>
                              {new Date(message.timestamp).toLocaleTimeString()}
                            </Typography>
                          </Box>
                          <Typography variant="body2">
                            {message.content}
                          </Typography>
                        </Paper>
                      </Box>
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
          <Button variant="outlined" startIcon={<DownloadIcon />}>
            Export
          </Button>
        </DialogActions>
      </Dialog>

      {/* PDF Viewer Dialog */}
      <PDFViewer
        open={pdfViewerOpen}
        onClose={() => setPdfViewerOpen(false)}
        pdfData={currentPdfData}
        title="Assessment Report"
        patientName={currentPdfData?.metadata?.patientName}
      />
    </Box>
  );
};

export default ConversationHistory; 
