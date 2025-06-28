# Conversation History Guide

This guide explains how conversation history works in the Healthcare AI system and how to use it effectively.

## 📋 Overview

The Healthcare AI system now persists conversation history across browser sessions using localStorage. When you complete AI agent assessments, they are automatically saved and can be viewed in the Dashboard and Conversation History pages.

## 🔄 How It Works

### Starting a Conversation
1. **Select a Patient**: Use Patient Search or FHIR Data Loader to select a patient
2. **Go to Agent Console**: Navigate to the AI Agent Console
3. **Configure Assessment**: Choose assessment type (Comprehensive, Emergency, Medication Review)
4. **Start Assessment**: Click "START ASSESSMENT" to begin

### Conversation Flow
1. **System Message**: Initial message indicating assessment start
2. **Agent Collaboration**: Multiple AI agents participate in the assessment
3. **Real-time Updates**: Messages appear as agents complete their analysis
4. **Summary Generation**: When ended, a comprehensive summary is created

### Conversation Completion
When you click "End" or the assessment completes:
1. **Summary Generated**: Assessment summary with recommendations
2. **Saved to History**: Conversation added to localStorage
3. **Available in UI**: Visible in Dashboard and History pages

## 📊 Viewing History

### Dashboard - Recent Conversations
- Shows up to 3 most recent conversations
- Displays conversation type, patient name, and time
- "View All" button links to full history
- Empty state guidance when no conversations exist

### Conversation History Page
- Complete list of all conversations
- Search functionality by patient name or type
- Detailed view with full conversation and summary
- Export capabilities for documentation

## 💾 Data Persistence

### localStorage Storage
- Conversations saved to browser's localStorage
- Key: `healthcare-ai-conversation-history`
- Persists across browser sessions
- Automatically loaded on application start

### What's Stored
- **Conversation Metadata**: ID, patient info, type, participants
- **Full Message History**: All agent and user messages
- **Generated Summary**: Assessment results and recommendations
- **Timestamps**: Creation and completion times
- **Framework Used**: AutoGen or CrewAI

## 🏥 Assessment Types

### Comprehensive Assessment
- **Participants**: Primary Care Physician, Cardiologist, Clinical Pharmacist
- **Duration**: ~15-20 minutes simulation
- **Summary**: Complete evaluation with recommendations
- **Use Case**: Regular check-ups, complex cases

### Emergency Assessment
- **Participants**: Emergency Physician, specialists as needed
- **Duration**: ~5-10 minutes simulation  
- **Summary**: Rapid triage and immediate care recommendations
- **Use Case**: Urgent medical situations

### Medication Review
- **Participants**: Clinical Pharmacist, Primary Care Physician
- **Duration**: ~8-12 minutes simulation
- **Summary**: Drug interaction analysis and optimization
- **Use Case**: Medication management, safety reviews

## 📈 Summary Generation

Each completed conversation includes:

### Assessment Summary
- Type of assessment completed
- Number of participating agents
- Overall evaluation status
- Key clinical findings

### Recommendations
- **Comprehensive**: Medication monitoring, follow-ups, lifestyle
- **Emergency**: Immediate interventions, monitoring protocols
- **Medication**: Interaction checks, dosage adjustments, counseling

### Metadata
- Conversation duration
- Message count
- Completion timestamp
- Framework used (AutoGen/CrewAI)

## 🔍 Searching and Filtering

### Search Capabilities
- **Patient Name**: Find conversations by patient
- **Assessment Type**: Filter by comprehensive, emergency, medication review
- **Case-Insensitive**: Search is not case sensitive

### Sorting
- **Default**: Most recent first
- **Chronological**: Based on conversation timestamp
- **Auto-Update**: New conversations appear at top

## 📤 Export Features

### Available Exports (Planned)
- **PDF Reports**: Formatted conversation summaries
- **CSV Data**: Structured conversation metadata
- **JSON Archive**: Complete conversation data

## 🔧 Troubleshooting

### No Conversations Showing
1. **Complete a Conversation**: Start and finish an assessment
2. **Check Browser Storage**: Ensure localStorage is enabled
3. **Clear Cache**: Refresh browser if needed

### History Not Persisting
1. **Browser Settings**: Check if localStorage is disabled
2. **Incognito Mode**: Private browsing may not persist data
3. **Storage Quota**: Clear old browser data if storage is full

### Performance Issues
1. **Large History**: Older conversations may slow loading
2. **Clear History**: Manual localStorage cleanup if needed
3. **Browser Limits**: Consider export/backup for large datasets

## 🔒 Privacy and Security

### Data Storage
- **Local Only**: Data stored in browser localStorage
- **No Server Storage**: Conversations not sent to backend
- **Session Isolated**: Each browser instance has separate storage

### Data Retention
- **User Controlled**: Data persists until manually cleared
- **Browser Dependent**: Subject to browser storage policies
- **Manual Cleanup**: Users can clear history via browser settings

## 🎯 Best Practices

### For Healthcare Providers
1. **Complete Assessments**: Always end conversations properly for history
2. **Document Thoroughly**: Use detailed assessment types
3. **Regular Review**: Check conversation history for patient continuity
4. **Export Important**: Save critical assessments externally

### For System Administration
1. **Browser Compatibility**: Ensure localStorage support
2. **Storage Monitoring**: Advise on browser storage limits
3. **Backup Strategies**: Implement export workflows
4. **User Training**: Educate on conversation history features

## 🚀 Getting Started

1. **Load a Patient**: Use FHIR Data Loader with test patient ID (597179, 597217, etc.)
2. **Start Assessment**: Go to Agent Console and begin comprehensive assessment
3. **Let It Complete**: Watch the multi-agent simulation run
4. **End Conversation**: Click "End" to generate summary
5. **View History**: Check Dashboard or Conversation History page

The conversation history system provides a complete record of AI agent assessments, enabling better patient care continuity and clinical documentation. 