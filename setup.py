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
        "reaction-scroll",
        "noaa_py"
    ],
    dependency_links=[
        "https://github.com/scubot/reaction-scroll/tarball/package#egg"
        "=reaction-scroll-0.0.1.dev0",

        "https://github.com/hxtk/noaa_py/tarball/master#egg=noaa_py-0.0.1.dev0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
