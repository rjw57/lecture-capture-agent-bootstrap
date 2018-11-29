from setuptools import setup, find_packages

setup(
    name='birthscream',
    author='UIS DevOps',
    packages=find_packages(),
    install_requires=[
        'docopt',
        'netifaces',
        'requests',
        'wifi',
    ],
    entry_points={
        'console_scripts': [
            'birthscream=birthscream:main'
        ]
    },
)
