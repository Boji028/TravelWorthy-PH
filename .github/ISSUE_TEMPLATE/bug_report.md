name: Bug Report
description: Report a bug or issue with the Travel Agency application
title: "[BUG] "
labels: ["bug", "needs-triage"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Thanks for reporting a bug! Please fill out the form below to help us understand and fix the issue.

  - type: checkboxes
    id: prerequisites
    attributes:
      label: Prerequisites
      description: Please verify the following before submitting
      options:
        - label: I have searched for similar issues
          required: true
        - label: I have verified this is not a duplicate
          required: true
        - label: I am using the latest version
          required: true

  - type: textarea
    id: description
    attributes:
      label: Describe the Bug
      description: A clear and concise description of what the bug is
      placeholder: "Example: When I try to book a tour, the page freezes..."
    validations:
      required: true

  - type: textarea
    id: steps_to_reproduce
    attributes:
      label: Steps to Reproduce
      description: Detailed steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. Scroll down to '...'
        4. See error
    validations:
      required: true

  - type: textarea
    id: expected_behavior
    attributes:
      label: Expected Behavior
      description: What you expected to happen
      placeholder: "The page should display the booking confirmation..."
    validations:
      required: true

  - type: textarea
    id: actual_behavior
    attributes:
      label: Actual Behavior
      description: What actually happened instead
      placeholder: "The page shows an error message instead..."
    validations:
      required: true

  - type: dropdown
    id: environment
    attributes:
      label: Environment
      description: What browser/environment are you using?
      options:
        - Chrome (latest)
        - Firefox (latest)
        - Safari (latest)
        - Edge (latest)
        - Other
    validations:
      required: true

  - type: input
    id: browser_version
    attributes:
      label: Browser Version
      description: "e.g. 120.0.0"

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots
      description: If applicable, add screenshots showing the issue
      placeholder: "You can paste images here"

  - type: textarea
    id: error_logs
    attributes:
      label: Error Logs or Stack Trace
      description: If you have console errors or stack traces, paste them here
      render: bash
      placeholder: |
        [Paste error logs here]

  - type: textarea
    id: additional_context
    attributes:
      label: Additional Context
      description: Any other context about the problem
      placeholder: "This started happening after the recent update..."

  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      description: Please confirm you have read and agree to follow our Code of Conduct
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true
