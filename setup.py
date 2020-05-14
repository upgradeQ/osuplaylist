import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="osuplaylist",
    version="1.0.0",
    author="upgradehq",
    author_email="noreply@example.com",
    description="Export audio from osu to directory/to ingame collection/to steam music  or create m3u8 playlist",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hqupgradehq/osuplaylist",
    packages=["osuplaylist"],
    entry_points={"console_scripts": ["osuplaylist=osuplaylist.osuplaylist:main"]},
    keywords="osu steam export music filter player playlist utility",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: End Users/Desktop",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    # for pathlib and f strings
    python_requires=">=3.6",
    platforms = ['any'],
    license = 'Unlicense'
)
