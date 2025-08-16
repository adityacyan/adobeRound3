# Python Environment Management

## Always Activate Local Environment First

Before running any Python or pip commands, **ALWAYS** check if the local conda environment is activated:

```bash
conda activate .\.conda
```

## Key Rules:

1. **Never run pip or python commands without activating the environment first**
2. **Check environment activation status** before any package installation or Python execution
3. **Use the local .conda environment** for this project to ensure dependency isolation
4. **Verify activation** by checking the command prompt shows `(.conda)` prefix

## Common Commands:

```bash
# Activate environment
conda activate .\.conda

# Install packages (only after activation)
python -m pip install package_name

# Run Python scripts (only after activation)
python script_name.py

# Check current environment
conda info --envs
```

## Why This Matters:

- Ensures dependencies are installed in the correct environment
- Prevents conflicts with system Python or other projects
- Maintains project isolation and reproducibility
- Avoids "package not found" errors during execution

## Before Any Python Task:

1. ✅ Check if environment is activated: `conda activate .\.conda`
2. ✅ Verify activation with prompt showing `(.conda)`
3. ✅ Then proceed with pip installs or Python execution
4. ✅ If packages are missing, install them in the activated environment

This is critical for proper development workflow and avoiding environment-related issues.