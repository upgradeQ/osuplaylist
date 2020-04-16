import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="osuplaylist",
    version="0.2.0",
    author="upgradehq",
    author_email="noreply@example.com",
    description="Export audio to directory/to ingame collection or create m3u8 playlist",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hqupgradehq/osuplaylist",
    packages=["osuplaylist"],
    entry_points={"console_scripts": ["osuplaylist=osuplaylist.osuplaylist:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    # for pathlib and f strings
    python_requires=">=3.6",
)
