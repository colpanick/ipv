from setuptools import setup, find_packages
setup(
    name="ipv",
    version="1.0",
    packages=find_packages(),
    install_requires=['requests'],
    entry_points={"console_scripts": ["ipv = ipv.ipv:init"]},
)
