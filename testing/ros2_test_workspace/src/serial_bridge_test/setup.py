from setuptools import find_packages, setup

package_name = 'serial_bridge_test'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nathaniel',
    maintainer_email='erdzean.nathaniel.sybico@example.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'dir_pub = serial_bridge_test.direction_publisher:main',
            'direction_to_serial = serial_bridge_test.direction_to_serial:main'
        ],
    },
)
