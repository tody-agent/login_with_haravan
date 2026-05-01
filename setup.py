from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="login_with_haravan",
    version="0.1.9",
    description="Frappe x Haravan Account for Frappe Helpdesk",
    author="Haravan",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests>=2.31.0"],
    zip_safe=False,
)
