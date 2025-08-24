#!/usr/bin/env python3
"""
Setup script for God CLI - Ollama Chat Interface
"""

from setuptools import setup, find_packages
import os
import stat

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Make the CLI script executable
def make_executable():
    script_path = "god_cli.py"
    if os.path.exists(script_path):
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)

setup(
    name="god-cli",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python CLI tool for interacting with local Ollama instances",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/god-cli",
    py_modules=["god_cli"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "god=god_cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

# Make the script executable after setup
make_executable()
