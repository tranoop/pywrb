# setup.py
from setuptools import setup, find_packages

setup(
    name='pywrb',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'pandas',
        'numpy',
        'xarray',
        'matplotlib',
    ],
    entry_points={
        'console_scripts': [
            'pywrb=pywrb:app.run',
        ],
    },
)
