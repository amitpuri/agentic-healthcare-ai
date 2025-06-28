"""
FHIR Tools for AI Agents with MCP Integration
Provides comprehensive FHIR operations and PDF export capabilities
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import os
from pathlib import Path

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger(__name__)

class FHIRMCPClient:
    """FHIR MCP Client for AI Agents with toolUse='fhir' configuration"""
    
    def __init__(self, mcp_url: str = None, tool_use: str = 'fhir'):
        # Get network configuration for dynamic URL generation
        network_host = os.getenv('NETWORK_HOST', 'localhost')
        network_protocol = os.getenv('NETWORK_PROTOCOL', 'http')
        default_mcp_url = f"{network_protocol}://{network_host}:8004"
        
        self.mcp_url = mcp_url or os.getenv('REACT_APP_FHIR_MCP_URL', default_mcp_url)
        self.tool_use = tool_use
        self.session = None
        self.request_id = 1
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP tool with JSON-RPC 2.0 protocol"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        request_data = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        self.request_id += 1
        
        try:
            async with self.session.post(
                f"{self.mcp_url}/mcp",
                json=request_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                result = await response.json()
                
                if "error" in result:
                    raise Exception(f"MCP Error: {result['error']}")
                
                return result.get("result", {})
                
        except Exception as ex:
            logger.error(f"MCP tool call failed: {ex}")
            raise ex
    
    async def get_tool_config(self) -> Dict[str, Any]:
        """Get FHIR tool configuration"""
        return await self.call_mcp_tool("get_tool_config", {"toolUse": self.tool_use})
    
    async def get_patient_comprehensive_data(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive patient data for AI assessment"""
        return await self.call_mcp_tool("get_patient_comprehensive_data", {"patient_id": patient_id})
    
    async def get_encounter_details(self, encounter_id: str) -> Dict[str, Any]:
        """Get detailed encounter information"""
        return await self.call_mcp_tool("get_encounter_details", {"encounter_id": encounter_id})
    
    async def get_vital_signs_analysis(self, patient_id: str, days: int = 30) -> Dict[str, Any]:
        """Get vital signs analysis"""
        return await self.call_mcp_tool("get_vital_signs_analysis", {"patient_id": patient_id, "days": days})
    
    async def search_fhir_resources(self, resource_type: str, search_params: Dict[str, str]) -> Dict[str, Any]:
        """Search FHIR resources"""
        return await self.call_mcp_tool("search", {"type": resource_type, "searchParam": search_params})


