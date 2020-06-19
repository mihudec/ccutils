from setuptools import setup, find_packages

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name='ccutils',
    version='0.2.8',
    packages=find_packages(exclude=["test", "examples"]),
    url='https://github.org/mihudec/ccutils',
    license='',
    author='Miroslav Hudec',
    author_email='mijujda@gmail.com',
    description='Cisco Configuration Utilities',
    install_requires=reqs,
    include_package_data=True
)
