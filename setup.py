from setuptools import setup

setup(
    name="cdict",
    packages=["cdict"],
    version="1.0.2",
    author="Jeffrey Wu",
    install_requires=[
        "immutabledict",
    ],
    url="https://github.com/wuthefwasthat/cdict",
    description="Combinatorial dictionaries",
    python_requires='>=3.7',
)
