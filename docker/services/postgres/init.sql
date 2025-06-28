-- Healthcare AI Database Initialization Script

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table for storing conversation history
CREATE TABLE IF NOT EXISTS conversation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    agent_type VARCHAR(50) NOT NULL, -- 'crewai' or 'autogen'
    message_type VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    message_content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Table for audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50), -- e.g., 'Patient', 'Observation'
    resource_id VARCHAR(255),
    fhir_endpoint VARCHAR(500),
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Table for FHIR operations tracking
CREATE TABLE IF NOT EXISTS fhir_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(50) NOT NULL, -- 'read', 'search', 'create', 'update'
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    query_parameters JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversation_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_fhir_operations_session_id ON fhir_operations(session_id);
CREATE INDEX IF NOT EXISTS idx_fhir_operations_timestamp ON fhir_operations(timestamp); 