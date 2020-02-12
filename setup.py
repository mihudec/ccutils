from setuptools import setup, find_packages

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name='ccutils',
    version='0.1.4',
    packages=find_packages(exclude=["test", "examples"]),
    url='https://bitbucket.org/mijujda/ccutils',
    license='',
    author='Miroslav Hudec',
    author_email='mijujda@gmail.com',
    description='Cisco Configuration Utilities',
    install_requires=reqs,
    include_package_data=True
)
