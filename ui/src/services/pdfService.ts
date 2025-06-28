/**
 * PDF Service for Healthcare AI Assessment Reports
 * Handles PDF generation, display, and download functionality
 */

import { realAgentService } from './realAgentService';

export interface PDFGenerationRequest {
  patientId: string;
  assessmentData: any;
  conversationData: any;
  filename?: string;
  assessmentType: 'comprehensive' | 'emergency' | 'medication_review';
}

export interface PDFResult {
  success: boolean;
  pdfPath?: string;
  pdfUrl?: string;
  filename?: string;
  error?: string;
  metadata?: {
    patientId: string;
    patientName: string;
    assessmentType: string;
    generatedAt: string;
    size: number;
  };
}

class PDFService {
  private baseUrl: string;

  constructor() {
    // Get network configuration for dynamic URL generation
    const networkHost = process.env.REACT_APP_NETWORK_HOST || 'localhost';
    const networkProtocol = process.env.REACT_APP_NETWORK_PROTOCOL || 'http';
    
    this.baseUrl = process.env.REACT_APP_AUTOGEN_API_URL || `${networkProtocol}://${networkHost}:8001`;
  }

  /**
   * Generate PDF assessment report via AI agent
   */
  async generateAssessmentReport(request: PDFGenerationRequest): Promise<PDFResult> {
    try {
      // Use the real agent service to generate PDF
      const response = await realAgentService.sendMessage({
        message: `Generate comprehensive assessment PDF report for patient ${request.patientId}`,
        framework: 'autogen', // Default to AutoGen for PDF generation
        conversationMode: request.assessmentType,
        patientId: request.patientId,
        additionalContext: {
          assessmentData: request.assessmentData,
          conversationData: request.conversationData,
          generatePDF: true,
          filename: request.filename
        }
      });

      if (response.success && response.data?.pdfPath) {
        return {
          success: true,
          pdfPath: response.data.pdfPath,
          pdfUrl: this.convertPathToUrl(response.data.pdfPath),
          filename: response.data.filename || this.generateFilename(request),
          metadata: {
            patientId: request.patientId,
            patientName: request.assessmentData?.patientName || 'Unknown',
            assessmentType: request.assessmentType,
            generatedAt: new Date().toISOString(),
            size: response.data.size || 0
          }
        };
      }

      return {
        success: false,
        error: response.error || 'Failed to generate PDF report'
      };

    } catch (error) {
      console.error('PDF generation failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error during PDF generation'
      };
    }
  }

  /**
   * Download PDF file
   */
  async downloadPDF(pdfUrl: string, filename: string): Promise<boolean> {
    try {
      const response = await fetch(pdfUrl);
      if (!response.ok) {
        throw new Error(`Failed to download PDF: ${response.statusText}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      // Create download link
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('PDF download failed:', error);
      return false;
    }
  }

  /**
   * Preview PDF in new window/tab
   */
  previewPDF(pdfUrl: string): void {
    window.open(pdfUrl, '_blank', 'noopener,noreferrer');
  }

  /**
   * Get PDF blob for inline display
   */
  async getPDFBlob(pdfUrl: string): Promise<Blob | null> {
    try {
      const response = await fetch(pdfUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch PDF: ${response.statusText}`);
      }
      return await response.blob();
    } catch (error) {
      console.error('Failed to get PDF blob:', error);
      return null;
    }
  }

  /**
   * Check if PDF exists and is accessible
   */
  async verifyPDF(pdfUrl: string): Promise<boolean> {
    try {
      const response = await fetch(pdfUrl, { method: 'HEAD' });
      return response.ok;
    } catch (error) {
      console.error('PDF verification failed:', error);
      return false;
    }
  }

