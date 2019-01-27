from setuptools import setup, find_packages

requires = [
    'pyramid',
    'waitress',
    'paste',
    'pyaml',
    'slacker',
    'pytz',
    'python-dateutil',
]

setup(
    name='webhook_alerter',
    version='0.0',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Ben Walker',
    author_email='ben@benstwa.co.uk',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires,
    entry_points={
        'console_scripts': [
            'start-webhook-alerter = webhook_alerter.app:main'
        ]
    }
)
