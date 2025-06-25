from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pywrb",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python module for processing wave data files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tranoop/pywrb",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'pywrb': [
            'templates/*.html',
            'static/css/*.css',
            'static/plots/*',
        ],
    },
    install_requires=[
        "flask",
        "pandas",
        "numpy",
        "xarray",
        "matplotlib",
        "netCDF4",
    ],
    classifiers=[
        "Catalin :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'pywrb=pywrb.pywrb:main',
        ],
    },
)
