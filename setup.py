from setuptools import setup, find_packages

setup(
    name="code-lm",  # The name of your package
    version="0.1.0",  # Package version
    description="A CLI for interacting with various LLM models using OpenRouter and other APIs.",
    long_description=open("README.md").read(),  # Read from README.md
    long_description_content_type="text/markdown",  # Markdown format
    author="Panagiotis897",
    author_email="your.email@example.com",  # Replace with your email
    url="https://github.com/Panagiotis897/lm-code",  # Repository URL
    license="MIT",  # License type
    packages=find_packages(where="src"),
    package_dir={"": "src"},  # Source directory for the package
    include_package_data=True,  # Include files listed in MANIFEST.in
    entry_points={
        "console_scripts": [
            "lmcode=gemini_cli.main:cli",  # Maps 'lmcode' command to the 'cli' function in main.py
        ]
    },
    install_requires=[
        "click",  # Add required dependencies
        "rich",
        "requests",
        "pyyaml",
        "questionary",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
