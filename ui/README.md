# Healthcare AI Agents UI

A modern React-based user interface for interacting with FHIR-integrated healthcare AI agents using both Microsoft Autogen and CrewAI frameworks.

## Features

### 🏥 Patient Management
- **Patient Search**: Search and select patients from FHIR servers
- **Patient Details**: View comprehensive patient summaries including conditions, medications, vital signs, and allergies
- **Recent Patients**: Quick access to recently viewed patients

### 🤖 AI Agent Interaction
- **Multi-Framework Support**: Switch between Microsoft Autogen and CrewAI frameworks
- **Specialized Agents**: 
  - Primary Care Physician
  - Cardiologist  
  - Clinical Pharmacist
  - Nurse Care Coordinator
- **Real-time Conversations**: Chat interface with multiple agents simultaneously
- **Assessment Types**: Comprehensive, Emergency, and Medication Review assessments

### 📊 Dashboard & Analytics
- **System Overview**: Real-time status of agents, response times, and utilization
- **Performance Metrics**: Agent performance charts and analytics
- **Activity Feed**: Recent assessments and alerts

### 💬 Conversation Management
- **Live Chat**: Real-time conversation with AI agents
- **Conversation History**: Review past assessments and decisions
- **Export Functionality**: Export conversations and reports

### ⚙️ Configuration
- **FHIR Integration**: Configure FHIR server connections
- **Agent Settings**: Customize agent behavior and specialties
- **Security**: Session management and data retention settings
- **Notifications**: Configure alerts and notifications

## Technology Stack

- **Frontend**: React 18 with TypeScript
- **UI Framework**: Material-UI (MUI) v5
- **State Management**: Redux Toolkit with RTK Query
- **Routing**: React Router v6
- **Charts**: Recharts
- **Real-time**: Socket.IO client
- **Build Tool**: Create React App

## Getting Started

### Prerequisites
- Node.js 16 or higher
- npm or yarn
- Running FHIR agent backends (Autogen and/or CrewAI)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
Create a `.env` file in the ui directory:
```env
REACT_APP_AUTOGEN_API_URL=http://localhost:8001
REACT_APP_CREWAI_API_URL=http://localhost:8000
REACT_APP_FHIR_SERVER_URL=https://hapi.fhir.org/baseR4/
```

3. Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`

### Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.

## Usage Guide

### 1. Patient Selection
1. Navigate to "Patient Search" in the sidebar
2. Search for patients by name or ID
3. Select a patient to view their details
4. Click "Start AI Assessment" to begin

### 2. Starting an Assessment
1. Go to "Agent Console"
2. Select the framework (Autogen or CrewAI)
3. Choose assessment type:
   - **Comprehensive**: Full patient evaluation
   - **Emergency**: Rapid triage assessment
   - **Medication Review**: Focus on drug interactions
4. Click "Start Assessment"

### 3. Interacting with Agents
1. Type questions or requests in the chat interface
2. Agents will respond based on their specialties
3. Review recommendations and clinical insights
4. End the conversation when complete

### 4. Reviewing History
1. Visit "Conversation History"
2. Browse past assessments and conversations
3. View summaries and recommendations
4. Export reports as needed

## API Integration

The UI integrates with two backend services:

### Autogen Service (Port 8001)
- `/conversation/comprehensive` - Start comprehensive assessment
- `/conversation/emergency` - Start emergency assessment  
- `/conversation/medication-review` - Start medication review
- `/patient/{id}/summary` - Get patient summary

### CrewAI Service (Port 8000)
- `/assessment/comprehensive` - Run comprehensive assessment
- `/assessment/emergency` - Run emergency assessment
- `/patient/{id}/summary` - Get patient summary

## Architecture

```
ui/
├── src/
│   ├── components/         # Reusable UI components
│   │   └── Layout/        # Header, Sidebar, etc.
│   │   └── components/    # Additional components
│   │   └── pages/         # Main application pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── PatientSearch.tsx
│   │   │   ├── AgentConsole.tsx
│   │   │   ├── ConversationHistory.tsx
│   │   │   └── Settings.tsx
│   │   ├── store/         # Redux store configuration
│   │   │   ├── api/       # API slice with RTK Query
│   │   │   └── slices/    # State slices
│   │   ├── App.tsx        # Main app component
│   │   └── index.tsx      # Entry point
│   ├── public/            # Static assets
│   └── package.json       # Dependencies and scripts
```

## Key Components

### AgentConsole
The main interface for interacting with AI agents:
- Framework selection (Autogen/CrewAI)
- Assessment type configuration
- Real-time chat interface
- Agent status monitoring

### Dashboard
System overview and analytics:
- Agent performance metrics
- System status indicators
- Recent activity feed
- Quick action buttons

### PatientSearch
Patient discovery and selection:
- FHIR server integration
- Patient search functionality
- Patient detail display
- Recent patients list

## Customization

### Adding New Agent Types
1. Update `agentSlice.ts` to include new agent definitions
2. Add agent-specific UI components
3. Configure backend integration in `apiSlice.ts`

### Styling Customization
- Modify the theme in `index.tsx`
- Customize component styles using MUI's `sx` prop
- Add custom CSS for specific requirements

## Development

### Running Tests
```bash
npm test
```

### Code Quality
```bash
npm run lint
npm run format
```

### Type Checking
```bash
npm run type-check
```

## Deployment

### Docker Deployment
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY build/ ./build/
EXPOSE 3000
CMD ["npx", "serve", "-s", "build", "-l", "3000"]
```

### Environment Configuration
Configure these environment variables for production:
- `REACT_APP_AUTOGEN_API_URL`
- `REACT_APP_CREWAI_API_URL`
- `REACT_APP_FHIR_SERVER_URL`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security Considerations

- All API communications use HTTPS in production
- FHIR data is handled according to HIPAA guidelines
- Session tokens are stored securely
- Audit logging tracks all user activities

## Support

For issues and questions:
1. Check the documentation
2. Review existing GitHub issues
3. Create a new issue with detailed information

## License

This project is licensed under the MIT License - see the LICENSE file for details. 