name: Performance Issue
description: Report a performance or optimization issue
title: "[PERFORMANCE] "
labels: ["performance", "optimization"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Help us identify and fix performance bottlenecks in the Travel Agency application.

  - type: textarea
    id: description
    attributes:
      label: Describe the Performance Issue
      description: What is performing poorly?
      placeholder: "The booking page takes 10+ seconds to load..."
    validations:
      required: true

  - type: dropdown
    id: affected_area
    attributes:
      label: Affected Area
      description: Which part of the application is affected?
      options:
        - Database queries
        - API responses
        - Frontend rendering
        - Image loading
        - Search functionality
        - Reports/exports
        - Other
    validations:
      required: true

  - type: textarea
    id: metrics
    attributes:
      label: Performance Metrics
      description: Include response times, CPU usage, memory, etc.
      placeholder: |
        - Current load time: 10 seconds
        - Expected load time: 2 seconds
        - Database queries: 50+ queries
    validations:
      required: true

  - type: textarea
    id: reproduction_steps
    attributes:
      label: Steps to Reproduce
      description: How can we reproduce the performance issue?
      placeholder: |
        1. Navigate to bookings page
        2. Load with 1000 bookings
        3. Observe slow rendering

  - type: textarea
    id: environment_details
    attributes:
      label: Environment Details
      description: Browser, server specs, database size, etc.
      placeholder: |
        - Browser: Chrome 120
        - Server: 2 CPU, 4GB RAM
        - Database: 10GB PostgreSQL

  - type: textarea
    id: profiling_data
    attributes:
      label: Profiling Data
      description: Include any performance profiling data or logs
      render: bash

  - type: textarea
    id: potential_solutions
    attributes:
      label: Potential Solutions
      description: Any ideas on how to fix this?
      placeholder: |
        - Add database indexes
        - Implement caching
        - Optimize queries

  - type: checkboxes
    id: terms
    attributes:
      label: Code of Conduct
      options:
        - label: I agree to follow this project's Code of Conduct
          required: true
