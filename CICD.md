# GitHub Actions CI/CD Setup

This project uses GitHub Actions for automated testing and Docker image building.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)
Runs on every push and pull request:
- **Lint & Format**: Ruff linter and formatter checks
- **Unit Tests**: pytest with coverage reporting
- **Docker Build**: Validates test and runtime stages build successfully

**What it does:**
- Checks code quality with Ruff
- Runs full test suite (23 tests)
- Generates coverage reports
- Builds Docker images to catch build issues early

### 2. Build & Push Workflow (`.github/workflows/build-push.yml`)
Runs on pushes to `main` and version tags:
- Builds and pushes Docker image to Docker Hub
- Tags images with branch name, version, SHA, and latest

**Requirements:**
Set these secrets in your GitHub repository:
1. `DOCKER_USERNAME` — your Docker Hub username
2. `DOCKER_PASSWORD` — your Docker Hub personal access token

## Setting Up Secrets

### For Docker Hub Push:
1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add:
   - Name: `DOCKER_USERNAME`, Value: your Docker Hub username
   - Name: `DOCKER_PASSWORD`, Value: your Docker Hub personal access token

**To create a Docker Hub token:**
1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Give it a name (e.g., "github-actions")
4. Copy the token and add it as `DOCKER_PASSWORD` secret

## Manual Workflow Trigger

Push a tag to trigger the build:
```bash
git tag v1.0.0
git push origin v1.0.0
```

Or manually trigger from GitHub:
1. Go to Actions → Build & Push Docker Image
2. Click "Run workflow"

## Monitoring

- **CI runs**: Check the "Checks" tab on pull requests
- **Build logs**: Click into any workflow run to see detailed logs
- **Coverage**: Uploaded to Codecov (optional, view at codecov.io)

## Local Testing

Before pushing, run locally:
```bash
# Lint check
ruff check .

# Format check
ruff format --check .

# Tests
pytest --cov=app --cov-report=term-missing

# Docker build (test stage)
docker build --target test .

# Docker build (runtime stage)
docker build --target runtime .
```