  /**
   * Get list of available PDF reports for a patient
   */
  async getPatientPDFReports(patientId: string): Promise<PDFResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/patient/${patientId}/pdf-reports`);
      if (!response.ok) {
        throw new Error(`Failed to fetch PDF reports: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.reports || [];
    } catch (error) {
      console.error('Failed to get patient PDF reports:', error);
      return [];
    }
  }

  /**
   * Convert server file path to downloadable URL
   */
  private convertPathToUrl(filePath: string): string {
    // Convert server file path to accessible URL
    if (filePath.startsWith('http')) {
      return filePath;
    }
    
    // Assume files are served from a static endpoint
    const filename = filePath.split('/').pop() || filePath;
    return `${this.baseUrl}/static/reports/${filename}`;
  }

  /**
   * Generate filename for PDF report
   */
  private generateFilename(request: PDFGenerationRequest): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
    const patientId = request.patientId.replace(/[^a-zA-Z0-9]/g, '_');
    return `assessment_report_${patientId}_${request.assessmentType}_${timestamp}.pdf`;
  }

  /**
   * Format file size for display
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Generate assessment summary for PDF
   */
  generateAssessmentSummary(conversationData: any, assessmentType: string): any {
    const messages = conversationData.messages || [];
    const agentMessages = messages.filter((msg: any) => msg.speaker !== 'User' && msg.speaker !== 'System');
    
    const summary = {
      assessmentType,
      timestamp: new Date().toISOString(),
      totalMessages: messages.length,
      agentParticipants: [...new Set(agentMessages.map((msg: any) => msg.speaker))],
      duration: this.calculateDuration(conversationData.startTime, conversationData.endTime),
      keyFindings: this.extractKeyFindings(agentMessages),
      recommendations: this.extractRecommendations(agentMessages),
      riskFactors: this.extractRiskFactors(agentMessages),
      followUpActions: this.extractFollowUpActions(agentMessages)
    };

    return summary;
  }

  private calculateDuration(startTime?: string, endTime?: string): string {
    if (!startTime || !endTime) return 'Unknown';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end.getTime() - start.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 60) {
      return `${diffMins} minutes`;
    } else {
      const hours = Math.floor(diffMins / 60);
      const mins = diffMins % 60;
      return `${hours}h ${mins}m`;
    }
  }

  private extractKeyFindings(messages: any[]): string[] {
    const findings: string[] = [];
    
    messages.forEach(msg => {
      const content = msg.content.toLowerCase();
      if (content.includes('finding') || content.includes('diagnosis') || content.includes('condition')) {
        // Extract potential findings
        const sentences = msg.content.split('.').filter((s: string) => s.trim().length > 10);
        findings.push(...sentences.slice(0, 2).map((s: string) => s.trim()));
      }
    });
    
    return findings.slice(0, 5); // Limit to top 5 findings
  }

  private extractRecommendations(messages: any[]): string[] {
    const recommendations: string[] = [];
    
    messages.forEach(msg => {
      const content = msg.content.toLowerCase();
      if (content.includes('recommend') || content.includes('suggest') || content.includes('should')) {
        const sentences = msg.content.split('.').filter((s: string) => s.trim().length > 10);
        recommendations.push(...sentences.slice(0, 2).map((s: string) => s.trim()));
      }
    });
    
    return recommendations.slice(0, 5); // Limit to top 5 recommendations
  }

  private extractRiskFactors(messages: any[]): string[] {
    const riskFactors: string[] = [];
    
    messages.forEach(msg => {
      const content = msg.content.toLowerCase();
      if (content.includes('risk') || content.includes('concern') || content.includes('warning')) {
        const sentences = msg.content.split('.').filter((s: string) => s.trim().length > 10);
        riskFactors.push(...sentences.slice(0, 1).map((s: string) => s.trim()));
      }
    });
    
    return riskFactors.slice(0, 3); // Limit to top 3 risk factors
  }

  private extractFollowUpActions(messages: any[]): string[] {
    const actions: string[] = [];
    
    messages.forEach(msg => {
      const content = msg.content.toLowerCase();
      if (content.includes('follow') || content.includes('monitor') || content.includes('schedule')) {
        const sentences = msg.content.split('.').filter((s: string) => s.trim().length > 10);
        actions.push(...sentences.slice(0, 1).map((s: string) => s.trim()));
      }
    });
    
    return actions.slice(0, 4); // Limit to top 4 follow-up actions
  }
}

export const pdfService = new PDFService(); 