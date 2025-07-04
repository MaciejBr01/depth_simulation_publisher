from setuptools import find_packages, setup
from glob import glob
import os
package_name = "depth_simulation_publisher"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # ("lib/" + package_name, glob("depth_simulation_publisher/synthetic_rgbd_camera_model/*.py"))
        (os.path.join('lib/', package_name, 'synthetic_rgbd_camera_model'), glob("depth_simulation_publisher/synthetic_rgbd_camera_model/*.py")),
        (os.path.join('lib/', package_name, 'synthetic_rgbd_camera_model', "src"), glob("depth_simulation_publisher/synthetic_rgbd_camera_model/src/*.py")),
        (os.path.join('lib/', package_name, 'synthetic_rgbd_camera_model', "params"), glob("depth_simulation_publisher/synthetic_rgbd_camera_model/params/*.json")),
    ],
    install_requires=[
        "setuptools",
        "rclpy",
        "sensor_msgs",
        "cv_bridge",
        "numpy",
        "opencv-python",
        "open3d",
    ],
    zip_safe=True,
    maintainer="maciej_br",
    maintainer_email="maciekbraszkiewicz@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "render_publisher = depth_simulation_publisher.render_publisher:main"
        ],
    },
)
