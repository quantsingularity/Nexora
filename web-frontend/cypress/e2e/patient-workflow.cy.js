describe("Patient Workflow", () => {
  beforeEach(() => {
    // Set up environment to use mock data
    cy.visit("/", {
      onBeforeLoad(win) {
        win.localStorage.setItem("REACT_APP_USE_MOCK_DATA", "true");
      },
    });
  });

  it("navigates through the main dashboard", () => {
    // Verify dashboard loads
    cy.contains("Clinical Dashboard").should("be.visible");
    cy.contains("Active Patients").should("be.visible");
    cy.contains("High Risk Patients").should("be.visible");

    // Check that charts are rendered
    cy.contains("Admissions & Readmissions Trend").should("be.visible");
    cy.contains("Patient Risk Distribution").should("be.visible");
  });

  it("navigates to patient list and views patient details", () => {
    // Click on Patients in the navigation
    cy.contains("Patients").click();

    // Verify patient list page loads
    cy.contains("Patient List").should("be.visible");

    // Wait for patients to load
    cy.get("table").should("be.visible");

    // Search for a patient
    cy.get('input[placeholder="Search patients..."]').type("John");

    // Verify search results
    cy.get("table tbody tr").should("have.length.greaterThan", 0);

    // Click on the first patient
    cy.get("table tbody tr")
      .first()
      .within(() => {
        cy.get("button").last().click();
      });

    // Verify patient detail page loads
    cy.contains("Patient Details").should("be.visible");
    cy.contains("Back").should("be.visible");
  });

  it("navigates to prediction models page", () => {
    // Click on Models in the navigation
    cy.contains("Models").click();

    // Verify models page loads
    cy.contains("Prediction Models").should("be.visible");
    cy.contains("Available Models").should("be.visible");

    // Check tabs are present
    cy.contains("Performance").should("be.visible");
    cy.contains("Training History").should("be.visible");
    cy.contains("Configuration").should("be.visible");

    // Click on Training History tab
    cy.contains("Training History").click();
    cy.contains("Training Details").should("be.visible");

    // Click on Configuration tab
    cy.contains("Configuration").click();
    cy.contains("Model Configuration").should("be.visible");
  });

  it("navigates to settings page", () => {
    // Click on Settings in the navigation
    cy.contains("Settings").click();

    // Verify settings page loads
    cy.get("h4").contains("Settings").should("be.visible");

    // Check tabs are present
    cy.contains("User Profile").should("be.visible");
    cy.contains("Security").should("be.visible");
    cy.contains("Notifications").should("be.visible");

    // Switch to Security tab
    cy.contains("Security").click();
    cy.contains("Security Settings").should("be.visible");
    cy.contains("Two-Factor Authentication").should("be.visible");

    // Switch to Notifications tab
    cy.contains("Notifications").click();
    cy.contains("Notification Preferences").should("be.visible");
    cy.contains("High-Risk Patient Alerts").should("be.visible");
  });

  it("tests patient list search and filter functionality", () => {
    // Navigate to patient list
    cy.contains("Patients").click();
    cy.contains("Patient List").should("be.visible");

    // Wait for table to load
    cy.get("table tbody tr", { timeout: 10000 }).should(
      "have.length.greaterThan",
      0,
    );

    // Get initial row count
    cy.get("table tbody tr").then((rows) => {
      const initialCount = rows.length;

      // Search for specific patient
      cy.get('input[placeholder="Search patients..."]').type("Smith");

      // Verify filtered results
      cy.get("table tbody tr").should("have.length.lessThan", initialCount);

      // Clear search
      cy.get('input[placeholder="Search patients..."]').clear();

      // Verify all results are back
      cy.get("table tbody tr").should("have.length", initialCount);
    });
  });

  it("tests patient detail tabs", () => {
    // Navigate to patients
    cy.contains("Patients").click();

    // Click on first patient
    cy.get("table tbody tr", { timeout: 10000 })
      .first()
      .within(() => {
        cy.get("button").last().click();
      });

    // Test Clinical Data tab
    cy.contains("Clinical Data").should("be.visible");
    cy.contains("Lab Results").should("be.visible");
    cy.contains("Diagnoses").should("be.visible");

    // Test Risk Analysis tab
    cy.contains("Risk Analysis").click();
    cy.contains("Risk Factors").should("be.visible");
    cy.contains("Recommended Interventions").should("be.visible");

    // Test Medications tab
    cy.contains("Medications").click();
    cy.contains("Current Medications").should("be.visible");

    // Test Timeline tab
    cy.contains("Timeline").click();
    cy.contains("Clinical Timeline").should("be.visible");
  });

  it("tests responsive navigation menu", () => {
    // Test menu toggle
    cy.get('[aria-label="open drawer"]').should("be.visible");
    cy.get('[aria-label="open drawer"]').click();

    // Verify menu items are still visible (or hidden on mobile)
    cy.contains("Dashboard").should("exist");
    cy.contains("Patients").should("exist");
  });

  it("tests profile menu", () => {
    // Click on profile button
    cy.get('[aria-label="account of current user"]').click();

    // Verify menu items
    cy.contains("Profile").should("be.visible");
    cy.contains("My account").should("be.visible");
    cy.contains("Logout").should("be.visible");

    // Close menu
    cy.get("body").click(0, 0);
  });

  it("verifies all main pages are accessible", () => {
    const pages = [
      { link: "Dashboard", title: "Clinical Dashboard" },
      { link: "Patients", title: "Patient List" },
      { link: "Models", title: "Prediction Models" },
      { link: "Settings", title: "Settings" },
    ];

    pages.forEach((page) => {
      cy.contains(page.link).click();
      cy.contains(page.title).should("be.visible");
    });
  });

  it("tests pagination in patient list", () => {
    // Navigate to patient list
    cy.contains("Patients").click();

    // Wait for table to load
    cy.get("table tbody tr", { timeout: 10000 }).should(
      "have.length.greaterThan",
      0,
    );

    // Check pagination controls exist
    cy.contains("Rows per page").should("be.visible");

    // Try changing rows per page
    cy.get('[aria-label="Rows per page:"]').parent().click();
    cy.get('[role="option"]').first().click();
  });

  it("tests error boundary", () => {
    // This is a basic test - in a real app you'd trigger an actual error
    // For now just verify the app loads without errors
    cy.contains("Clinical Dashboard").should("be.visible");
    cy.get("body").should("not.contain", "Something went wrong");
  });
});
