-- Create database
CREATE DATABASE IF NOT EXISTS tcs_forecast;
USE tcs_forecast;

-- Table to log all forecast requests and responses
CREATE TABLE IF NOT EXISTS forecast_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_description TEXT NOT NULL,
    
    -- Agent execution details
    tools_used JSON,
    execution_time_seconds DECIMAL(10, 2),
    
    -- Output
    forecast_output JSON NOT NULL,
    
    -- Metadata
    llm_provider VARCHAR(50),
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    
    INDEX idx_timestamp (request_timestamp),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table to store extracted financial metrics
CREATE TABLE IF NOT EXISTS financial_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    forecast_log_id INT,
    quarter VARCHAR(10),
    year INT,
    
    total_revenue DECIMAL(20, 2),
    net_profit DECIMAL(20, 2),
    operating_margin DECIMAL(5, 2),
    revenue_growth DECIMAL(5, 2),
    
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (forecast_log_id) REFERENCES forecast_logs(id) ON DELETE CASCADE,
    INDEX idx_quarter (quarter, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;