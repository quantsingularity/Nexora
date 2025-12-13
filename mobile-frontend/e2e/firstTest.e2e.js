describe("Basic Navigation", () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it("should show login screen on launch", async () => {
    await expect(element(by.id("login-screen"))).toBeVisible();
  });

  it("should show login button", async () => {
    await expect(element(by.id("login-button"))).toBeVisible();
  });

  it("should have username and password inputs", async () => {
    await expect(element(by.id("username-input"))).toBeVisible();
    await expect(element(by.id("password-input"))).toBeVisible();
  });
});
