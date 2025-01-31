import os
import pickle
import gzip
import redis

default_port = 6379
default_db = 0
default_expiration = 1800


def _redis():
  host = os.environ['REDIS_HOST']
  port = int(os.environ.get('REDIS_PORT', str(default_port)))
  db = int(os.environ.get('REDIS_DB', str(default_db)))
  return redis.Redis(host=host, port=port, db=db)


def object_store(name: str, data: object) -> str:
  f"""
  Store an object in redis

  :Environment Variables:
    - **REDIS_HOST** (str): The hostname of the redis server.
    - **REDIS_PORT** (int): The port number of the redis server (default to {default_port}).
    - **REDIS_DB** (int): The database number for object storage (default to {default_db}).
    - **REDIS_EXPIRATION** (int): The expiration time of the object (default to {default_expiration}).
  :param name: name of the object
  :param data: value of the object
  :return: the name of the object
  """
  compressed = gzip.compress(pickle.dumps(data))
  expiration = int(os.environ.get('REDIS_EXPIRATION', str(default_expiration)))
  _redis().set(name, compressed, ex=expiration)
  return name


def object_read(name: str):
  f"""
  Read an object in redis

  :Environment Variables:
    - **REDIS_HOST** (str): The hostname of the redis server.
    - **REDIS_PORT** (int): The port number of the redis server (default to {default_port}).
    - **REDIS_DB** (int): The database number for object storage (default to {default_db}).
  :param name: name of the object
  :return: the stored value
  """
  compressed = _redis().get(name)
  return None if compressed is None else pickle.loads(gzip.decompress(compressed))


def object_delete(name: str) -> str:
  f"""
  Delete an object in redis

  :Environment Variables:
    - **REDIS_HOST** (str): The hostname of the redis server.
    - **REDIS_PORT** (int): The port number of the redis server (default to {default_port}).
    - **REDIS_DB** (int): The database number for object storage (default to {default_db}).
  :param name: name of the object to delete
  :return: the name of the object deleted
  """
  _redis().delete(name)
  return name
