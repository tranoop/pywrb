# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pywrb",
    version="0.1.0",  # Ensure this is a valid version string
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python module for processing wave data files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tranoop/pywrb",
    packages=find_packages(),
    include_package_data=True,  # Include non-Python files (e.g., templates, static files)
    package_data={
        "pywrb": [
            "templates/*",  # Include all files in the templates directory
            "static/*",     # Include all files in the static directory
        ],
    },
    install_requires=[
        "flask",
        "pandas",
        "numpy",
        "xarray",
        "matplotlib",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "pywrb=pywrb:app.run",  # Command-line executable
        ],
    },
)
