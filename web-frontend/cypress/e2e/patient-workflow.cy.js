describe('Patient Workflow', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/patients/*', { fixture: 'patient.json' }).as('getPatient');
    cy.intercept('GET', '/api/predictions/*', { fixture: 'predictions.json' }).as('getPredictions');
    cy.visit('/');
  });

  it('completes full patient workflow', () => {
    // Login
    cy.get('[data-testid="login-form"]').within(() => {
      cy.get('input[name="username"]').type('testuser');
      cy.get('input[name="password"]').type('password');
      cy.get('button[type="submit"]').click();
    });

    // Navigate to patient search
    cy.get('[data-testid="patient-search"]').click();

    // Search for patient
    cy.get('input[placeholder="Search patients..."]').type('John Doe');
    cy.wait('@getPatient');

    // Select patient
    cy.get('[data-testid="patient-list"]').contains('John Doe').click();

    // Verify patient dashboard loads
    cy.get('[data-testid="patient-dashboard"]').should('be.visible');
    cy.wait('@getPredictions');

    // Check risk score display
    cy.get('[data-testid="risk-score"]').should('be.visible');
    cy.get('[data-testid="risk-score-value"]').should('contain', '75%');

    // View prediction explanation
    cy.get('[data-testid="show-explanation"]').click();
    cy.get('[data-testid="feature-importance-chart"]').should('be.visible');

    // Check clinical history
    cy.get('[data-testid="clinical-history"]').should('be.visible');
    cy.get('[data-testid="diagnoses-list"]').should('contain', 'Diabetes');

    // View lab results
    cy.get('[data-testid="lab-results-tab"]').click();
    cy.get('[data-testid="lab-results-table"]').should('be.visible');

    // Add clinical note
    cy.get('[data-testid="add-note"]').click();
    cy.get('[data-testid="note-editor"]').within(() => {
      cy.get('textarea').type('Patient showing improvement');
      cy.get('button[type="submit"]').click();
    });
    cy.get('[data-testid="clinical-notes"]').should('contain', 'Patient showing improvement');

    // Update risk assessment
    cy.get('[data-testid="update-risk"]').click();
    cy.get('[data-testid="risk-assessment-form"]').within(() => {
      cy.get('input[name="risk"]').type('0.8');
      cy.get('textarea[name="notes"]').type('Increased risk due to recent lab results');
      cy.get('button[type="submit"]').click();
    });

    // Verify risk update
    cy.get('[data-testid="risk-score-value"]').should('contain', '80%');
    cy.get('[data-testid="risk-history"]').should('contain', 'Increased risk due to recent lab results');

    // Export patient report
    cy.get('[data-testid="export-report"]').click();
    cy.get('[data-testid="export-options"]').within(() => {
      cy.get('input[name="include_labs"]').check();
      cy.get('input[name="include_notes"]').check();
      cy.get('button[type="submit"]').click();
    });

    // Verify export
    cy.readFile('cypress/downloads/patient-report.pdf').should('exist');
  });

  it('handles error states gracefully', () => {
    // Test API error handling
    cy.intercept('GET', '/api/patients/*', { statusCode: 500 }).as('getPatientError');
    cy.visit('/patients/123');
    cy.get('[data-testid="error-message"]').should('be.visible');
    cy.get('[data-testid="retry-button"]').click();
    cy.wait('@getPatientError');
    cy.get('[data-testid="error-message"]').should('be.visible');

    // Test network error
    cy.intercept('GET', '/api/predictions/*', { forceNetworkError: true }).as('getPredictionsError');
    cy.visit('/patients/123');
    cy.get('[data-testid="error-message"]').should('be.visible');
  });

  it('validates user inputs', () => {
    cy.visit('/patients/123');

    // Test risk assessment validation
    cy.get('[data-testid="update-risk"]').click();
    cy.get('[data-testid="risk-assessment-form"]').within(() => {
      cy.get('input[name="risk"]').type('2.0'); // Invalid risk score
      cy.get('button[type="submit"]').click();
      cy.get('[data-testid="error-message"]').should('contain', 'Risk score must be between 0 and 1');
    });

    // Test clinical note validation
    cy.get('[data-testid="add-note"]').click();
    cy.get('[data-testid="note-editor"]').within(() => {
      cy.get('button[type="submit"]').click();
      cy.get('[data-testid="error-message"]').should('contain', 'Note cannot be empty');
    });
  });

  it('maintains data consistency', () => {
    cy.visit('/patients/123');

    // Verify data consistency after updates
    cy.get('[data-testid="update-risk"]').click();
    cy.get('[data-testid="risk-assessment-form"]').within(() => {
      cy.get('input[name="risk"]').type('0.85');
      cy.get('button[type="submit"]').click();
    });

    // Refresh page and verify data persistence
    cy.reload();
    cy.get('[data-testid="risk-score-value"]').should('contain', '85%');

    // Verify audit trail
    cy.get('[data-testid="audit-trail"]').should('contain', 'Risk assessment updated');
  });
}); 