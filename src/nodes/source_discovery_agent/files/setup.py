"""
Setup configuration for Source Discovery Agent
"""

from setuptools import setup, find_packages
import os

# Get the directory where setup.py is located to resolve relative paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Read README for long description
def read_readme():
    readme_path = os.path.join(BASE_DIR, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return "Research Discovery & Validation Specialist for autonomous research workflows"

# Read requirements
def read_requirements():
    requirements = []
    req_path = os.path.join(BASE_DIR, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    requirements.append(line)
    return requirements

setup(
    name="source-discovery-agent",
    version="1.0.0",
    author="Research Systems Team",
    author_email="research@example.com",
    description="Research Discovery & Validation Specialist for autonomous research workflows",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/source-discovery-agent",
    packages=find_packages(exclude=["tests", "tests.*", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=2.12.0",
            "black>=21.5b1",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
        "nlp": [
            "spacy>=3.0.0",
            "scikit-learn>=0.24.0",
        ],
        "enhanced": [
            "wayback>=0.4.0",
            "newspaper3k>=0.2.8",
            "langdetect>=1.0.9",
            "datefinder>=0.7.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "source-discovery=source_discovery_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "source_discovery_agent": ["*.yaml", "*.json"],
    },
    keywords=[
        "research",
        "discovery",
        "validation",
        "credibility",
        "sources",
        "academic",
        "agent",
        "automation",
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/source-discovery-agent/issues",
        "Source": "https://github.com/yourusername/source-discovery-agent",
        "Documentation": "https://source-discovery-agent.readthedocs.io",
    },
)