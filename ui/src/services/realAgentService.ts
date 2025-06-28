import { AgentExecution, AgentCommunication } from '../store/slices/agentCommunicationSlice';

export interface RealAgentConfig {
  framework: 'autogen' | 'crewai';
  apiKey: string;
  fhirServerUrl: string;
  modelName?: string;
  temperature?: number;
}

export interface ScenarioConfig {
  type: 'comprehensive' | 'emergency' | 'medication_review';
  patientId: string;
  patientName: string;
  chiefComplaint?: string;
  urgencyLevel?: 'routine' | 'urgent' | 'emergent' | 'stat';
  additionalContext?: string;
}

export interface LLMCommunication {
  id: string;
  agentId: string;
  agentName: string;
  framework: 'autogen' | 'crewai';
  provider: string;
  model: string;
  sessionStart: string;
  sessionEnd?: string;
  patientId?: string;
  scenarioType: string;
  messages: LLMMessage[];
  totalInputTokens: number;
  totalOutputTokens: number;
  totalTokens: number;
  costEstimate: number;
  responseTimeMs: number;
  finalResponse?: string;
  confidenceScore?: number;
  functionCallsMade: string[];
  toolsUsed: string[];
  errorMessage?: string;
}

export interface LLMMessage {
  id: string;
  timestamp: string;
  role: 'system' | 'user' | 'assistant' | 'function';
  content: string;
  tokens?: number;
  functionCall?: any;
  toolCalls?: any[];
}

export interface AgentResponse {
  success: boolean;
  communicationId: string;
  response: string;
  recommendations?: string[];
  confidence?: number;
  duration: number;
  tokensUsed: number;
  cost: number;
  error?: string;
}

export interface ScenarioExecution {
  id: string;
  scenarioType: string;
  framework: 'autogen' | 'crewai';
  patientId: string;
  patientName: string;
  startTime: string;
  endTime?: string;
  status: 'running' | 'completed' | 'failed';
  agents: AgentExecutionDetail[];
  communications: LLMCommunication[];
  summary?: string;
  totalCost: number;
  totalTokens: number;
  totalDuration: number;
}

export interface AgentExecutionDetail {
  agentId: string;
  agentName: string;
  specialty: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  input: string;
  output?: string;
  recommendations?: string[];
  confidence?: number;
  communicationIds: string[];
}

class RealAgentService {
  private baseUrl: string;
  private config: RealAgentConfig;
  private activeScenarios: Map<string, ScenarioExecution> = new Map();

  constructor(baseUrl: string = '', apiKey: string = '') {
    this.baseUrl = baseUrl || '';
    this.config = {
      framework: 'autogen',
      apiKey: apiKey,
      fhirServerUrl: 'https://hapi.fhir.org/baseR4',
      modelName: 'gpt-4',
      temperature: 0.1
    };
  }

  async updateConfig(config: Partial<RealAgentConfig>): Promise<void> {
    this.config = { ...this.config, ...config };
  }

