from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [
        line.strip() for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="AgenticAI",            # Replace with your project’s name
    version="0.1.0",             # Update version as needed
    description="A short description of your project",  # Add a description
    packages=find_packages(),    # Automatically find packages (ensure __init__.py is present)
    install_requires=requirements,  # Dependencies from requirements.txt
)
