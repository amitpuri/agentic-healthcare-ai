/**
 * FHIR Service for Healthcare AI UI
 * Provides methods to fetch real patient data from FHIR servers
 * Supports both direct FHIR calls and MCP protocol (Model Context Protocol)
 * Defaults to using MCP for enhanced security and standardized access
 */

interface FHIRPatient {
  id: string;
  name: Array<{
    given: string[];
    family: string;
  }>;
  birthDate: string;
  gender: string;
  identifier?: Array<{
    value: string;
    system?: string;
  }>;
  telecom?: Array<{
    system: string;
    value: string;
  }>;
  address?: Array<{
    line: string[];
    city: string;
    state: string;
    postalCode: string;
  }>;
}

interface FHIRCondition {
  id: string;
  code: {
    coding: Array<{
      code: string;
      display: string;
      system?: string;
    }>;
  };
  subject: {
    reference: string;
  };
  clinicalStatus?: {
    coding: Array<{
      code: string;
    }>;
  };
  verificationStatus?: {
    coding: Array<{
      code: string;
    }>;
  };
}

interface FHIRMedicationRequest {
  id: string;
  medicationCodeableConcept?: {
    coding: Array<{
      code: string;
      display: string;
    }>;
  };
  subject: {
    reference: string;
  };
  dosageInstruction?: Array<{
    text: string;
  }>;
  status: string;
}

interface FHIRObservation {
  id: string;
  code: {
    coding: Array<{
      code: string;
      display: string;
    }>;
  };
  subject: {
    reference: string;
  };
  valueQuantity?: {
    value: number;
    unit: string;
  };
  valueString?: string;
  effectiveDateTime?: string;
  status: string;
}

interface FHIRBundle {
  resourceType: string;
  entry?: Array<{
    resource: any;
  }>;
  total?: number;
}

class FHIRService {
  private proxyUrl: string;
  private mcpUrl: string;
  private fhirServerUrl: string;
  private timeout: number = 10000;
  private useMcp: boolean = true; // Default to MCP
  private mcpRequestId: number = 1;
  
  // MCP Inspector Configuration
  private mcpServerRequestTimeout: number = 10000;
  private mcpRequestTimeoutResetOnProgress: boolean = true;
  private mcpRequestMaxTotalTimeout: number = 60000;
  private mcpProxyFullAddress: string = 'localhost';
  private clientPort: number = 6274;
  private serverPort: number = 6277;

  constructor() {
    // Get network configuration
    const networkHost = process.env.REACT_APP_NETWORK_HOST || 'localhost';
    const networkProtocol = process.env.REACT_APP_NETWORK_PROTOCOL || 'http';
    
    // Get FHIR proxy URL from environment or generate from network config
    this.proxyUrl = process.env.REACT_APP_FHIR_PROXY_URL || `${networkProtocol}://${networkHost}:8003`;
    
    // Get FHIR MCP URL from environment or generate from network config  
    this.mcpUrl = process.env.REACT_APP_FHIR_MCP_URL || `${networkProtocol}://${networkHost}:8004`;
    
    // Get FHIR server URL from saved settings, environment, or use default
    const savedFhirUrl = localStorage.getItem('REACT_APP_FHIR_BASE_URL');
    this.fhirServerUrl = savedFhirUrl || process.env.REACT_APP_FHIR_BASE_URL || 'https://hapi.fhir.org/baseR4';
    
    // Check if MCP should be used (can be toggled in settings)
    // Default to true if not explicitly set to false
    const savedMcpSetting = localStorage.getItem('USE_FHIR_MCP');
    this.useMcp = savedMcpSetting ? savedMcpSetting === 'true' : true;
    
    // Load MCP Inspector configuration from environment or localStorage
    this.loadMcpConfig();
  }

