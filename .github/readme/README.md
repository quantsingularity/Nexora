# GitHub Workflows for Nexora

## Overview

This directory contains the continuous integration and continuous deployment (CI/CD) workflows for the Nexora project. These workflows automate the testing, building, and deployment processes, ensuring code quality and reliability throughout the development lifecycle. The automated pipeline helps maintain consistency across environments and reduces manual intervention during the release process.

## Workflow Structure

Currently, the Nexora project implements a single workflow file (`ci-cd.yml`) that handles the complete CI/CD process. This consolidated approach simplifies maintenance while providing comprehensive coverage for both code and frontend components of the application.

## CI/CD Workflow

The `ci-cd.yml` workflow is designed to automatically trigger on specific Git events and execute a series of jobs to validate, build, and deploy the Nexora application.

### Trigger Events

The workflow is configured to activate on the following Git events:

- **Push Events**: Automatically triggered when code is pushed to the `main`, `master`, or `develop` branches. This ensures that any direct changes to these critical branches are immediately validated.

- **Pull Request Events**: Automatically triggered when pull requests target the `main`, `master`, or `develop` branches. This validates proposed changes before they are merged into these important branches.

This dual-trigger approach ensures code quality is maintained both during active development and when preparing for integration into stable branches.

### Job: code Testing

The `code-test` job runs on an Ubuntu latest environment and performs comprehensive testing of the code codebase. This job consists of the following steps:

1. **Checkout Code**: Uses the `actions/checkout@v3` action to fetch the repository code.

2. **Set up Python**: Configures Python 3.10 using the `actions/setup-python@v4` action, which is the required version for the Nexora code.

3. **Install Dependencies**: Upgrades pip and installs all required dependencies specified in the `src/requirements.txt` file.

4. **Run Tests**: Executes the pytest test suite located in the `src/tests/` directory to validate code functionality.

This job ensures that all code code meets the project's quality standards and functions as expected before proceeding with deployment.

### Job: Frontend Testing

The `frontend-test` job also runs on an Ubuntu latest environment and focuses on validating the frontend codebase. This job consists of the following steps:

1. **Checkout Code**: Uses the `actions/checkout@v3` action to fetch the repository code.

2. **Set up Node.js**: Configures Node.js 18 using the `actions/setup-node@v3` action, which is required for the Nexora frontend. This step also configures npm caching to speed up subsequent workflow runs.

3. **Install Dependencies**: Runs `npm ci` in the frontend directory to install all required dependencies in a clean, reproducible manner.

4. **Run Tests**: Executes the frontend test suite using `npm test` to validate frontend functionality and user interface components.

This job ensures that all frontend code meets the project's quality standards and functions as expected before proceeding with deployment.

### Job: Build and Deploy

The `build-and-deploy` job is dependent on the successful completion of both the `code-test` and `frontend-test` jobs. This job is conditionally executed only when:

1. The trigger event is a push (not a pull request)
2. The target branch is either `main` or `master`

This ensures that deployment only occurs for production-ready code that has passed all tests. The job consists of the following steps:

1. **Checkout Code**: Uses the `actions/checkout@v3` action to fetch the repository code.

2. **Set up Node.js**: Configures Node.js 18 using the `actions/setup-node@v3` action for building the frontend.

3. **Build Frontend**: Installs frontend dependencies and builds the production-ready frontend assets.

4. **Set up Python**: Configures Python 3.10 using the `actions/setup-python@v4` action for the code deployment.

5. **Install code Dependencies**: Installs all required code dependencies.

6. **Deploy Application**: Placeholder step for deployment commands. The actual deployment commands would need to be added based on the project's deployment strategy.

## Workflow Configuration Details

### Environment

All jobs in the workflow run on the latest Ubuntu environment (`ubuntu-latest`), which provides a consistent and up-to-date platform for building and testing the application.

### Dependency Caching

The workflow implements caching for Node.js dependencies to improve performance:

- The frontend job uses the `cache: 'npm'` option with the `actions/setup-node@v3` action.
- The cache is specifically tied to the `frontend/package-lock.json` file, ensuring that the cache is invalidated when dependencies change.

### Conditional Execution

The deployment job uses conditional execution based on the event type and target branch:

```yaml
if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
```

This ensures that deployments only occur when code is pushed directly to production branches, not during pull request validation.

## Extending the Workflow

The current workflow provides a solid foundation for CI/CD but can be extended in several ways:

### Adding Environment-Specific Deployments

The workflow can be extended to support different environments (development, staging, production) based on the target branch:

- `develop` branch could deploy to a development environment
- `staging` branch could deploy to a staging environment
- `main`/`master` branches could deploy to production

### Adding Security Scanning

Security scanning steps could be added to identify vulnerabilities in dependencies or code:

- Add dependency scanning using tools like OWASP Dependency Check
- Implement static code analysis for security vulnerabilities
- Add container scanning if the application is containerized

### Adding Performance Testing

Performance testing could be integrated to ensure the application meets performance requirements:

- Add load testing steps using tools like k6 or JMeter
- Implement performance benchmarking to track changes over time

## Best Practices for Working with This Workflow

When working with the Nexora CI/CD workflow, consider the following best practices:

1. **Test Locally Before Pushing**: Run tests locally before pushing to avoid unnecessary workflow runs.

2. **Keep Dependencies Updated**: Regularly update dependencies to ensure security and compatibility.

3. **Monitor Workflow Runs**: Regularly check workflow runs to identify and address any issues promptly.

4. **Document Changes**: When modifying the workflow, document the changes and their purpose.

5. **Use Secrets for Sensitive Data**: Store sensitive information like API keys and passwords as GitHub secrets.

## Troubleshooting

If you encounter issues with the workflow, consider the following troubleshooting steps:

1. **Check Workflow Logs**: Examine the detailed logs for each job to identify specific errors.

2. **Verify Dependencies**: Ensure all required dependencies are correctly specified in the respective requirements files.

3. **Check Environment Variables**: Verify that any required environment variables are properly set.

4. **Test Steps Locally**: Try to reproduce the failing steps locally to identify environment-specific issues.

5. **Review Recent Changes**: Check recent code changes that might have introduced incompatibilities.

## Conclusion

The GitHub workflow configuration for Nexora provides a robust CI/CD pipeline that ensures code quality and simplifies the deployment process. By automating testing and deployment, the workflow helps maintain a consistent and reliable application across all environments.
