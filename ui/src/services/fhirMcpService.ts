/**
 * FHIR MCP Service for Healthcare AI UI
 * Provides methods to communicate with FHIR servers via MCP protocol
 */

import { fhirService } from './fhirService';

// Ensure MCP is enabled by default
fhirService.setUseMcp(true);

/**
 * MCP-first FHIR service instance
 * This wrapper ensures the FHIR service uses MCP protocol by default
 */
class FHIRMcpService {
  
  /**
   * Initialize MCP service with current settings
   */
  static initialize() {
    // Get current settings from localStorage
    const savedSettings = localStorage.getItem('healthcare-ai-settings');
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        
        // Apply MCP settings
        if (settings.useFhirMcp !== undefined) {
          fhirService.setUseMcp(settings.useFhirMcp);
        } else {
          // Default to MCP if no setting exists
          fhirService.setUseMcp(true);
        }
        
        if (settings.fhirMcpUrl) {
          // Ensure the URL ends with /rpc for proper endpoint
          let mcpUrl = settings.fhirMcpUrl;
          if (!mcpUrl.endsWith('/rpc')) {
            mcpUrl = mcpUrl.replace(/\/(sse|mcp)\/?$/, '/rpc');
            if (!mcpUrl.endsWith('/rpc')) {
              mcpUrl = mcpUrl.replace(/\/$/, '') + '/rpc';
            }
          }
          fhirService.updateMcpUrl(mcpUrl);
        }
        
        if (settings.fhirServerUrl) {
          fhirService.updateBaseUrl(settings.fhirServerUrl);
        }
        
        // Apply MCP configuration if available
        const mcpConfig: any = {};
        if (settings.mcpServerRequestTimeout !== undefined) mcpConfig.mcpServerRequestTimeout = settings.mcpServerRequestTimeout;
        if (settings.mcpRequestTimeoutResetOnProgress !== undefined) mcpConfig.mcpRequestTimeoutResetOnProgress = settings.mcpRequestTimeoutResetOnProgress;
        if (settings.mcpRequestMaxTotalTimeout !== undefined) mcpConfig.mcpRequestMaxTotalTimeout = settings.mcpRequestMaxTotalTimeout;
        if (settings.mcpProxyFullAddress !== undefined) mcpConfig.mcpProxyFullAddress = settings.mcpProxyFullAddress;
        if (settings.clientPort !== undefined) mcpConfig.clientPort = settings.clientPort;
        if (settings.serverPort !== undefined) mcpConfig.serverPort = settings.serverPort;
        
        if (Object.keys(mcpConfig).length > 0) {
          fhirService.updateMcpConfig(mcpConfig);
        }
      } catch (error) {
        console.warn('Failed to load MCP settings from localStorage:', error);
        // Fall back to MCP default
        fhirService.setUseMcp(true);
      }
    } else {
      // No settings saved, use MCP by default
      fhirService.setUseMcp(true);
    }
  }
  
  /**
   * Get the configured FHIR service instance
   */
  static getService() {
    return fhirService;
  }
  
  /**
   * Check if MCP is currently enabled
   */
  static isUsingMcp(): boolean {
    return fhirService.getUseMcp();
  }
  
  /**
   * Test the MCP connection
   */
  static async testMcpConnection() {
    // Ensure MCP is enabled for testing
    const originalUseMcp = fhirService.getUseMcp();
    fhirService.setUseMcp(true);
    
    try {
      const result = await fhirService.testConnection();
      return result;
    } finally {
      // Restore original setting
      fhirService.setUseMcp(originalUseMcp);
    }
  }
}

// Initialize on module load
FHIRMcpService.initialize();

export { FHIRMcpService };
export default fhirService; 