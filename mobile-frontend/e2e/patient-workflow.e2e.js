describe('Patient Workflow', () => {
  beforeAll(async () => {
    await device.launchApp();
    // Set default timeout for all tests
    jest.setTimeout(30000);
  });

  beforeEach(async () => {
    await device.reloadReactNative();
    // Clear any previous test data
    await device.clearKeychain();
    await device.clearUserDefaults();
  });

  afterEach(async () => {
    // Cleanup after each test
    await device.clearKeychain();
    await device.clearUserDefaults();
  });

  it('completes full patient workflow', async () => {
    try {
      // Login
      await element(by.id('username-input')).typeText('testuser');
      await element(by.id('password-input')).typeText('password');
      await element(by.id('login-button')).tap();

      // Wait for login to complete
      await waitFor(element(by.id('patient-list-tab'))).toBeVisible().withTimeout(5000);

      // Navigate to patient list
      await element(by.id('patient-list-tab')).tap();
      await waitFor(element(by.id('patient-list'))).toBeVisible().withTimeout(5000);

      // Search for patient
      await element(by.id('search-input')).typeText('John Doe');
      await waitFor(element(by.text('John Doe'))).toBeVisible().withTimeout(5000);

      // Select patient
      await element(by.text('John Doe')).tap();

      // Verify patient details screen
      await waitFor(element(by.id('patient-details'))).toBeVisible().withTimeout(5000);
      await expect(element(by.id('patient-name'))).toHaveText('John Doe');
      await expect(element(by.id('risk-score'))).toBeVisible();

      // View risk details
      await element(by.id('risk-details-button')).tap();
      await waitFor(element(by.id('risk-details-modal'))).toBeVisible().withTimeout(5000);
      await expect(element(by.id('risk-chart'))).toBeVisible();

      // View clinical history
      await element(by.id('clinical-history-tab')).tap();
      await waitFor(element(by.id('clinical-history-list'))).toBeVisible().withTimeout(5000);
      await expect(element(by.text('Diabetes'))).toBeVisible();

      // Add clinical note
      await element(by.id('add-note-button')).tap();
      await element(by.id('note-input')).typeText('Patient showing improvement');
      await element(by.id('save-note-button')).tap();
      await waitFor(element(by.text('Patient showing improvement'))).toBeVisible().withTimeout(5000);

      // Update risk assessment
      await element(by.id('update-risk-button')).tap();
      await element(by.id('risk-input')).typeText('0.8');
      await element(by.id('risk-notes-input')).typeText('Increased risk due to recent lab results');
      await element(by.id('save-risk-button')).tap();

      // Verify risk update
      await waitFor(element(by.id('risk-score'))).toHaveText('80%').withTimeout(5000);
      await waitFor(element(by.text('Increased risk due to recent lab results'))).toBeVisible().withTimeout(5000);

      // View lab results
      await element(by.id('lab-results-tab')).tap();
      await waitFor(element(by.id('lab-results-list'))).toBeVisible().withTimeout(5000);

      // Export patient report
      await element(by.id('export-button')).tap();
      await element(by.id('include-labs-checkbox')).tap();
      await element(by.id('include-notes-checkbox')).tap();
      await element(by.id('export-confirm-button')).tap();

      // Verify export success
      await waitFor(element(by.id('export-success-message'))).toBeVisible().withTimeout(5000);
    } catch (error) {
      console.error('Test failed:', error);
      throw error;
    }
  });

  it('handles error states gracefully', async () => {
    try {
      // Test network error
      await device.setURLBlacklist(['.*/api/.*']);
      await element(by.id('patient-list-tab')).tap();
      await waitFor(element(by.id('error-message'))).toBeVisible().withTimeout(5000);
      await expect(element(by.id('retry-button'))).toBeVisible();

      // Test retry functionality
      await device.setURLBlacklist([]);
      await element(by.id('retry-button')).tap();
      await waitFor(element(by.id('patient-list'))).toBeVisible().withTimeout(5000);
    } catch (error) {
      console.error('Test failed:', error);
      throw error;
    }
  });

  it('validates user inputs', async () => {
    try {
      await element(by.id('patient-list-tab')).tap();
      await element(by.text('John Doe')).tap();

      // Test risk assessment validation
      await element(by.id('update-risk-button')).tap();
      await element(by.id('risk-input')).typeText('2.0'); // Invalid risk score
      await element(by.id('save-risk-button')).tap();
      await waitFor(element(by.id('error-message'))).toHaveText('Risk score must be between 0 and 1').withTimeout(5000);

      // Test clinical note validation
      await element(by.id('add-note-button')).tap();
      await element(by.id('save-note-button')).tap();
      await waitFor(element(by.id('error-message'))).toHaveText('Note cannot be empty').withTimeout(5000);
    } catch (error) {
      console.error('Test failed:', error);
      throw error;
    }
  });

  it('maintains data consistency', async () => {
    try {
      await element(by.id('patient-list-tab')).tap();
      await element(by.text('John Doe')).tap();

      // Update risk assessment
      await element(by.id('update-risk-button')).tap();
      await element(by.id('risk-input')).typeText('0.85');
      await element(by.id('save-risk-button')).tap();

      // Navigate away and back
      await element(by.id('back-button')).tap();
      await element(by.text('John Doe')).tap();

      // Verify data persistence
      await waitFor(element(by.id('risk-score'))).toHaveText('85%').withTimeout(5000);
    } catch (error) {
      console.error('Test failed:', error);
      throw error;
    }
  });

  it('handles offline mode', async () => {
    try {
      // Enable offline mode
      await device.setURLBlacklist(['.*/api/.*']);

      // Navigate to patient list
      await element(by.id('patient-list-tab')).tap();

      // Verify offline indicator
      await waitFor(element(by.id('offline-indicator'))).toBeVisible().withTimeout(5000);

      // Verify cached data is displayed
      await waitFor(element(by.id('patient-list'))).toBeVisible().withTimeout(5000);

      // Attempt to update data
      await element(by.text('John Doe')).tap();
      await element(by.id('update-risk-button')).tap();
      await element(by.id('risk-input')).typeText('0.9');
      await element(by.id('save-risk-button')).tap();

      // Verify offline warning
      await waitFor(element(by.id('offline-warning'))).toBeVisible().withTimeout(5000);

      // Re-enable network
      await device.setURLBlacklist([]);

      // Verify sync
      await element(by.id('sync-button')).tap();
      await waitFor(element(by.id('sync-success'))).toBeVisible().withTimeout(5000);
    } catch (error) {
      console.error('Test failed:', error);
      throw error;
    }
  });
});
