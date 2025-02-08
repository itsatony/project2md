# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="project2md",
    version="1.0.0",
    author="itsatony",
    author_email="i@itsatony.com",
    description="Transform Git repositories into comprehensive Markdown documentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/itsatony/project2md",
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=7.0.0",
        "gitpython>=3.1.0",
        "pyyaml>=5.1.0",
        "rich>=9.0.0",  # for progress bars and pretty output
        "pathspec>=0.9.0",  # for gitignore-style pattern matching
        "chardet>=3.0.4",  # for file encoding detection
        "humanize>=3.0.0",  # for human-readable sizes
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=0.900",
            "pylint>=2.12.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "project2md=project2md.cli:main",
        ],
    },
)