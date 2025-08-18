"""Setup script for agent-framework."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chaotic-af",
    version="0.1.0",
    author="Agent Framework Contributors",
    description="Build multi-agent systems with ease using MCP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.1.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.15.0"],
        "google": ["google-generativeai>=0.3.0"],
        "all": ["openai>=1.0.0", "anthropic>=0.15.0", "google-generativeai>=0.3.0"],
    },
    entry_points={
        "console_scripts": [
            "agentctl=agent_framework.cli.commands:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
