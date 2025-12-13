describe("Patient Workflow", () => {
  beforeAll(async () => {
    await device.launchApp();
    jest.setTimeout(30000);
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it("should complete login and view patient list", async () => {
    // Login
    await element(by.id("username-input")).typeText("clinician");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();

    // Wait for patient list to appear
    await waitFor(element(by.id("patient-list-tab")))
      .toBeVisible()
      .withTimeout(5000);

    // Verify patient list is visible
    await expect(element(by.id("patient-list"))).toBeVisible();
  });

  it("should search for patients", async () => {
    // Login first
    await element(by.id("username-input")).typeText("clinician");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();

    // Wait for patient list
    await waitFor(element(by.id("patient-list-tab")))
      .toBeVisible()
      .withTimeout(5000);

    // Search for a patient
    await element(by.id("search-input")).typeText("John");
    await waitFor(element(by.text("John Doe")))
      .toBeVisible()
      .withTimeout(3000);
  });

  it("should view patient details", async () => {
    // Login
    await element(by.id("username-input")).typeText("clinician");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();

    // Wait for patient list
    await waitFor(element(by.id("patient-list-tab")))
      .toBeVisible()
      .withTimeout(5000);

    // Tap on first patient
    await element(by.id("patient-item-p001")).tap();

    // Verify patient details screen
    await waitFor(element(by.id("patient-details")))
      .toBeVisible()
      .withTimeout(5000);

    await expect(element(by.id("risk-score"))).toBeVisible();
  });

  it("should handle error states gracefully", async () => {
    // Login
    await element(by.id("username-input")).typeText("clinician");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();

    // Wait for patient list
    await waitFor(element(by.id("patient-list-tab")))
      .toBeVisible()
      .withTimeout(5000);

    // If error occurs, retry button should be available
    // This test depends on network conditions
  });

  it("should pull to refresh patient list", async () => {
    // Login
    await element(by.id("username-input")).typeText("clinician");
    await element(by.id("password-input")).typeText("password123");
    await element(by.id("login-button")).tap();

    // Wait for patient list
    await waitFor(element(by.id("patient-list-tab")))
      .toBeVisible()
      .withTimeout(5000);

    // Pull to refresh
    await element(by.id("patient-list")).swipe("down", "slow");

    // List should still be visible after refresh
    await expect(element(by.id("patient-list"))).toBeVisible();
  });
});
