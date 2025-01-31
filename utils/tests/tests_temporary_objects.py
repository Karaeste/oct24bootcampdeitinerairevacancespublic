import os
import unittest
import time
from testcontainers.redis import RedisContainer
from testcontainers.core.waiting_utils import wait_for_logs
from utils import object_store, object_read, object_delete


class TestTemporaryObjects(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.redis_container = RedisContainer("redis:latest")
    cls.redis_container.start()
    wait_for_logs(cls.redis_container, "Ready to accept connections")
    os.environ["REDIS_HOST"] = cls.redis_container.get_container_host_ip()
    os.environ["REDIS_PORT"] = str(cls.redis_container.get_exposed_port(cls.redis_container.port))

  @classmethod
  def tearDownClass(cls):
    cls.redis_container.stop()

  def test_store_and_read_big_data(self):
    data = list(os.urandom(10000000))
    os.environ['REDIS_EXPIRATION'] = '3600'
    self.assertEqual(data, object_read(object_store("abc", data)))

  def test_store_and_auto_delete(self):
    data = list(os.urandom(100))
    os.environ['REDIS_EXPIRATION'] = '5'
    name = object_store('xyz', data)
    self.assertEqual(data, object_read(name))
    time.sleep(5)
    self.assertEqual(None, object_read(name))

  def test_store_and_delete(self):
    data = list(os.urandom(100))
    os.environ['REDIS_EXPIRATION'] = '3600'
    name = object_store('ijk', data)
    self.assertEqual(data, object_read(name))
    time.sleep(5)
    self.assertEqual(data, object_read(name))
    object_delete(name)
    self.assertEqual(None, object_read(name))


if __name__ == "__main__":
  unittest.main()
