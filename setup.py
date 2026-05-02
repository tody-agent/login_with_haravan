from setuptools import setup, find_packages

setup(
    name="login_with_haravan",
    version="0.1.12",
    description="Frappe x Haravan Account for Frappe Helpdesk",
    author="Haravan",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["requests>=2.31.0"],
    zip_safe=False,
)