  private loadMcpConfig() {
    // Load from localStorage (settings) first, then environment variables
    const savedSettings = localStorage.getItem('healthcare-ai-settings');
    let settings: any = {};
    
    if (savedSettings) {
      try {
        settings = JSON.parse(savedSettings);
      } catch (error) {
        console.warn('Failed to parse saved settings:', error);
      }
    }
    
    // MCP Inspector Configuration with fallbacks
    this.mcpServerRequestTimeout = settings.mcpServerRequestTimeout || 
      parseInt(process.env.REACT_APP_MCP_SERVER_REQUEST_TIMEOUT || '10000');
      
    this.mcpRequestTimeoutResetOnProgress = settings.mcpRequestTimeoutResetOnProgress !== undefined ? 
      settings.mcpRequestTimeoutResetOnProgress : 
      (process.env.REACT_APP_MCP_REQUEST_TIMEOUT_RESET_ON_PROGRESS === 'true');
      
    this.mcpRequestMaxTotalTimeout = settings.mcpRequestMaxTotalTimeout || 
      parseInt(process.env.REACT_APP_MCP_REQUEST_MAX_TOTAL_TIMEOUT || '60000');
      
    this.mcpProxyFullAddress = settings.mcpProxyFullAddress || 
      process.env.REACT_APP_MCP_PROXY_FULL_ADDRESS || 
      process.env.REACT_APP_NETWORK_HOST || 'localhost';
      
    this.clientPort = settings.clientPort || 
      parseInt(process.env.REACT_APP_CLIENT_PORT || '6274');
      
    this.serverPort = settings.serverPort || 
      parseInt(process.env.REACT_APP_SERVER_PORT || '6277');
      
    // Update main timeout to use MCP server request timeout
    this.timeout = this.mcpServerRequestTimeout;
  }

  /**
   * Update the FHIR base URL (used when settings are changed)
   */
  updateBaseUrl(newUrl: string) {
    this.fhirServerUrl = newUrl;
  }

  /**
   * Update the MCP URL (used when settings are changed)
   */
  updateMcpUrl(newUrl: string) {
    this.mcpUrl = newUrl;
  }

  /**
   * Toggle between MCP and direct FHIR communication
   */
  setUseMcp(useMcp: boolean) {
    this.useMcp = useMcp;
    localStorage.setItem('USE_FHIR_MCP', useMcp.toString());
  }

  /**
   * Get current MCP usage status
   */
  getUseMcp(): boolean {
    return this.useMcp;
  }

  /**
   * Get MCP configuration
   */
  getMcpConfig() {
    return {
      mcpServerRequestTimeout: this.mcpServerRequestTimeout,
      mcpRequestTimeoutResetOnProgress: this.mcpRequestTimeoutResetOnProgress,
      mcpRequestMaxTotalTimeout: this.mcpRequestMaxTotalTimeout,
      mcpProxyFullAddress: this.mcpProxyFullAddress,
      clientPort: this.clientPort,
      serverPort: this.serverPort,
    };
  }
  
  /**
   * Update MCP configuration
   */
  updateMcpConfig(config: Partial<{
    mcpServerRequestTimeout: number;
    mcpRequestTimeoutResetOnProgress: boolean;
    mcpRequestMaxTotalTimeout: number;
    mcpProxyFullAddress: string;
    clientPort: number;
    serverPort: number;
  }>) {
    if (config.mcpServerRequestTimeout !== undefined) {
      this.mcpServerRequestTimeout = config.mcpServerRequestTimeout;
      this.timeout = config.mcpServerRequestTimeout; // Update main timeout
    }
    if (config.mcpRequestTimeoutResetOnProgress !== undefined) {
      this.mcpRequestTimeoutResetOnProgress = config.mcpRequestTimeoutResetOnProgress;
    }
    if (config.mcpRequestMaxTotalTimeout !== undefined) {
      this.mcpRequestMaxTotalTimeout = config.mcpRequestMaxTotalTimeout;
    }
    if (config.mcpProxyFullAddress !== undefined) {
      this.mcpProxyFullAddress = config.mcpProxyFullAddress;
    }
    if (config.clientPort !== undefined) {
      this.clientPort = config.clientPort;
    }
    if (config.serverPort !== undefined) {
      this.serverPort = config.serverPort;
    }
  }

  private async makeRequest(endpoint: string, params?: Record<string, string>): Promise<any> {
    if (this.useMcp) {
      return this.makeMcpRequest(endpoint, params);
    } else {
      return this.makeProxyRequest(endpoint, params);
    }
  }

