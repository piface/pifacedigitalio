from distutils.core import setup


setup(
    name='pifacedigitalio',
    version='1.1',
    description='The PiFace Digital I/O module.',
    author='Thomas Preston',
    author_email='thomasmarkpreston@gmail.com',
    url='https://github.com/piface/pifacedigitalio',
    py_modules=['pifacedigitalio'],
    long_description="pifacedigitalio provides functions and classes for "
        "interfacing with PiFace Digital board.",
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='piface digital raspberrypi openlx',
    license='GPLv3+',
    requires=[
        'pifacecommon',
    ]
)
