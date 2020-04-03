import setuptools

install_requires = [
    'pytest',
    'numpy',
    'cocotb',
    'nmigen @ git+https://github.com/m-labs/nmigen.git@v0.1#egg=nmigen',
    'nmigen-cocotb @ git+https://github.com/akukulanski/nmigen-cocotb.git@master#egg=nmigen-cocotb',
    'cores-nmigen @ git+https://github.com/akukulanski/cores-nmigen.git@master#egg=cores-nmigen',
]

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nmigen-datapath-sniffer",
    version="0.1.0",
    author="A. Kukulanski",
    author_email="akukulanski@gmail.com",
    description="Datapath sniffer with AXI Lite interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/akukulanski/nmigen-datapath-sniffer.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=install_requires,
)
