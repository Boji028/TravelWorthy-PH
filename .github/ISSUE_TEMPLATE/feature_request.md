name: Feature Request
description: Suggest a new feature or enhancement
title: "[FEATURE] "
labels: ["enhancement", "feature-request"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Thanks for your feature request! Help us understand your idea with the information below.

  - type: textarea
    id: is_feature_related_to_problem
    attributes:
      label: Is your feature request related to a problem?
      description: Describe the problem you're trying to solve
      placeholder: "e.g., I'm trying to... but there's no way to..."
    validations:
      required: true

  - type: textarea
    id: describe_solution
    attributes:
      label: Describe the Solution You'd Like
      description: How should the feature work?
      placeholder: "The application should allow users to..."
    validations:
      required: true

  - type: textarea
    id: describe_alternatives
    attributes:
      label: Describe Alternatives You've Considered
      description: Are there any alternative solutions or features?
      placeholder: "We could also consider..."

  - type: textarea
    id: additional_context
    attributes:
      label: Additional Context
      description: Any other context or examples
      placeholder: "Here are some similar features in competing products..."

  - type: dropdown
    id: priority
    attributes:
      label: Priority
      description: How urgent is this feature?
      options:
        - Low
        - Medium
        - High
        - Critical

  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true
