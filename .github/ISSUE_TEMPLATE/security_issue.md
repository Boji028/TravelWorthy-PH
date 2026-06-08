name: Security Issue
description: Report a security vulnerability (Please use responsible disclosure)
title: "[SECURITY] "
labels: ["security", "vulnerability"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        🔒 **SECURITY REPORT**
        
        Thank you for helping us keep the Travel Agency application secure!
        
        **Please note:** For sensitive security issues, consider emailing security@travel-agency.com instead of posting publicly.
        
        Do not disclose security vulnerabilities publicly before they have been addressed.

  - type: dropdown
    id: vulnerability_type
    attributes:
      label: Vulnerability Type
      description: What type of security issue is this?
      options:
        - SQL Injection
        - Cross-Site Scripting (XSS)
        - Cross-Site Request Forgery (CSRF)
        - Authentication bypass
        - Authorization bypass
        - Sensitive data exposure
        - Security misconfiguration
        - Insecure deserialization
        - Using components with known vulnerabilities
        - Insufficient logging and monitoring
        - Other
    validations:
      required: true

  - type: textarea
    id: vulnerability_description
    attributes:
      label: Describe the Vulnerability
      description: Detailed description of the security issue
      placeholder: "The application is vulnerable to SQL injection in the search parameter..."
    validations:
      required: true

  - type: textarea
    id: attack_scenario
    attributes:
      label: Possible Attack Scenario
      description: How could an attacker exploit this vulnerability?
      placeholder: |
        1. An attacker could...
        2. This would allow them to...
        3. Impact would be...
    validations:
      required: true

  - type: textarea
    id: proof_of_concept
    attributes:
      label: Proof of Concept (Optional)
      description: Include a minimal proof of concept if applicable
      render: bash
      placeholder: "curl 'http://localhost/search?q='; DROP TABLE users;--'"

  - type: textarea
    id: impact
    attributes:
      label: Impact Assessment
      description: What is the potential impact?
      placeholder: |
        - Confidentiality impact: High
        - Integrity impact: High
        - Availability impact: Medium
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      description: How severe is this vulnerability?
      options:
        - Critical (System completely compromised)
        - High (Significant impact on security)
        - Medium (Moderate security impact)
        - Low (Minor security issue)
    validations:
      required: true

  - type: textarea
    id: remediation
    attributes:
      label: Suggested Remediation
      description: How can this vulnerability be fixed?
      placeholder: |
        - Use parameterized queries
        - Implement input validation
        - Add CSRF tokens

  - type: input
    id: cvss_score
    attributes:
      label: CVSS Score (Optional)
      description: "If you have calculated a CVSS score, provide it here"
      placeholder: "7.5"

  - type: textarea
    id: additional_info
    attributes:
      label: Additional Information
      description: Any other relevant information

  - type: checkboxes
    id: disclosure
    attributes:
      label: Responsible Disclosure
      description: Please follow responsible disclosure practices
      options:
        - label: I have not disclosed this vulnerability publicly elsewhere
          required: true
        - label: I will allow time for patching before public disclosure
          required: true
        - label: I agree to follow this project's Code of Conduct
          required: true
