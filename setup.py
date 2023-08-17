from setuptools import setup, find_packages

setup(
    name="Dan Testing",
    version="1.0.0",
    description="Spawn VNs to test DAN layer",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/Cifko/spawn-vns-tests",
    packages=find_packages(),
    install_requires=[
        "grpcio-tools",
        "requests",
        "psutil",
        "jsonrpcserver"
        # Add more dependencies here
    ],
)
