from setuptools import setup, find_packages

setup(
    name="chatroom-application",
    version="1.0.0",
    description="Secure real-time chatroom application",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt6>=6.4.0",
        "cryptography>=3.4.8",
        "pytest>=7.0.0",
        "pytest-qt>=4.0.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "chatroom-server=server.main:main",
            "chatroom-client=client.main:main",
        ],
    },
)