  private async makeProxyRequest(endpoint: string, params?: Record<string, string>): Promise<any> {
    // Use proxy URL with FHIR endpoint
    const url = new URL(`/fhir/${endpoint}`, this.proxyUrl);
    
    // Add fhir_url parameter to tell proxy which FHIR server to use
    url.searchParams.append('fhir_url', this.fhirServerUrl);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        throw new Error(`FHIR proxy request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('FHIR Service Error:', error);
      throw error;
    }
  }

  private async makeMcpRequest(endpoint: string, params?: Record<string, string>): Promise<any> {
    // Parse endpoint to determine FHIR operation
    const parts = endpoint.split('/');
    const resourceType = parts[0];
    const resourceId = parts[1];
    
    let method = 'search';
    let methodParams: any = {};
    
    if (resourceId) {
      method = 'read';
      methodParams = { type: resourceType, id: resourceId, format: "fhir" };
    } else if (params) {
      method = 'search';
      methodParams = { type: resourceType, searchParam: params, format: "fhir" };
    } else {
      method = 'search';
      methodParams = { type: resourceType, searchParam: {}, format: "fhir" };
    }
    
    return this.sendMcpRequest(method, methodParams);
  }

  private async sendMcpRequest(method: string, params: any): Promise<any> {
    const requestId = this.mcpRequestId++;
    const startTime = Date.now();
    let progressResetCount = 0;
    
    const mcpRequest = {
      jsonrpc: "2.0",
      id: requestId,
      method: `tools/call`,
      params: {
        name: method,
        arguments: params
      }
    };

    const controller = new AbortController();
    let timeoutId: NodeJS.Timeout | undefined;
    
    // Set up timeout with progress reset capability
    const setupTimeout = (timeoutMs: number) => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        controller.abort();
      }, timeoutMs);
    };
    
    // Initial timeout
    setupTimeout(this.mcpServerRequestTimeout);
    
    // Max total timeout
    const maxTimeoutId = setTimeout(() => {
      controller.abort();
    }, this.mcpRequestMaxTotalTimeout);

    try {
      const response = await fetch(this.mcpUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(mcpRequest),
        signal: controller.signal,
      });

      if (timeoutId) clearTimeout(timeoutId);
      clearTimeout(maxTimeoutId);

      if (!response.ok) {
        throw new Error(`MCP request failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(`MCP error: ${result.error.message || 'Unknown MCP error'}`);
      }
      
      // Reset timeout on progress if enabled and we're still within reasonable bounds
      const elapsed = Date.now() - startTime;
      if (this.mcpRequestTimeoutResetOnProgress && elapsed < this.mcpRequestMaxTotalTimeout / 2) {
        progressResetCount++;
      }
      
      return result.result || result;
      
    } catch (error) {
      if (timeoutId) clearTimeout(timeoutId);
      clearTimeout(maxTimeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        const elapsed = Date.now() - startTime;
        if (elapsed >= this.mcpRequestMaxTotalTimeout) {
          throw new Error(`MCP request exceeded maximum timeout (${this.mcpRequestMaxTotalTimeout}ms)`);
        } else {
          throw new Error(`MCP request timeout (${this.mcpServerRequestTimeout}ms)`);
        }
      }
      
      throw error;
    }
  }

  /**
   * Get patient by ID from FHIR server
   */
  async getPatient(patientId: string): Promise<any> {
    try {
      const patient = await this.makeRequest(`Patient/${patientId}`);
      return this.transformPatientData(patient);
    } catch (error) {
      console.error(`Failed to fetch patient ${patientId}:`, error);
      throw error;
    }
  }

  /**
   * Search for patients by name or identifier
   */
  async searchPatients(searchTerm: string): Promise<any[]> {
    try {
      const params: Record<string, string> = {};
      
      // Search by name or identifier
      if (searchTerm) {
        // Check if search term looks like a patient ID (numeric)
        if (/^\d+$/.test(searchTerm.trim())) {
          // Search by ID
          params._id = searchTerm.trim();
        } else {
          // Search by name
          params.name = searchTerm;
        }
      }

      const bundle: FHIRBundle = await this.makeRequest('Patient', params);
      
      if (!bundle.entry) {
        return [];
      }

      return bundle.entry
        .filter(entry => entry.resource?.resourceType === 'Patient')
        .map(entry => this.transformPatientData(entry.resource))
        .slice(0, 10); // Limit to 10 results
    } catch (error) {
      console.error('Failed to search patients:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive patient data including conditions, medications, and observations
   */
  async getComprehensivePatientData(patientId: string): Promise<any> {
    try {
      const [patient, conditions, medications, observations] = await Promise.all([
        this.getPatient(patientId),
        this.getPatientConditions(patientId),
        this.getPatientMedications(patientId),
        this.getPatientObservations(patientId),
      ]);

      return {
        ...patient,
        conditions,
        medications,
        vital_signs: this.extractVitalSigns(observations),
        allergies: this.extractAllergies(conditions),
        recent_visits: [], // This would require Encounter resources
        risk_scores: {
          cardiovascular: Math.random() * 0.5, // Placeholder - would calculate from real data
          diabetes: Math.random() * 0.3,
          fall_risk: Math.random() * 0.2,
        },
      };
    } catch (error) {
      console.error(`Failed to get comprehensive data for patient ${patientId}:`, error);
      throw error;
    }
  }

  /**
   * Get patient conditions
   */
  async getPatientConditions(patientId: string): Promise<any[]> {
    try {
      const bundle: FHIRBundle = await this.makeRequest('Condition', {
        patient: patientId,
        _sort: '-date',
      });

      if (!bundle.entry) {
        return [];
      }

      return bundle.entry
        .filter(entry => entry.resource?.resourceType === 'Condition')
        .map(entry => this.transformConditionData(entry.resource));
    } catch (error) {
      console.error(`Failed to fetch conditions for patient ${patientId}:`, error);
      return [];
    }
  }

  /**
   * Get patient medications
   */
  async getPatientMedications(patientId: string): Promise<any[]> {
    try {
      const bundle: FHIRBundle = await this.makeRequest('MedicationRequest', {
        patient: patientId,
        _sort: '-date',
      });

      if (!bundle.entry) {
        return [];
      }

      return bundle.entry
        .filter(entry => entry.resource?.resourceType === 'MedicationRequest')
        .map(entry => this.transformMedicationData(entry.resource));
    } catch (error) {
      console.error(`Failed to fetch medications for patient ${patientId}:`, error);
      return [];
    }
  }

  /**
   * Get patient observations (vital signs, lab results, etc.)
   */
  async getPatientObservations(patientId: string): Promise<any[]> {
    try {
      const bundle: FHIRBundle = await this.makeRequest('Observation', {
        patient: patientId,
        _sort: '-date',
        _count: '50',
      });

      if (!bundle.entry) {
        return [];
      }

      return bundle.entry
        .filter(entry => entry.resource?.resourceType === 'Observation')
        .map(entry => this.transformObservationData(entry.resource));
    } catch (error) {
      console.error(`Failed to fetch observations for patient ${patientId}:`, error);
      return [];
    }
  }

  /**
   * Transform FHIR Patient resource to our format
   */
  private transformPatientData(fhirPatient: FHIRPatient): any {
    const name = fhirPatient.name?.[0];
    const fullName = name ? `${name.given?.join(' ')} ${name.family}`.trim() : '';
    
    const phone = fhirPatient.telecom?.find(t => t.system === 'phone')?.value;
    const email = fhirPatient.telecom?.find(t => t.system === 'email')?.value;
    
    const address = fhirPatient.address?.[0];
    const addressString = address ? 
      `${address.line?.join(' ')}, ${address.city}, ${address.state} ${address.postalCode}`.trim() : 
      undefined;

    // Calculate age from birth date
    const birthDate = fhirPatient.birthDate;
    const age = birthDate ? Math.floor((Date.now() - new Date(birthDate).getTime()) / (365.25 * 24 * 60 * 60 * 1000)) : 0;

    return {
      patient_id: fhirPatient.id,
      name: fullName,
      birth_date: birthDate,
      gender: fhirPatient.gender,
      age,
      phone,
      email,
      address: addressString,
    };
  }

  /**
   * Transform FHIR Condition resource to our format
   */
  private transformConditionData(fhirCondition: FHIRCondition): any {
    const coding = fhirCondition.code?.coding?.[0];
    const isActive = fhirCondition.clinicalStatus?.coding?.[0]?.code === 'active';
    
    return {
      code: coding?.code,
      display: coding?.display || '',
      severity: isActive ? 'active' : 'inactive',
      system: coding?.system,
    };
  }

  /**
   * Transform FHIR MedicationRequest resource to our format
   */
  private transformMedicationData(fhirMedication: FHIRMedicationRequest): any {
    const coding = fhirMedication.medicationCodeableConcept?.coding?.[0];
    const dosage = fhirMedication.dosageInstruction?.[0]?.text;
    
    return {
      name: coding?.display || '',
      code: coding?.code,
      dosage: dosage || '',
      frequency: '',
      status: fhirMedication.status,
    };
  }

  /**
   * Transform FHIR Observation resource to our format
   */
  private transformObservationData(fhirObservation: FHIRObservation): any {
    const coding = fhirObservation.code?.coding?.[0];
    const value = fhirObservation.valueQuantity?.value || fhirObservation.valueString;
    const unit = fhirObservation.valueQuantity?.unit;
    
    return {
      code: coding?.code,
      display: coding?.display || '',
      value,
      unit,
      date: fhirObservation.effectiveDateTime,
      status: fhirObservation.status,
    };
  }

  /**
   * Extract vital signs from observations
   */
  private extractVitalSigns(observations: any[]): any {
    const vitalSigns: any = {};
    
    observations.forEach(obs => {
      switch (obs.code) {
        case '8480-6': // Systolic BP
          vitalSigns.systolic_bp = obs.value;
          break;
        case '8462-4': // Diastolic BP
          vitalSigns.diastolic_bp = obs.value;
          break;
        case '8867-4': // Heart rate
          vitalSigns.heart_rate = obs.value;
          break;
        case '8310-5': // Body temperature
          vitalSigns.temperature = obs.value;
          break;
        case '29463-7': // Body weight
          vitalSigns.weight = obs.value;
          break;
        case '8302-2': // Body height
          vitalSigns.height = obs.value;
          break;
      }
    });

    // Format blood pressure
    if (vitalSigns.systolic_bp && vitalSigns.diastolic_bp) {
      vitalSigns.blood_pressure = `${vitalSigns.systolic_bp}/${vitalSigns.diastolic_bp}`;
    }

    return vitalSigns;
  }

  /**
   * Extract allergies from conditions (simplified)
   */
  private extractAllergies(conditions: any[]): string[] {
    return conditions
      .filter(condition => condition.display?.toLowerCase().includes('allergy'))
      .map(condition => condition.display)
      .slice(0, 5); // Limit to 5 allergies
  }

  /**
   * Test FHIR server connection
   */
  async testConnection(): Promise<{ success: boolean; message: string; serverInfo?: any }> {
    try {
      if (this.useMcp) {
        // Test MCP server health first
        let healthData: any = {};
        // Extract base URL from MCP URL (remove /rpc suffix for health check)
        const baseUrl = this.mcpUrl.replace('/rpc', '');
        try {
          const healthResponse = await fetch(`${baseUrl}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(this.timeout),
          });
          
          if (!healthResponse.ok) {
            throw new Error(`MCP server not responding: ${healthResponse.status}`);
          }
          
          healthData = await healthResponse.json();
          console.log('MCP Server Health:', healthData);
        } catch (healthError) {
          throw new Error(`MCP server unavailable at ${baseUrl}/health: ${healthError instanceof Error ? healthError.message : 'Unknown error'}`);
        }

        // Test FHIR capabilities through MCP
        const capabilities = await this.sendMcpRequest('get_capabilities', {});
        
        const softwareName = capabilities?.software?.name || healthData?.service || 'FHIR Server via MCP';
        const fhirVersion = capabilities?.fhirVersion || 'R4';
        
        return {
          success: true,
          message: `Successfully connected to ${softwareName} (FHIR ${fhirVersion}) via MCP`,
          serverInfo: {
            method: 'MCP',
            mcpUrl: this.mcpUrl,
            fhirUrl: this.fhirServerUrl,
            software: softwareName,
            version: fhirVersion,
            capabilities: capabilities
          }
        };
      } else {
        // Use proxy's test connection endpoint
        const url = new URL('/fhir/test-connection', this.proxyUrl);
        url.searchParams.append('fhir_url', this.fhirServerUrl);
        
        const response = await fetch(url.toString(), {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(this.timeout),
        });

        if (!response.ok) {
          throw new Error(`Proxy connection test failed: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        return {
          ...result,
          serverInfo: {
            ...result.serverInfo,
            method: 'Proxy'
          }
        };
      }
    } catch (error) {
      const method = this.useMcp ? 'MCP' : 'Proxy';
      console.error(`FHIR ${method} connection test failed:`, error);
      return {
        success: false,
        message: `${method} connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }

  /**
   * Get available patient IDs (for testing purposes)
   */
  async getAvailablePatientIds(limit: number = 10): Promise<string[]> {
    try {
      const bundle: FHIRBundle = await this.makeRequest('Patient', {
        _count: limit.toString(),
        _elements: 'id',
      });

      if (!bundle.entry) {
        return [];
      }

      return bundle.entry
        .filter(entry => entry.resource?.resourceType === 'Patient')
        .map(entry => entry.resource.id)
        .filter(id => id);
    } catch (error) {
      console.error('Failed to get available patient IDs:', error);
      return [];
    }
  }
}

export const fhirService = new FHIRService();
export default fhirService; 