class PatientAssessmentReport:
    """PDF Assessment Report Generator for AI Agents"""
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom styles for the PDF report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.darkblue,
            spaceBefore=15,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReportBody',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
    
    async def generate_comprehensive_assessment(
        self,
        patient_data: Dict[str, Any],
        assessment_data: Dict[str, Any],
        output_filename: str = None
    ) -> str:
        """Generate comprehensive AI assessment report in PDF format"""
        
        if not output_filename:
            patient_id = patient_data.get("patient", {}).get("id", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"assessment_report_{patient_id}_{timestamp}.pdf"
        
        file_path = self.output_dir / output_filename
        
        # Create PDF document
        doc = SimpleDocTemplate(str(file_path), pagesize=A4, topMargin=0.5*inch)
        story = []
        
        # Title
        story.append(Paragraph("AI Healthcare Assessment Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Patient Information Section
        story.append(Paragraph("Patient Information", self.styles['SectionHeader']))
        patient_info = self._format_patient_info(patient_data.get("patient", {}))
        story.append(Paragraph(patient_info, self.styles['ReportBody']))
        story.append(Spacer(1, 15))
        
        # Clinical Summary Section
        story.append(Paragraph("Clinical Summary", self.styles['SectionHeader']))
        
        # Conditions
        if patient_data.get("conditions", {}).get("entry"):
            story.append(Paragraph("<b>Active Conditions:</b>", self.styles['ReportBody']))
            conditions_table = self._create_conditions_table(patient_data["conditions"]["entry"])
            story.append(conditions_table)
            story.append(Spacer(1, 10))
        
        # Medications
        if patient_data.get("medications", {}).get("entry"):
            story.append(Paragraph("<b>Current Medications:</b>", self.styles['ReportBody']))
            medications_table = self._create_medications_table(patient_data["medications"]["entry"])
            story.append(medications_table)
            story.append(Spacer(1, 10))
        
        # Vital Signs
        if patient_data.get("vital_signs", {}).get("entry"):
            story.append(Paragraph("<b>Recent Vital Signs:</b>", self.styles['ReportBody']))
            vitals_table = self._create_vitals_table(patient_data["vital_signs"]["entry"])
            story.append(vitals_table)
            story.append(Spacer(1, 15))
        
        # AI Assessment Section
        story.append(Paragraph("AI Assessment & Recommendations", self.styles['SectionHeader']))
        
        if assessment_data:
            # Risk Assessment
            if "risk_scores" in assessment_data:
                story.append(Paragraph("<b>Risk Assessment:</b>", self.styles['ReportBody']))
                risk_content = self._format_risk_assessment(assessment_data["risk_scores"])
                story.append(Paragraph(risk_content, self.styles['ReportBody']))
                story.append(Spacer(1, 10))
            
            # Clinical Recommendations
            if "recommendations" in assessment_data:
                story.append(Paragraph("<b>Clinical Recommendations:</b>", self.styles['ReportBody']))
                for idx, rec in enumerate(assessment_data["recommendations"], 1):
                    story.append(Paragraph(f"{idx}. {rec}", self.styles['ReportBody']))
                story.append(Spacer(1, 10))
            
            # Care Plan
            if "care_plan" in assessment_data:
                story.append(Paragraph("<b>Proposed Care Plan:</b>", self.styles['ReportBody']))
                care_plan_content = self._format_care_plan(assessment_data["care_plan"])
                story.append(Paragraph(care_plan_content, self.styles['ReportBody']))
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Generated by AI Healthcare System | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data Source: FHIR MCP Server"
        story.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Assessment report generated: {file_path}")
        return str(file_path)
    
    def _format_patient_info(self, patient: Dict[str, Any]) -> str:
        """Format patient information for PDF"""
        name = ""
        if patient.get("name") and len(patient["name"]) > 0:
            name_parts = []
            if patient["name"][0].get("given"):
                name_parts.extend(patient["name"][0]["given"])
            if patient["name"][0].get("family"):
                name_parts.append(patient["name"][0]["family"])
            name = " ".join(name_parts)
        
        birth_date = patient.get("birthDate", "")
        gender = patient.get("gender", "")
        patient_id = patient.get("id", "")
        
        return f"""
        <b>Name:</b> {name}<br/>
        <b>Patient ID:</b> {patient_id}<br/>
        <b>Date of Birth:</b> {birth_date}<br/>
        <b>Gender:</b> {gender.capitalize() if gender else ""}<br/>
        """
    
    def _create_conditions_table(self, conditions: List[Dict[str, Any]]) -> Table:
        """Create conditions table for PDF"""
        data = [['Condition', 'Status', 'Clinical Status']]
        
        for condition in conditions[:10]:  # Limit to 10 conditions
            if not condition:
                continue
                
            # Extract condition name
            condition_name = ""
            if condition.get("code", {}).get("coding"):
                coding = condition["code"]["coding"][0]
                condition_name = coding.get("display") or coding.get("code", "")
            
            # Extract status
            verification_status = ""
            if condition.get("verificationStatus", {}).get("coding"):
                verification_status = condition["verificationStatus"]["coding"][0].get("code", "")
            
            clinical_status = ""
            if condition.get("clinicalStatus", {}).get("coding"):
                clinical_status = condition["clinicalStatus"]["coding"][0].get("code", "")
            
            data.append([condition_name, verification_status, clinical_status])
        
        table = Table(data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_medications_table(self, medications: List[Dict[str, Any]]) -> Table:
        """Create medications table for PDF"""
        data = [['Medication', 'Status', 'Dosage']]
        
        for med in medications[:10]:  # Limit to 10 medications
            if not med:
                continue
                
            # Extract medication name
            med_name = ""
            if med.get("medicationCodeableConcept", {}).get("coding"):
                coding = med["medicationCodeableConcept"]["coding"][0]
                med_name = coding.get("display") or coding.get("code", "")
            
            status = med.get("status", "")
            
            # Extract dosage
            dosage = ""
            if med.get("dosageInstruction") and len(med["dosageInstruction"]) > 0:
                dosage = med["dosageInstruction"][0].get("text", "")
            
            data.append([med_name, status, dosage])
        
        table = Table(data, colWidths=[3*inch, 1*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _create_vitals_table(self, vitals: List[Dict[str, Any]]) -> Table:
        """Create vital signs table for PDF"""
        data = [['Vital Sign', 'Value', 'Unit', 'Date']]
        
        for vital in vitals[:10]:  # Limit to 10 vitals
            if not vital:
                continue
                
            # Extract vital sign name
            vital_name = ""
            if vital.get("code", {}).get("coding"):
                coding = vital["code"]["coding"][0]
                vital_name = coding.get("display") or coding.get("code", "")
            
            # Extract value and unit
            value = ""
            unit = ""
            if vital.get("valueQuantity"):
                value = str(vital["valueQuantity"].get("value", ""))
                unit = vital["valueQuantity"].get("unit", "")
            
            # Extract date
            date = vital.get("effectiveDateTime", "")
            if date and "T" in date:
                date = date.split("T")[0]  # Just the date part
            
            data.append([vital_name, value, unit, date])
        
        table = Table(data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _format_risk_assessment(self, risk_scores: Dict[str, Any]) -> str:
        """Format risk assessment for PDF"""
        risk_text = ""
        for risk_type, risk_data in risk_scores.items():
            if isinstance(risk_data, dict):
                risk_level = risk_data.get("risk_level", "")
                score = risk_data.get("score", "")
                risk_text += f"<b>{risk_type.replace('_', ' ').title()}:</b> {risk_level.capitalize() if risk_level else ''} (Score: {score})<br/>"
        
        return risk_text
    
    def _format_care_plan(self, care_plan: Dict[str, Any]) -> str:
        """Format care plan for PDF"""
        plan_text = ""
        
        if care_plan.get("goals"):
            plan_text += "<b>Goals:</b><br/>"
            for goal in care_plan["goals"]:
                plan_text += f"• {goal}<br/>"
            plan_text += "<br/>"
        
        if care_plan.get("interventions"):
            plan_text += "<b>Interventions:</b><br/>"
            for intervention in care_plan["interventions"]:
                plan_text += f"• {intervention}<br/>"
            plan_text += "<br/>"
        
        if care_plan.get("monitoring"):
            plan_text += "<b>Monitoring:</b><br/>"
            for monitor in care_plan["monitoring"]:
                plan_text += f"• {monitor}<br/>"
        
        return plan_text


class FHIRToolsForAgents:
    """Comprehensive FHIR tools for AI agents with MCP integration"""
    
    def __init__(self, mcp_url: str = None):
        self.mcp_client = FHIRMCPClient(mcp_url)
        self.pdf_generator = PatientAssessmentReport()
    
    async def get_patient_for_assessment(self, patient_id: str) -> str:
        """Get comprehensive patient data for AI assessment (JSON formatted for agent consumption)"""
        try:
            async with self.mcp_client as client:
                config = await client.get_tool_config()
                patient_data = await client.get_patient_comprehensive_data(patient_id)
                
                return json.dumps({
                    "tool_config": config,
                    "patient_data": patient_data,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
        except Exception as e:
            return json.dumps({"error": f"Failed to get patient data: {str(e)}"})
    
    async def get_encounter_for_analysis(self, encounter_id: str) -> str:
        """Get encounter details for AI analysis"""
        try:
            async with self.mcp_client as client:
                encounter_data = await client.get_encounter_details(encounter_id)
                
                return json.dumps({
                    "encounter_data": encounter_data,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
        except Exception as e:
            return json.dumps({"error": f"Failed to get encounter data: {str(e)}"})
    
    async def get_vital_signs_trends(self, patient_id: str, days: int = 30) -> str:
        """Get vital signs trends for AI analysis"""
        try:
            async with self.mcp_client as client:
                vitals_data = await client.get_vital_signs_analysis(patient_id, days)
                
                return json.dumps({
                    "vitals_analysis": vitals_data,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
        except Exception as e:
            return json.dumps({"error": f"Failed to get vital signs: {str(e)}"})
    
    async def generate_assessment_pdf(
        self,
        patient_id: str,
        assessment_data: Dict[str, Any] = None,
        filename: str = None
    ) -> str:
        """Generate PDF assessment report"""
        try:
            async with self.mcp_client as client:
                # Get comprehensive patient data
                patient_data = await client.get_patient_comprehensive_data(patient_id)
                
                # Generate PDF report
                pdf_path = await self.pdf_generator.generate_comprehensive_assessment(
                    patient_data, assessment_data or {}, filename
                )
                
                return json.dumps({
                    "pdf_path": pdf_path,
                    "patient_id": patient_id,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
                
        except Exception as e:
            return json.dumps({"error": f"Failed to generate PDF: {str(e)}"}) 