  async startScenario(scenarioConfig: ScenarioConfig): Promise<ScenarioExecution> {
    const scenarioId = `scenario_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const scenario: ScenarioExecution = {
      id: scenarioId,
      scenarioType: scenarioConfig.type,
      framework: this.config.framework,
      patientId: scenarioConfig.patientId,
      patientName: scenarioConfig.patientName,
      startTime: new Date().toISOString(),
      status: 'running',
      agents: this.getAgentsForScenario(scenarioConfig.type),
      communications: [],
      totalCost: 0,
      totalTokens: 0,
      totalDuration: 0
    };

    this.activeScenarios.set(scenarioId, scenario);

    try {
      // Start scenario execution
      const body = {
        patient_id: scenarioConfig.patientId,
        scenario_config: scenarioConfig,
        agent_config: {
          model: this.config.modelName,
          temperature: this.config.temperature,
          track_communications: true
        }
      };

      const endpoint = this.config.framework === 'autogen' 
        ? `/api/autogen/${scenarioConfig.type}`
        : `/api/crewai/${scenarioConfig.type}`;

      const requestUrl = `${this.baseUrl}${endpoint}`;
      console.log(`[RealAgentService] Starting scenario. Requesting URL: ${requestUrl}`);

      const response = await fetch(requestUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[RealAgentService] Raw error response:', errorText);
        try {
            const errorBody = JSON.parse(errorText);
            console.error('[RealAgentService] Parsed error body:', JSON.stringify(errorBody, null, 2));
            const detail = errorBody.detail || 'Unknown validation error';
            throw new Error(`Agent service request failed: ${response.status} - ${JSON.stringify(detail)}`);
        } catch (e) {
            throw new Error(`Agent service request failed: ${response.status} - ${errorText}`);
        }
      }

      const result = await response.json();
      
      // Update scenario with results
      scenario.status = 'completed';
      scenario.endTime = new Date().toISOString();
      scenario.communications = result.communications || [];
      scenario.summary = result.summary;
      
      // Update agent details
      scenario.agents.forEach(agent => {
        const agentResult = result.agent_results?.find((r: any) => r.agent_id === agent.agentId);
        if (agentResult) {
          agent.status = 'completed';
          agent.endTime = new Date().toISOString();
          agent.output = agentResult.output;
          agent.recommendations = agentResult.recommendations;
          agent.confidence = agentResult.confidence;
          agent.communicationIds = agentResult.communication_ids || [];
        }
      });

      // Calculate totals
      scenario.totalCost = scenario.communications.reduce((sum, comm) => sum + comm.costEstimate, 0);
      scenario.totalTokens = scenario.communications.reduce((sum, comm) => sum + comm.totalTokens, 0);
      scenario.totalDuration = scenario.communications.reduce((sum, comm) => sum + comm.responseTimeMs, 0);

      return scenario;

    } catch (error) {
      scenario.status = 'failed';
      scenario.endTime = new Date().toISOString();
      // Ensure we don't re-wrap the error
      if (error instanceof Error && error.message.startsWith('Agent service request failed')) {
        throw new Error(`Failed to execute scenario: ${error.message}`);
      }
      throw new Error(`Failed to execute scenario: ${error}`);
    }
  }

  async executeAgentTask(
    agentId: string,
    agentName: string,
    task: string,
    patientId?: string,
    context?: string
  ): Promise<AgentResponse> {
    const startTime = Date.now();

    try {
      const endpoint = this.config.framework === 'autogen' 
        ? '/api/autogen/execute-task'
        : '/api/crewai/execute-task';

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          agent_id: agentId,
          agent_name: agentName,
          task: task,
          patient_id: patientId,
          context: context,
          config: {
            model: this.config.modelName,
            temperature: this.config.temperature
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Agent task execution failed: ${response.status}`);
      }

      const result = await response.json();
      const duration = Date.now() - startTime;

      return {
        success: true,
        communicationId: result.communication_id,
        response: result.response,
        recommendations: result.recommendations,
        confidence: result.confidence,
        duration: duration,
        tokensUsed: result.tokens_used || 0,
        cost: result.cost_estimate || 0
      };

    } catch (error) {
      const duration = Date.now() - startTime;
      return {
        success: false,
        communicationId: '',
        response: '',
        duration: duration,
        tokensUsed: 0,
        cost: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async getCommunications(): Promise<LLMCommunication[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/communications`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch communications: ${response.status}`);
      }

      const data = await response.json();
      
      // Handle both old array format and new object format with enhanced data
      if (Array.isArray(data)) {
        return data;
      } else if (data.communications && Array.isArray(data.communications)) {
        return data.communications;
      } else {
        console.warn('Unexpected communications response format:', data);
        return [];
      }
    } catch (error) {
      console.error('Failed to fetch communications:', error);
      return [];
    }
  }

  async getCommunicationStats(): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/communications/stats`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch communication stats: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to fetch communication stats:', error);
      return {};
    }
  }

  async getScenario(scenarioId: string): Promise<ScenarioExecution | null> {
    return this.activeScenarios.get(scenarioId) || null;
  }

  async getActiveScenarios(): Promise<ScenarioExecution[]> {
    return Array.from(this.activeScenarios.values())
      .filter(scenario => scenario.status === 'running');
  }

  async getAllScenarios(): Promise<ScenarioExecution[]> {
    return Array.from(this.activeScenarios.values());
  }

  async sendMessage(request: {
    message: string;
    framework: 'autogen' | 'crewai';
    conversationMode: string;
    patientId?: string;
    additionalContext?: any;
  }): Promise<{ success: boolean; data?: any; error?: string }> {
    try {
      // Handle PDF generation request
      if (request.additionalContext?.generatePDF) {
        const pdfRequest = {
          patient_id: request.patientId,
          assessment_type: request.conversationMode,
          assessment_data: request.additionalContext.assessmentData,
          conversation_data: request.additionalContext.conversationData,
          filename: request.additionalContext.filename
        };

        const pdfEndpoint = request.framework === 'autogen' 
                  ? `/api/autogen/generate-pdf`
                  : `/api/crewai/generate-pdf`;

        const response = await fetch(pdfEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.config.apiKey}`
          },
          body: JSON.stringify(pdfRequest)
        });

        if (!response.ok) {
          throw new Error(`PDF generation failed: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
          return {
            success: true,
            data: {
              pdfPath: result.pdfPath,
              filename: result.filename,
              size: result.size
            }
          };
        } else {
          return {
            success: false,
            error: result.error || 'PDF generation failed'
          };
        }
      }

      // Handle regular message requests
      const endpoint = request.framework === 'autogen'
        ? '/api/autogen/message'
        : '/api/crewai/message';

      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          message: request.message,
          patient_id: request.patientId,
          conversation_mode: request.conversationMode,
          context: request.additionalContext
        })
      });

      if (!response.ok) {
        throw new Error(`Message request failed: ${response.status}`);
      }

      const result = await response.json();
      
      return {
        success: true,
        data: result
      };

    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  private getAgentsForScenario(scenarioType: string): AgentExecutionDetail[] {
    const baseAgents = [
      {
        agentId: 'pcp-1',
        agentName: 'Primary Care Physician',
        specialty: 'Internal Medicine',
        status: 'pending' as const,
        input: `${scenarioType} assessment initiated`,
        communicationIds: []
      },
      {
        agentId: 'nurse-1',
        agentName: 'Nurse Care Coordinator',
        specialty: 'Nursing',
        status: 'pending' as const,
        input: 'Care coordination and patient education',
        communicationIds: []
      }
    ];

    switch (scenarioType) {
      case 'comprehensive':
        return [
          ...baseAgents,
          {
            agentId: 'card-1',
            agentName: 'Cardiologist',
            specialty: 'Cardiology',
            status: 'pending' as const,
            input: 'Cardiovascular risk assessment',
            communicationIds: []
          },
          {
            agentId: 'pharm-1',
            agentName: 'Clinical Pharmacist',
            specialty: 'Pharmacy',
            status: 'pending' as const,
            input: 'Medication review and optimization',
            communicationIds: []
          }
        ];

      case 'emergency':
        return [
          {
            agentId: 'emergency-1',
            agentName: 'Emergency Physician',
            specialty: 'Emergency Medicine',
            status: 'pending' as const,
            input: 'Emergency triage and stabilization',
            communicationIds: []
          },
          ...baseAgents
        ];

      case 'medication_review':
        return [
          {
            agentId: 'pharm-1',
            agentName: 'Clinical Pharmacist',
            specialty: 'Pharmacy',
            status: 'pending' as const,
            input: 'Comprehensive medication review',
            communicationIds: []
          },
          baseAgents[0] // PCP only
        ];

      default:
        return baseAgents;
    }
  }

  // Convert to format expected by Redux store
  convertToAgentExecution(
    agentDetail: AgentExecutionDetail,
    scenarioExecution: ScenarioExecution
  ): Omit<AgentExecution, 'id'> {
    return {
      agentId: agentDetail.agentId,
      agentName: agentDetail.agentName,
      agentSpecialty: agentDetail.specialty,
      executionType: this.getExecutionType(scenarioExecution.scenarioType),
      status: this.mapStatus(agentDetail.status),
      startTime: agentDetail.startTime || scenarioExecution.startTime,
      endTime: agentDetail.endTime,
      duration: agentDetail.endTime && agentDetail.startTime 
        ? Math.floor((new Date(agentDetail.endTime).getTime() - new Date(agentDetail.startTime).getTime()) / 1000)
        : undefined,
      patientId: scenarioExecution.patientId,
      patientName: scenarioExecution.patientName,
      inputData: {
        query: agentDetail.input,
        context: `${scenarioExecution.scenarioType} scenario`,
        patientData: {
          id: scenarioExecution.patientId,
          name: scenarioExecution.patientName
        }
      },
      outputData: agentDetail.output ? {
        result: agentDetail.output,
        recommendations: agentDetail.recommendations,
        confidence: agentDetail.confidence
      } : undefined,
      framework: scenarioExecution.framework,
      tokens: this.calculateTokensForAgent(agentDetail.communicationIds, scenarioExecution.communications),
      cost: this.calculateCostForAgent(agentDetail.communicationIds, scenarioExecution.communications)
    };
  }

  convertToAgentCommunication(
    llmComm: LLMCommunication,
    scenarioExecution: ScenarioExecution
  ): Omit<AgentCommunication, 'id'> {
    return {
      timestamp: llmComm.sessionStart,
      fromAgentId: llmComm.agentId,
      fromAgentName: llmComm.agentName,
      communicationType: 'request',
      message: llmComm.finalResponse || 'LLM communication in progress',
      context: `${scenarioExecution.scenarioType} scenario - ${llmComm.model}`,
      patientId: scenarioExecution.patientId,
      priority: 'medium',
      status: llmComm.sessionEnd ? 'processed' : 'sent'
    };
  }

  private getExecutionType(scenarioType: string): 'assessment' | 'analysis' | 'recommendation' | 'coordination' | 'query' {
    switch (scenarioType) {
      case 'comprehensive': return 'assessment';
      case 'emergency': return 'assessment';
      case 'medication_review': return 'analysis';
      default: return 'query';
    }
  }

  private mapStatus(status: string): 'running' | 'completed' | 'failed' | 'pending' {
    switch (status) {
      case 'pending': return 'pending';
      case 'running': return 'running';
      case 'completed': return 'completed';
      case 'failed': return 'failed';
      default: return 'pending';
    }
  }

  private calculateTokensForAgent(communicationIds: string[], communications: LLMCommunication[]) {
    const agentComms = communications.filter(comm => communicationIds.indexOf(comm.id) !== -1);
    const totalTokens = agentComms.reduce((sum, comm) => sum + comm.totalTokens, 0);
    const inputTokens = agentComms.reduce((sum, comm) => sum + comm.totalInputTokens, 0);
    const outputTokens = agentComms.reduce((sum, comm) => sum + comm.totalOutputTokens, 0);

    return totalTokens > 0 ? { input: inputTokens, output: outputTokens, total: totalTokens } : undefined;
  }

  private calculateCostForAgent(communicationIds: string[], communications: LLMCommunication[]) {
    const agentComms = communications.filter(comm => communicationIds.indexOf(comm.id) !== -1);
    return agentComms.reduce((sum, comm) => sum + comm.costEstimate, 0);
  }
}

export const realAgentService = new RealAgentService(); 