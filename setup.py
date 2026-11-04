from setuptools import setup

package_name = 'bag_tools'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    extras_require={'test': ['pytest']},
    zip_safe=True,
    maintainer='Dimitri Ackermann',
    maintainer_email='dimitri.ackermann@googlemail.com',
    description='Action servers that record MCAP bags into datasets/ and replay them.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'bag_recorder = bag_tools.bag_recorder:main',
            'bag_player = bag_tools.bag_player:main',
        ],
    },
)
