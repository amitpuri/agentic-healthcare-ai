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
  PictureAsPdf as PdfIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store/store';
import { setFramework, setConversationMode, updateAgentStatus } from '../store/slices/agentSlice';
import { clearCurrentPatient, setCurrentPatient } from '../store/slices/patientSlice';
import { useNavigate } from 'react-router-dom';
import { startConversation, addMessage, endConversation, updateConversationStatus, setConnected, setTypingIndicator, addPDFReport } from '../store/slices/conversationSlice';
import { addExecution, updateExecution, addCommunication } from '../store/slices/agentCommunicationSlice';
import { pdfService, PDFGenerationRequest, PDFResult } from '../services/pdfService';
import PDFViewer from '../components/PDFViewer';

const AgentConsole: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { selectedFramework, activeAgents, conversationMode, isLoading } = useSelector((state: RootState) => state.agents);
  const { activeConversation, isConnected, typingIndicator } = useSelector((state: RootState) => state.conversations);
  const { currentPatient } = useSelector((state: RootState) => state.patients);

  const [userInput, setUserInput] = useState('');
  const [selectedAssessmentType, setSelectedAssessmentType] = useState<'comprehensive' | 'emergency' | 'medication_review'>('comprehensive');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [urgencyLevel, setUrgencyLevel] = useState('routine');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const assessmentTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // PDF-related state
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);
  const [currentPdfData, setCurrentPdfData] = useState<PDFResult | null>(null);
  const [pdfGenerating, setPdfGenerating] = useState(false);

  // Function to load patient from FHIR server by ID (via MCP)
  const loadPatientFromFHIR = async (patientId: string) => {
    try {
      const { FHIRMcpService } = await import('../services/fhirMcpService');
      const fhirService = FHIRMcpService.getService();
      const comprehensivePatientData = await fhirService.getComprehensivePatientData(patientId);
      dispatch(setCurrentPatient(comprehensivePatientData));
    } catch (error) {
      console.error('Failed to load patient from FHIR via MCP:', error);
      alert(`Failed to load patient ${patientId}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Function to generate PDF assessment report
  const generateAssessmentPDF = async (assessmentType: string, patientName: string) => {
    if (!activeConversation || !currentPatient) {
      console.error('No active conversation or patient data for PDF generation');
      return;
    }

    setPdfGenerating(true);

    try {
      // Generate assessment summary from conversation data
      const assessmentSummary = pdfService.generateAssessmentSummary(
        activeConversation,
        assessmentType
      );

      // Create PDF generation request
      const pdfRequest: PDFGenerationRequest = {
        patientId: currentPatient.patient_id,
        assessmentType: assessmentType as 'comprehensive' | 'emergency' | 'medication_review',
        assessmentData: {
          patientName,
          patientId: currentPatient.patient_id,
          assessmentSummary,
          patientData: currentPatient,
        },
        conversationData: activeConversation,
        filename: `${assessmentType}_assessment_${currentPatient.patient_id}_${new Date().toISOString().split('T')[0]}.pdf`
      };

      // Generate PDF via AI agent
      const pdfResult = await pdfService.generateAssessmentReport(pdfRequest);

      if (pdfResult.success && pdfResult.pdfUrl) {
        // Add PDF to conversation
        const pdfInfo = {
          filename: pdfResult.filename || pdfRequest.filename || 'assessment_report.pdf',
          pdfUrl: pdfResult.pdfUrl,
          generatedAt: new Date().toISOString(),
          assessmentType,
          patientName,
          size: pdfResult.metadata?.size || 0
        };

        dispatch(addPDFReport(pdfInfo));

        // Show success message with PDF preview option
        const pdfMessage = {
          id: `msg_${Date.now()}`,
          speaker: 'System',
          role: 'assistant' as const,
          content: `📄 Assessment PDF report generated successfully! The comprehensive ${assessmentType} assessment for ${patientName} has been saved.`,
          timestamp: new Date().toISOString(),
        };
        dispatch(addMessage(pdfMessage));

        // Set PDF data for viewing and auto-open viewer
        setCurrentPdfData(pdfResult);
        setPdfViewerOpen(true);

      } else {
        throw new Error(pdfResult.error || 'Failed to generate PDF report');
      }

    } catch (error) {
      console.error('PDF generation failed:', error);
      
      const errorMessage = {
        id: `msg_${Date.now()}`,
        speaker: 'System',
        role: 'assistant' as const,
        content: `❌ Failed to generate PDF report: ${error instanceof Error ? error.message : 'Unknown error'}. You can try generating the report again from the conversation history.`,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(errorMessage));
    } finally {
      setPdfGenerating(false);
    }
  };

  // Helper functions for agent execution tracking
  const startAgentExecution = (agentName: string, agentId: string, executionType: string, query: string, context?: string) => {
    const execution = {
      agentId,
      agentName,
      agentSpecialty: getAgentSpecialty(agentId),
      executionType: executionType as 'assessment' | 'analysis' | 'recommendation' | 'coordination' | 'query',
      status: 'running' as const,
      startTime: new Date().toISOString(),
      patientId: currentPatient?.patient_id,
      patientName: currentPatient?.name,
      inputData: {
        query,
        context,
        patientData: currentPatient ? {
          id: currentPatient.patient_id,
          name: currentPatient.name,
          conditions: currentPatient.conditions?.length || 0,
          medications: currentPatient.medications?.length || 0
        } : undefined
      },
      framework: selectedFramework
    };
    
    dispatch(addExecution(execution));
    return execution;
  };

  const completeAgentExecution = (executionId: string, result: string, recommendations?: string[], confidence?: number) => {
    const endTime = new Date().toISOString();
    const updates = {
      status: 'completed' as const,
      endTime,
      outputData: {
        result,
        recommendations,
        confidence,
        nextSteps: recommendations?.slice(0, 3) // First 3 recommendations as next steps
      },
      tokens: {
        input: Math.floor(Math.random() * 200) + 300, // Simulate token usage
        output: Math.floor(Math.random() * 150) + 200,
        total: 0
      },
      cost: 0,
      duration: 0
    };
    
    updates.tokens.total = updates.tokens.input + updates.tokens.output;
    updates.cost = updates.tokens.total * 0.00003; // Simulate cost calculation
    
    // Calculate duration if we have the execution
    const execution = { executions: [{ id: executionId, startTime: new Date(Date.now() - Math.random() * 300000).toISOString() }] };
    const startTime = new Date(execution.executions[0].startTime);
    updates.duration = Math.floor((new Date(endTime).getTime() - startTime.getTime()) / 1000);
    
    dispatch(updateExecution({ id: executionId, updates }));
  };

  const addAgentCommunication = (fromAgentId: string, fromAgentName: string, toAgentId?: string, toAgentName?: string, message?: string, type: string = 'request') => {
    const communication = {
      timestamp: new Date().toISOString(),
      fromAgentId,
      fromAgentName,
      toAgentId,
      toAgentName,
      communicationType: type as 'request' | 'response' | 'broadcast' | 'handoff' | 'collaboration',
      message: message || `Agent ${fromAgentName} is ${type === 'handoff' ? 'handing off to' : 'communicating with'} ${toAgentName || 'the team'}`,
      context: `Patient assessment for ${currentPatient?.name || 'current patient'}`,
      patientId: currentPatient?.patient_id,
      priority: 'medium' as const,
      status: 'sent' as const
    };
    
    dispatch(addCommunication(communication));
  };

  const getAgentSpecialty = (agentId: string) => {
    const agent = activeAgents.find(a => a.id === agentId);
    return agent?.specialty || 'General';
  };

  const getAgentIdByName = (agentName: string) => {
    const agentMap: { [key: string]: string } = {
      'Primary Care Physician': 'pcp-1',
      'Cardiologist': 'card-1',
      'Clinical Pharmacist': 'pharm-1',
      'Nurse Care Coordinator': 'nurse-1',
      'Emergency Physician': 'emergency-1'
    };
    return agentMap[agentName] || 'unknown';
  };

  // Comprehensive agent simulation system with execution tracking
  const simulateAgentAssessment = (assessmentType: string, patientName: string, framework: string) => {
    const agentWorkflow = getAgentWorkflow(assessmentType, patientName);
    let stepIndex = 0;
    const executionMap = new Map<string, any>(); // Track executions by agent name

    const executeNextStep = () => {
      if (stepIndex >= agentWorkflow.length || !activeConversation) {
        // Assessment complete - complete all remaining executions
        executionMap.forEach((execution, agentName) => {
          completeAgentExecution(
            execution.id,
            `${assessmentType} assessment completed`,
            [`Assessment completed for ${patientName}`, 'Follow-up scheduled', 'Documentation updated'],
            0.85 + Math.random() * 0.1
          );
        });

        dispatch(setTypingIndicator(null));
        
        const completionMessage = {
          id: `msg_${Date.now()}`,
          speaker: 'System',
          role: 'assistant' as const,
          content: `✅ ${assessmentType.charAt(0).toUpperCase() + assessmentType.slice(1)} assessment completed for ${patientName}. All agents have provided their recommendations.`,
          timestamp: new Date().toISOString(),
        };
        dispatch(addMessage(completionMessage));
        
        // Reset agent statuses to active
        activeAgents.forEach(agent => {
          dispatch(updateAgentStatus({ agentId: agent.id, status: 'active' }));
        });
        
        // Generate PDF assessment report
        generateAssessmentPDF(assessmentType, patientName);
        
        return;
      }

      const step = agentWorkflow[stepIndex];
      const agentId = getAgentIdByName(step.agent);
      
      // Start execution tracking for this agent if not already started
      if (!executionMap.has(step.agent)) {
        const execution = startAgentExecution(
          step.agent,
          agentId,
          (step as any).executionType || 'assessment',
          (step as any).query || `${assessmentType} assessment for ${patientName}`,
          (step as any).context
        );
        executionMap.set(step.agent, execution);
        
        // Update agent status to busy
        dispatch(updateAgentStatus({ agentId, status: 'busy', patientId: currentPatient?.patient_id }));
      }
      
      // Add communication if this is a handoff or collaboration
      if ((step as any).communicationType && stepIndex > 0) {
        const previousStep = agentWorkflow[stepIndex - 1];
        addAgentCommunication(
          getAgentIdByName(previousStep.agent),
          previousStep.agent,
          agentId,
          step.agent,
          (step as any).communicationMessage,
          (step as any).communicationType
        );
      }
      
      // Show typing indicator
      dispatch(setTypingIndicator(step.agent));
      
      setTimeout(() => {
        // Add agent message
        const agentMessage = {
          id: `msg_${Date.now()}`,
          speaker: step.agent,
          role: 'agent' as const,
          content: step.message,
          timestamp: new Date().toISOString(),
        };
        dispatch(addMessage(agentMessage));
        
        // Complete execution for this step if it has results
        if ((step as any).results) {
          const execution = executionMap.get(step.agent);
          if (execution) {
            completeAgentExecution(
              execution.id,
              (step as any).results.summary,
              (step as any).results.recommendations,
              (step as any).results.confidence
            );
          }
        }
        
        stepIndex++;
        
        // Schedule next step
        assessmentTimerRef.current = setTimeout(executeNextStep, (step as any).nextDelay || 3000);
      }, (step as any).typingDelay || 2000);
    };

    // Start the workflow
    setTimeout(executeNextStep, 2000);
  };

  const getAgentWorkflow = (assessmentType: string, patientName: string) => {
    const workflows = {
      comprehensive: [
        {
          agent: 'Primary Care Physician',
          message: `🔍 Initiating comprehensive assessment for ${patientName}. Reviewing patient history, vital signs, and current medications...`,
          typingDelay: 2000,
          nextDelay: 4000,
          executionType: 'assessment',
          query: `Comprehensive health assessment for ${patientName}`,
          context: 'Initial consultation and review',
        },
        {
          agent: 'Primary Care Physician',
          message: `📊 Patient data analysis complete. Key findings:\n• Age: 49 years, Male\n• Current conditions: Hypertension, Type 2 Diabetes\n• Medications: Metformin 500mg BID, Lisinopril 10mg daily\n• Allergies: Penicillin, Shellfish\n\nRecommending specialist consultations...`,
          typingDelay: 3000,
          nextDelay: 3000,
          executionType: 'assessment',
          query: `Primary care data analysis for ${patientName}`,
          context: 'Patient data review and specialist referral decision',
          results: {
            summary: 'Primary care assessment completed with specialist referrals recommended',
            recommendations: ['Schedule cardiology consultation', 'Monitor blood pressure', 'Continue current medications'],
            confidence: 0.92
          }
        },
        {
          agent: 'Cardiologist',
          message: `❤️ Cardiology assessment initiated. Analyzing cardiovascular risk factors...\n\nFindings:\n• Blood pressure: 132/84 mmHg (Stage 1 hypertension)\n• Current ACE inhibitor therapy appropriate\n• Recommend: ECG, lipid panel, and exercise stress test\n• Consider increasing Lisinopril to 15mg if BP remains elevated`,
          typingDelay: 2500,
          nextDelay: 4000,
          executionType: 'analysis',
          query: 'Cardiac risk assessment and management recommendations',
          context: 'Referral from primary care for cardiovascular evaluation',
          communicationType: 'request',
          communicationMessage: 'Requesting cardiac consultation for patient with elevated BP and family history',
          results: {
            summary: 'Moderate cardiac risk identified with management recommendations',
            recommendations: ['Start ACE inhibitor therapy', 'Cardiac stress test', 'Lifestyle modifications'],
            confidence: 0.87
          }
        },
        {
          agent: 'Clinical Pharmacist',
          message: `💊 Medication review in progress...\n\n✅ Current regimen analysis:\n• Metformin: Appropriate dose, no interactions\n• Lisinopril: Well-tolerated ACE inhibitor\n\n⚠️ Recommendations:\n• Monitor renal function quarterly\n• Consider adding statin therapy for cardiovascular protection\n• Patient education on hypoglycemia signs needed`,
          typingDelay: 2000,
          nextDelay: 3500,
          executionType: 'review',
          query: `Medication review for ${patientName}`,
          context: 'Comprehensive medication analysis and optimization'
        },
        {
          agent: 'Nurse Care Coordinator',
          message: `👩‍⚕️ Care coordination assessment:\n\n📋 Patient education needs:\n• Diabetes self-management training\n• Blood pressure monitoring technique\n• Medication adherence review\n\n📅 Follow-up schedule:\n• 2-week BP recheck\n• 3-month HbA1c and comprehensive metabolic panel\n• 6-month cardiology follow-up\n\nPatient demonstrates good understanding of care plan.`,
          typingDelay: 2200,
          nextDelay: 2000,
          executionType: 'coordination',
          query: `Care coordination for ${patientName}`,
          context: 'Patient education and follow-up planning'
        },
      ],
      emergency: [
        {
          agent: 'Emergency Physician',
          message: `🚨 EMERGENCY ASSESSMENT: Rapid triage initiated for ${patientName}`,
          typingDelay: 1000,
          nextDelay: 2000,
          executionType: 'assessment',
          query: `Emergency triage for ${patientName}`,
          context: 'Rapid emergency assessment and stabilization'
        },
        {
          agent: 'Emergency Physician',
          message: `⚡ Primary survey complete:\n• Airway: Clear\n• Breathing: 22/min, SpO2 96%\n• Circulation: HR 110, BP 85/55\n• Disability: Alert and oriented\n• Exposure: No obvious trauma\n\nInitiating secondary assessment...`,
          typingDelay: 1500,
          nextDelay: 3000,
          executionType: 'assessment',
          query: `Primary survey for ${patientName}`,
          context: 'ABCDE primary survey and vital signs assessment'
        },
        {
          agent: 'Nurse Care Coordinator',
          message: `🩺 Vital signs monitoring:\n• Temperature: 101.2°F\n• Blood pressure trending up: 95/60\n• IV access established\n• Labs sent: CBC, CMP, lactate, blood cultures\n\nRecommending fluid resuscitation protocol.`,
          typingDelay: 1200,
          nextDelay: 2500,
          executionType: 'coordination',
          query: `Emergency care coordination for ${patientName}`,
          context: 'Vital signs monitoring and emergency interventions'
        },
      ],
      medication_review: [
        {
          agent: 'Clinical Pharmacist',
          message: `💊 Comprehensive medication review for ${patientName} initiated...`,
          typingDelay: 1500,
          nextDelay: 3000,
          executionType: 'review',
          query: `Medication review for ${patientName}`,
          context: 'Comprehensive medication therapy review'
        },
        {
          agent: 'Clinical Pharmacist',
          message: `📋 Current medication analysis:\n\n✅ APPROPRIATE:\n• Metformin 500mg BID - First-line T2DM therapy\n• Lisinopril 10mg daily - ACE inhibitor for HTN\n\n⚠️ CONSIDERATIONS:\n• Drug interaction check: No significant interactions detected\n• Renal dosing: Current doses appropriate for eGFR >60\n• Adherence assessment needed`,
          typingDelay: 2500,
          nextDelay: 3500,
          executionType: 'analysis',
          query: `Medication analysis for ${patientName}`,
          context: 'Drug interaction and dosing appropriateness review'
        },
        {
          agent: 'Primary Care Physician',
          message: `👨‍⚕️ Clinical review of pharmacist recommendations:\n\nAGREE with current regimen. Additional considerations:\n• Add aspirin 81mg daily for cardioprotection\n• Consider metformin ER for improved tolerance\n• Schedule medication therapy management session\n\nNo immediate changes required. Continue current therapy.`,
          typingDelay: 2000,
          nextDelay: 2000,
          executionType: 'recommendation',
          query: `Clinical medication review for ${patientName}`,
          context: 'Provider review of pharmacist recommendations'
        },
      ],
    };

    return workflows[assessmentType as keyof typeof workflows] || workflows.comprehensive;
  };

  // Add connectivity check
  useEffect(() => {
    const checkConnectivity = async () => {
      try {
        const [crewaiResponse, autogenResponse] = await Promise.all([
          fetch('/api/crewai/health'),
          fetch('/api/autogen/health')
        ]);
        
        if (crewaiResponse.ok && autogenResponse.ok) {
          dispatch(setConnected(true));
        } else {
          dispatch(setConnected(false));
        }
      } catch (error) {
        dispatch(setConnected(false));
      }
    };

    // Check connectivity on mount
    checkConnectivity();
    
    // Check connectivity every 30 seconds
    const interval = setInterval(checkConnectivity, 30000);
    
    return () => clearInterval(interval);
  }, [dispatch]);

  // Cleanup assessment timer on unmount
  useEffect(() => {
    return () => {
      if (assessmentTimerRef.current) {
        clearTimeout(assessmentTimerRef.current);
      }
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeConversation?.messages]);

  const handleStartConversation = () => {
    if (!currentPatient) {
      alert('Please select a patient first');
      return;
    }

    const conversationData = {
      conversation_id: `conv_${Date.now()}`,
      patient_id: currentPatient.patient_id,
      patient_name: currentPatient.name,
      conversation_type: selectedAssessmentType,
      status: 'active' as const,
      participants: activeAgents.map(agent => agent.name),
      messages: [],
      timestamp: new Date().toISOString(),
      framework: selectedFramework,
    };

    dispatch(startConversation(conversationData));
    
    // Update agent statuses
    activeAgents.forEach(agent => {
      dispatch(updateAgentStatus({ agentId: agent.id, status: 'busy', patientId: currentPatient.patient_id }));
    });

    // Add initial system message
    const initialMessage = {
      id: `msg_${Date.now()}`,
      speaker: 'System',
      role: 'assistant' as const,
      content: `Starting ${selectedAssessmentType} assessment for patient ${currentPatient.name} using ${selectedFramework.toUpperCase()} framework.`,
      timestamp: new Date().toISOString(),
    };

    dispatch(addMessage(initialMessage));

    // Start the agent simulation workflow
    simulateAgentAssessment(selectedAssessmentType, currentPatient.name, selectedFramework);
  };

  const handleSendMessage = () => {
    if (!userInput.trim() || !activeConversation) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      speaker: 'Healthcare Provider',
      role: 'user' as const,
      content: userInput,
      timestamp: new Date().toISOString(),
    };

    dispatch(addMessage(userMessage));
    setUserInput('');

    // Simulate agent responses
    setTimeout(() => {
      const agentMessage = {
        id: `msg_${Date.now() + 1}`,
        speaker: 'Primary Care Physician',
        role: 'agent' as const,
        content: `I've reviewed the patient data. Based on the assessment, I recommend conducting a comprehensive evaluation focusing on the cardiovascular risk factors and medication interactions.`,
        timestamp: new Date().toISOString(),
      };
      dispatch(addMessage(agentMessage));
    }, 2000);
  };

  const handleEndConversation = () => {
    // Stop any running assessment simulation
    if (assessmentTimerRef.current) {
      clearTimeout(assessmentTimerRef.current);
      assessmentTimerRef.current = null;
    }
    
    // Generate conversation summary before ending
    if (activeConversation) {
      const summary = generateConversationSummary();
      dispatch(updateConversationStatus({ 
        status: 'completed', 
        summary 
      }));
    } else {
      dispatch(endConversation());
    }
    
    dispatch(setTypingIndicator(null));
    
    // Reset agent statuses
    activeAgents.forEach(agent => {
      dispatch(updateAgentStatus({ agentId: agent.id, status: 'idle' }));
    });
  };

  const generateConversationSummary = () => {
    if (!activeConversation) return null;

    const messages = activeConversation.messages;
    const agentMessages = messages.filter(msg => msg.role === 'agent');
    const assessmentType = activeConversation.conversation_type;
    
    // Generate summary based on assessment type and messages
    const summary = {
      assessment: generateAssessmentSummary(assessmentType, agentMessages),
      recommendations: generateRecommendations(assessmentType, agentMessages),
      participants: activeConversation.participants,
      messageCount: messages.length,
      duration: calculateConversationDuration(),
      completedAt: new Date().toISOString()
    };

    return summary;
  };

  const generateAssessmentSummary = (type: string, agentMessages: any[]) => {
    const typeDescriptions = {
      comprehensive: 'Comprehensive multi-agent assessment completed',
      emergency: 'Emergency assessment and triage completed',
      medication_review: 'Medication review and optimization completed'
    };

    const baseDescription = typeDescriptions[type as keyof typeof typeDescriptions] || 'Assessment completed';
    const agentCount = new Set(agentMessages.map(msg => msg.speaker)).size;
    
    return `${baseDescription}. ${agentCount} healthcare agents participated in the evaluation. Patient care recommendations have been generated based on collaborative analysis.`;
  };

  const generateRecommendations = (type: string, agentMessages: any[]) => {
    // Extract key recommendations based on assessment type
    const recommendations: string[] = [];
    
    switch (type) {
      case 'comprehensive':
        recommendations.push('Continue current medication regimen with regular monitoring');
        recommendations.push('Schedule follow-up appointment in 3 months');
        recommendations.push('Patient education on lifestyle modifications');
        break;
      case 'emergency':
        recommendations.push('Immediate medical intervention protocols initiated');
        recommendations.push('Continuous monitoring required');
        recommendations.push('Notify attending physician of assessment results');
        break;
      case 'medication_review':
        recommendations.push('Current medications reviewed for interactions');
        recommendations.push('Dosage adjustments may be needed based on renal function');
        recommendations.push('Patient counseling on medication adherence');
        break;
      default:
        recommendations.push('Follow standard care protocols');
        break;
    }

    return recommendations;
  };

  const calculateConversationDuration = () => {
    if (!activeConversation || activeConversation.messages.length === 0) return '0 minutes';
    
    const startTime = new Date(activeConversation.timestamp);
    const endTime = new Date();
    const durationMs = endTime.getTime() - startTime.getTime();
    const durationMinutes = Math.round(durationMs / 60000);
    
    return `${durationMinutes} minutes`;
  };



  const getAssessmentTypeInfo = (type: string) => {
    switch (type) {
      case 'comprehensive':
        return {
          icon: <LocalHospitalIcon />,
          color: 'primary',
          description: 'Complete patient assessment with all agents participating'
        };
      case 'emergency':
        return {
          icon: <EmergencyIcon />,
          color: 'error',
          description: 'Rapid triage and emergency assessment'
        };
      case 'medication_review':
        return {
          icon: <MedicationIcon />,
          color: 'info',
          description: 'Focus on medication interactions and optimization'
        };
      default:
        return {
          icon: <LocalHospitalIcon />,
          color: 'primary',
          description: 'Standard assessment'
        };
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        AI Agent Console
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
            Please select a patient from the Patient Search page. You can also use the FHIR Data Loader to import real patient data.
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Control Panel */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Framework Selection
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <Chip
                  label="Autogen"
                  clickable
                  color={selectedFramework === 'autogen' ? 'primary' : 'default'}
                  onClick={() => dispatch(setFramework('autogen'))}
                />
                <Chip
                  label="CrewAI"
                  clickable
                  color={selectedFramework === 'crewai' ? 'secondary' : 'default'}
                  onClick={() => dispatch(setFramework('crewai'))}
                />
              </Box>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={conversationMode === 'multi'}
                    onChange={(e) => dispatch(setConversationMode(e.target.checked ? 'multi' : 'single'))}
                  />
                }
                label="Multi-agent collaboration"
              />
            </CardContent>
          </Card>

          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Assessment Configuration
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Assessment Type</InputLabel>
                <Select
                  value={selectedAssessmentType}
                  label="Assessment Type"
                  onChange={(e) => setSelectedAssessmentType(e.target.value as any)}
                >
                  <MenuItem value="comprehensive">Comprehensive Assessment</MenuItem>
                  <MenuItem value="emergency">Emergency Assessment</MenuItem>
                  <MenuItem value="medication_review">Medication Review</MenuItem>
                </Select>
              </FormControl>

              {selectedAssessmentType === 'emergency' && (
                <TextField
                  fullWidth
                  label="Chief Complaint"
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  placeholder="e.g., Chest pain with shortness of breath"
                  sx={{ mb: 2 }}
                />
              )}

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Urgency Level</InputLabel>
                <Select
                  value={urgencyLevel}
                  label="Urgency Level"
                  onChange={(e) => setUrgencyLevel(e.target.value)}
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
                  startIcon={<PlayArrowIcon />}
                  onClick={handleStartConversation}
                  disabled={!currentPatient || !!activeConversation}
                  fullWidth
                  title={!currentPatient ? 'Please select a patient first' : 
                         activeConversation ? 'End current conversation first' : 
                         'Start AI assessment with selected patient'}
                >
                  {!currentPatient ? 'Select Patient First' : 
                   activeConversation ? 'Assessment Active' : 
                   'START ASSESSMENT'}
                </Button>
                {activeConversation && (
                  <Button
                    variant="outlined"
                    startIcon={<StopIcon />}
                    onClick={handleEndConversation}
                    color="error"
                  >
                    End
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>

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
                View Agent Communications
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Conversation Area */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ pb: 1 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">
                  AI Agent Conversation
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {isConnected && <Chip label="Connected" color="success" size="small" />}
                  {currentPatient && (
                    <Chip 
                      label={`Patient: ${currentPatient.name}`} 
                      color="info" 
                      size="small" 
                      icon={<PersonIcon />}
                    />
                  )}
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Box>
              </Box>
            </CardContent>

            <Divider />

            {/* Messages Area */}
            <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
              {!activeConversation ? (
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  height: '100%',
                  color: 'text.secondary' 
                }}>
                  <PsychologyIcon sx={{ fontSize: 64, mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No Active Conversation
                  </Typography>
                  <Typography variant="body2" textAlign="center">
                    Select a patient and start an assessment to begin collaborating with AI agents
                  </Typography>
                </Box>
              ) : (
                <Box>
                  {activeConversation.messages.map((message) => (
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
                  
                  {typingIndicator && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar sx={{ width: 24, height: 24, mr: 1 }}>
                        <SmartToyIcon fontSize="small" />
                      </Avatar>
                      <Typography variant="body2" color="text.secondary">
                        {typingIndicator} is typing...
                      </Typography>
                      <CircularProgress size={16} sx={{ ml: 1 }} />
                    </Box>
                  )}
                  
                  <div ref={messagesEndRef} />
                </Box>
              )}
            </Box>

            {/* Input Area */}
            {activeConversation && (
              <>
                <Divider />
                <Box sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      fullWidth
                      variant="outlined"
                      placeholder="Type your message to the AI agents..."
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      multiline
                      maxRows={3}
                    />
                    <Button
                      variant="contained"
                      endIcon={<SendIcon />}
                      onClick={handleSendMessage}
                      disabled={!userInput.trim() || isLoading}
                      sx={{ minWidth: 100 }}
                    >
                      Send
                    </Button>
                  </Box>
                </Box>
              </>
            )}
          </Card>

          {/* Assessment Info */}
          {selectedAssessmentType && (
            <Card sx={{ mt: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ bgcolor: `${getAssessmentTypeInfo(selectedAssessmentType).color}.main` }}>
                    {getAssessmentTypeInfo(selectedAssessmentType).icon}
                  </Avatar>
                  <Box>
                    <Typography variant="h6">
                      {selectedAssessmentType.replace('_', ' ').toUpperCase()}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {getAssessmentTypeInfo(selectedAssessmentType).description}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* PDF Viewer Dialog */}
      <PDFViewer
        open={pdfViewerOpen}
        onClose={() => setPdfViewerOpen(false)}
        pdfData={currentPdfData || undefined}
        title="Assessment Report"
        patientName={currentPatient?.name}
      />
    </Box>
  );
};

export default AgentConsole; 