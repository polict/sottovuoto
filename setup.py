from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sottovuoto",
    description="sottovuoto is a tight variable packing tool for solidity",
    url="https://github.com",
    author="Paolo Giai",
    version="0.0.1",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "slither-analyzer",
        "ortools"
    ],
    license="GPL-3.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "sottovuoto = sottovuoto.__main__:main"
        ]
    },
)