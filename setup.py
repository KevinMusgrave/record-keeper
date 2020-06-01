import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="record-keeper",
    version="0.9.26",
    author="Kevin Musgrave",
    author_email="tkm45@cornell.edu",
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
    python_requires='>=3.0',
    install_requires=[
          'numpy',
          'matplotlib'
    ],
)