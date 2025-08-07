#!/bin/bash

# Install pre-commit
pip install pre-commit

# Install all hooks
pre-commit install

# Run the hooks on all files once
pre-commit run --all-files 