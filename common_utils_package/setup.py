from setuptools import setup, find_packages

setup(
    name="common_utils",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "python-jose>=3.3.0",
        "sqlalchemy>=1.4.23",
        "httpx>=0.19.0",
        "redis>=4.0.2",
    ],
    author="MadhuSIT",
    author_email="madhu@example.com",
    description="Common utilities for microservices",
    keywords="fastapi,microservices,utils",
)