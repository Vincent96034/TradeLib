from setuptools import setup, find_packages


def parse_requirements(filename):
    with open(filename, "r") as file:
        return [
            line.strip() for line in file if line.strip() and not line.startswith("#")
        ]


setup(
    name="TradeLib",
    version="0.1.0",
    packages=find_packages(where="tradelib"),
    install_requires=parse_requirements("requirements.txt"),
    author="Vincent Haunberger",
    author_email="vhaunberger@gmail.com",
    description="A library for trading algorithms",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vincenthaunberger/TradeLib",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
