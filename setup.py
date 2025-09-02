from setuptools import setup, find_packages

setup(
    name="code-lm",
    version="0.2.5",
    description="A CLI for interacting with various LLM models using OpenRouter and other APIs.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Panagiotis897",
    author_email="orion256business@gmail.com",
    url="https://github.com/Panagiotis897/lm-code",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "lmcode=gemini_cli.main:cli",
        ]
    },
    install_requires=[
        "click",
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
