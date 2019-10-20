import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="scubot-noaa",
    version="1.0.0.dev0",
    author="Scubot Team",
    description="Tide Chart for Scubot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/scubot/noaa",
    packages=setuptools.find_packages(),
    install_requires=[
        "tinydb",
        "discord",

        "reaction-scroll @ git+https://github.com/scubot/reaction-scroll.git"
        "@25df3c55e91b646542908311abed6691939c81cb",

        "noaa_py @ git+https://github.com/hxtk/noaa_py.git"
        "@54b3eb3471e72aad54d83d147feb1ff89442d43c"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
