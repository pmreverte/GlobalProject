from setuptools import setup, find_packages

setup(
    name="backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "passlib",
        "python-jose",
        "python-multipart",
        "bcrypt",
        "pytest",
        "pytest-cov"
    ],
)