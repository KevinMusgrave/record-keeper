import setuptools

import record_keeper

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="record-keeper",
    version=record_keeper.__version__,
    author="Kevin Musgrave",
    description="Record experiment data easily",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KevinMusgrave/record-keeper",
    packages=setuptools.find_packages(include=["record_keeper"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.0",
    install_requires=["numpy", "matplotlib"],
)
