#!/usr/bin/env python3
import os
import re
import numpy as np
import sys
import rclpy
import open3d
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import importlib
from ament_index_python.packages import get_package_share_directory

_package_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../depth_simulation_publisher/synthetic_rgbd_camera_model'))
print(_package_dir)

if _package_dir not in sys.path:
    sys.path.insert(1, _package_dir)

from src.processor import ImageProcessor



class ImagePairPublisher(Node):
    def __init__(self, folder_path: str, scan_period: float = 1.0):
        super().__init__("image_pair_publisher")
        self.declare_parameter("rgb_topic", "/camera/rgb/image_raw")
        self.declare_parameter("depth_topic", "/camera/depth/image_raw")
        self.rgb_topic = self.get_parameter("rgb_topic").value
        self.depth_topic = self.get_parameter("depth_topic").value
        self.processor = ImageProcessor(
            params_path=os.path.join(_package_dir, 'params', 'femto_mega.json'),
        )

        # Publisher dla rgb i depth
        self.rgb_pub = self.create_publisher(Image, self.rgb_topic, 10)
        self.depth_pub = self.create_publisher(Image, self.depth_topic, 10)
        self.bridge = CvBridge()

        # Ścieżka do folderu z obrazami
        self.folder_path = folder_path
        if not os.path.isdir(self.folder_path):
            self.get_logger().error(
                f"Podana ścieżka nie istnieje lub nie jest folderem: {self.folder_path}"
            )
            rclpy.shutdown()
            return

        # Regularne wyrażenie do wyłuskania indeksu i
        self.rgb_pattern = re.compile(r"rgb_(\d+)\.png$")
        self.depth_pattern = re.compile(r"depth_(\d+)\.png$")

        # Numer ostatnio opublikowanej pary
        self.last_published_idx = -1

        # Timer do periodycznego sprawdzania folderu
        self.timer = self.create_timer(scan_period, self.timer_callback)
        self.get_logger().info(
            f"Uruchomiono ImagePairPublisher, skanując folder: {self.folder_path}"
        )

    def timer_callback(self):
        """
        Co scan_period sekund:
        - listowanie plików w folderze,
        - znalezienie tych, które mają obie pary (rgb_i i depth_i),
        - wybranie największego i > last_published_idx,
        - wczytanie obrazów i publikacja.
        """
        try:
            all_files = os.listdir(self.folder_path)
        except Exception as e:
            self.get_logger().error(f"Nie można odczytać folderu: {e}")
            return

        rgb_indices = set()
        depth_indices = set()

        # Zebrane indeksy z plików rgb_i.png
        for fname in all_files:
            m = self.rgb_pattern.match(fname)
            if m:
                rgb_indices.add(int(m.group(1)))

        # Zebrane indeksy z plików depth_i.png
        for fname in all_files:
            m = self.depth_pattern.match(fname)
            if m:
                depth_indices.add(int(m.group(1)))

        # Indeksy, dla których mamy obie grafiki
        common_indices = rgb_indices.intersection(depth_indices)
        if not common_indices:
            return  # nic do roboty

        latest_idx = max(common_indices)
        if latest_idx <= self.last_published_idx:
            return  # brak nowego

        # Wczytujemy pliki rgb_latest_idx.png i depth_latest_idx.png
        rgb_path = os.path.join(self.folder_path, f"rgb_{latest_idx}.png")
        depth_path = os.path.join(self.folder_path, f"depth_{latest_idx}.png")
        self.get_logger().info(f"{rgb_path}, {depth_path}")
        rgb_image, depth_image = self.processor.process_single_img_pair_no_save(
            rgb_path, depth_path
        )

        # Konwersja do wiadomości ROS Image
        try:
            ros_rgb = self.bridge.cv2_to_imgmsg(rgb_image, encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"Błąd konwersji RGB do Image: {e}")
            return

        # Zakładamy, że depth to 16-bit PNG (np. z Kinecta, ZED itp.)
        # Jeśli depth jest 8-bit (mono), zmień encoding na 'mono8'
        depth_dtype = depth_image.dtype
        if depth_dtype == np.uint16:
            depth_encoding = "16UC1"
        elif depth_dtype == np.uint8:
            depth_encoding = "mono8"
        else:
            # Jeżeli inny typ, spróbujemy wymusić 16UC1
            depth_image = depth_image.astype(np.uint16)
            depth_encoding = "16UC1"

        try:
            ros_depth = self.bridge.cv2_to_imgmsg(depth_image, encoding=depth_encoding)
        except Exception as e:
            self.get_logger().error(f"Błąd konwersji Depth do Image: {e}")
            return

        # Ustawiamy timestamp i wysyłamy na topic
        now = self.get_clock().now().to_msg()
        ros_rgb.header.stamp = now
        ros_depth.header.stamp = now

        self.rgb_pub.publish(ros_rgb)
        self.depth_pub.publish(ros_depth)
        self.get_logger().info(f"Opublikowano parę obrazów o indexie {latest_idx}")

        # Aktualizujemy ostatni opublikowany indeks
        self.last_published_idx = latest_idx


def main(args=None):
    rclpy.init(args=args)

    # Odczytujemy folder z argumentu linii komend.
    # Jeśli nie podano, przyjmujemy bieżący katalog.
    folder_to_watch = "/home/maciej_br/mgr/renders/rendered"
    if len(sys.argv) > 1:
        folder_to_watch = sys.argv[1]

    node = ImagePairPublisher(folder_to_watch, scan_period=1.0)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info("Zamykanie węzła ImagePairPublisher...")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
