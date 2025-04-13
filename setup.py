import os
import setuptools
import platform

with open("README.md", "r", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

# Determine specific platform dependencies
install_requires = [
    "futu-api>=9.1.5000",
    "vnpy>=4.0.0",
]

setuptools.setup(
    name="vnpy_futu",
    version="1.0.0",
    author="Quantix-Lab",
    author_email="contact@quantix-lab.com",
    description="Enhanced Futu Securities gateway for VeighNa trading framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vnpy/vnpy_futu",
    project_urls={
        "Documentation": "https://www.vnpy.com/docs",
        "Source Code": "https://github.com/vnpy/vnpy_futu",
        "Bug Tracker": "https://github.com/vnpy/vnpy_futu/issues",
    },
    packages=setuptools.find_packages(exclude=["tests", "examples"]),
    include_package_data=True,
    package_data={"": ["*.json", "*.mo", "*.md"]},
    zip_safe=False,
    install_requires=install_requires,
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: VeighNa",
    ],
    python_requires=">=3.7",
    keywords="quant quantitative investment trading algotrading",
)
