# Installation Guide

This document provides instructions for installing and setting up the project.

## Prerequisites

Before installing, ensure you have:
- Python 3.8 or higher
- pip package manager
- Git

## Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/test-docs.git
   cd test-docs
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

The following environment variables are required:
- `GITHUB_TOKEN`: Your GitHub API token
- `TEST_REPO`: The repository to test against

## Verification

To verify the installation:
```bash
python -m unittest tests/test_documentation_embeddings.py
```
