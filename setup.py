from setuptools import setup, find_packages

setup(
    name="telegram_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'telebot>=0.0.5',
        'python-dotenv>=1.0.0',
        'mistralai>=0.0.7',
        'SQLAlchemy>=2.0.23',
        'cryptography>=41.0.7',
        'schedule>=1.2.1',
        'pytest>=7.4.3',
        'black>=23.11.0',
        'isort>=5.12.0',
        'setuptools>=69.0.0'
    ]
)