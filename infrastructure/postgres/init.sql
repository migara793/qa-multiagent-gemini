-- QA Multi-Agent System Database Schema
-- PostgreSQL Reference: https://www.postgresql.org/docs/

-- Create executions table
CREATE TABLE IF NOT EXISTS executions (
    id VARCHAR(36) PRIMARY KEY,
    commit_sha VARCHAR(40) NOT NULL,
    branch VARCHAR(255) NOT NULL,
    pull_request_id VARCHAR(50),
    repo_url VARCHAR(500) NOT NULL,
    trigger_type VARCHAR(20) NOT NULL,
    author VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time FLOAT,
    result JSONB,
    error TEXT
);

-- Create test_results table
CREATE TABLE IF NOT EXISTS test_results (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    agent_name VARCHAR(50) NOT NULL,
    test_type VARCHAR(20) NOT NULL,
    total_tests INTEGER DEFAULT 0,
    passed_tests INTEGER DEFAULT 0,
    failed_tests INTEGER DEFAULT 0,
    duration FLOAT,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create bugs table
CREATE TABLE IF NOT EXISTS bugs (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    line_number INTEGER,
    root_cause TEXT,
    suggested_fix TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create quality_gates table
CREATE TABLE IF NOT EXISTS quality_gates (
    id SERIAL PRIMARY KEY,
    execution_id VARCHAR(36) REFERENCES executions(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,
    passed BOOLEAN DEFAULT FALSE,
    coverage FLOAT,
    pass_rate FLOAT,
    failed_tests INTEGER,
    critical_vulnerabilities INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_executions_commit ON executions(commit_sha);
CREATE INDEX IF NOT EXISTS idx_executions_branch ON executions(branch);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_created ON executions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_test_results_execution ON test_results(execution_id);
CREATE INDEX IF NOT EXISTS idx_test_results_agent ON test_results(agent_name);

CREATE INDEX IF NOT EXISTS idx_metrics_execution ON metrics(execution_id);
CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);

CREATE INDEX IF NOT EXISTS idx_bugs_execution ON bugs(execution_id);
CREATE INDEX IF NOT EXISTS idx_bugs_severity ON bugs(severity);

CREATE INDEX IF NOT EXISTS idx_quality_gates_execution ON quality_gates(execution_id);

-- Insert sample data for testing (optional)
COMMENT ON TABLE executions IS 'QA pipeline execution records';
COMMENT ON TABLE test_results IS 'Test execution results from agents';
COMMENT ON TABLE metrics IS 'Quality metrics collected during execution';
COMMENT ON TABLE bugs IS 'Bugs detected during testing';
COMMENT ON TABLE quality_gates IS 'Quality gate evaluation results';

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO qauser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO qauser;
