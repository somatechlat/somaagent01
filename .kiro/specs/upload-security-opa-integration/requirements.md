# Requirements Document

## Introduction

This specification defines the requirements for completing three critical security and architecture improvements identified in the Architecture Flow Analysis:

1. **OPA Policy Integration in Agent Tool Calls** - Add policy enforcement before tool execution in agent.py
2. **ClamAV Antivirus Scanning** - Enable antivirus scanning for file uploads
3. **TUS Protocol Completion** - Implement full resumable upload specification

These improvements address gaps in the current VIBE compliance score and strengthen the security posture of SomaAgent01.

## Glossary

- **OPA**: Open Policy Agent - authorization policy engine
- **ClamAV**: Open-source antivirus engine
- **TUS**: Resumable upload protocol (tus.io)
- **VIBE**: Verification, Implementation, Behavior, Execution coding rules
- **Tool**: Agent capability that can be invoked via JSON request
- **PolicyClient**: Existing OPA client at `services/common/policy_client.py`
- **AttachmentsStore**: PostgreSQL-backed file storage
- **Quarantine**: Status for files that fail antivirus scan

## Requirements

### Requirement 1: OPA Policy Check in Agent Tool Execution

**User Story:** As a system administrator, I want tool execution in the agent to be authorized via OPA policy, so that unauthorized tool usage is prevented at the agent level.

#### Acceptance Criteria

1. WHEN the agent's `process_tools()` method is called THEN the System SHALL check OPA policy before executing the tool
2. WHEN OPA denies a tool request THEN the System SHALL NOT execute the tool and SHALL add a warning to history
3. WHEN OPA is unavailable THEN the System SHALL fail-closed (deny the tool request)
4. WHEN OPA allows a tool request THEN the System SHALL proceed with tool execution
5. WHEN a tool is denied THEN the System SHALL log the denial with tenant_id, tool_name, and reason

### Requirement 2: ClamAV Antivirus Integration

**User Story:** As a system administrator, I want uploaded files scanned for viruses, so that malicious files are quarantined before storage.

#### Acceptance Criteria

1. WHEN a file upload is finalized THEN the System SHALL scan the file content using ClamAV via pyclamd
2. WHEN ClamAV detects a threat THEN the System SHALL set file status to "quarantined" with the threat name
3. WHEN ClamAV scan passes THEN the System SHALL set file status to "clean"
4. WHEN ClamAV is unavailable THEN the System SHALL set file status to "scan_pending" and log a warning
5. WHEN a file is quarantined THEN the System SHALL NOT allow download of that file

### Requirement 3: TUS Protocol Completion

**User Story:** As a user, I want resumable file uploads, so that large file uploads can survive network interruptions.

#### Acceptance Criteria

1. WHEN a TUS upload is initiated THEN the System SHALL return `upload_id`, `upload_url`, and `chunk_size`
2. WHEN a TUS chunk is uploaded THEN the System SHALL validate offset continuity
3. WHEN a TUS upload is resumed THEN the System SHALL accept chunks from the last successful offset
4. WHEN a TUS upload is finalized THEN the System SHALL compute SHA-256 and trigger ClamAV scan
5. WHEN a TUS upload expires THEN the System SHALL cleanup partial upload data

### Requirement 4: Prometheus Metrics for Security Events

**User Story:** As an SRE, I want security events exposed as Prometheus metrics, so that I can monitor and alert on security issues.

#### Acceptance Criteria

1. WHEN a tool is denied by OPA THEN the System SHALL increment `tool_policy_denied_total` counter
2. WHEN a file is quarantined THEN the System SHALL increment `upload_quarantined_total` counter
3. WHEN ClamAV scan completes THEN the System SHALL record duration in `clamav_scan_duration_seconds` histogram
4. WHEN OPA check completes THEN the System SHALL record duration in `opa_tool_check_duration_seconds` histogram

### Requirement 5: Configuration via cfg Facade

**User Story:** As a system maintainer, I want all new configuration to use the canonical cfg facade, so that configuration remains consolidated.

#### Acceptance Criteria

1. WHEN ClamAV connection is configured THEN the System SHALL use `cfg.env("SA01_CLAMAV_HOST")` and `cfg.env("SA01_CLAMAV_PORT")`
2. WHEN TUS chunk size is configured THEN the System SHALL use `cfg.env("SA01_TUS_CHUNK_SIZE")`
3. WHEN TUS expiry is configured THEN the System SHALL use `cfg.env("SA01_TUS_EXPIRY_HOURS")`
4. WHEN OPA tool policy is configured THEN the System SHALL use existing `cfg.settings().external.opa_url`
