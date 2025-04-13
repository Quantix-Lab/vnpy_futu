import setuptools

setuptools.setup(
    name="vnpy_futu",
    version="1.0.0",
    author="VeighNa Team",
    author_email="support@vnpy.com",
    description="Futu Securities gateway for VeighNa framework",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vnpy/vnpy_futu",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        "futu-api",
        "vnpy",
    ],
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
)
