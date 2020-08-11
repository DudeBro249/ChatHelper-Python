import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chatHelper", # Replace with your own username
    version="1.1.5",
    author="WeServe Technologies",
    author_email="appdevdeploy@gmail.com",
    description="High-level chat client API that makes sending messages between computers(using http) easy.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DudeBro249/ChatHelper-Python/",
    packages=["chatHelper"],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires= ["Flask", "requests"]
)
