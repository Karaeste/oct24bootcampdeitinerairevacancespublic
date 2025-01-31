import os
from functools import wraps
from airflow.models import Variable


def inject_vars_into_env(*var_names):
  """
  Decorator to inject specific Airflow Variables into the environment.
  If no variable names are provided, all variables are injected.
  """

  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      for var_name in var_names:
        value = Variable.get(var_name)
        os.environ[var_name] = value
      return func(*args, **kwargs)

    return wrapper

  return decorator
