from tiltfile_runner import run_tiltfile_func
import unittest
import os

class EnvTest(unittest.TestCase):

  def setUp(self):
    if os.path.exists(".tiltenv"):
      os.remove(".tiltenv")

  def test_saves_and_gets_values(self):
    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == None

    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1", val="test_val1")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test2", val="test_val2")

    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == "test_val1"
    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test2")
    assert val == "test_val2"

    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1", val="test_val3")
    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == "test_val3"

  def test_generates_and_saves_random_value(self):
    val1 = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get_or_random", key="test1")
    assert val1 is not None

    val2 = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get_or_random", key="test1")
    assert val1 == val2

    val3 = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get_or_random", key="test2")
    assert val1 != val3

  def test_adds_prefix_to_random_value(self):
    val1 = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get_or_random", key="test1", val_prefix="dave")
    assert val1.startswith("dave") == True

  def test_deletes_key(self):
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1", val="test_val1")

    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_delete", key="test1")

    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == None

  def test_delete_does_not_error_if_key_not_present(self):
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_delete", key="test1")


  def test_get_and_set_supports_dot_notation(self):
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1.a", val="test_val1")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1.b", val="test_val2")

    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    val2 = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1.a")
    val3 = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1.b")
    assert val == {
      'a': 'test_val1',
      'b': 'test_val2'
    }
    assert val2 == 'test_val1'
    assert val3 == 'test_val2'

  def test_get_dot_notation_handles_non_existent_keys_gracefully(self):
    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1.a.b")
    assert val == None

  def test_delete_supports_dot_notation(self):
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1.a", val="test_val1")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_set", key="test1.b", val="test_val2")

    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_delete", key="test1.a")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_delete", key="test1.a.b")

    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == {
      'b': 'test_val2'
    }

  def test_adds_to_list(self):
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_add", key="test1.a", val="test_val1")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_add", key="test1.a", val="test_val2")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_add", key="test1.b", val="test_val3")

    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == {
      'a': ['test_val1', 'test_val2'],
      'b': ['test_val3']
    }

  def test_removes_from_list(self):
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_add", key="test1.a", val="test_val1")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_add", key="test1.a", val="test_val2")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_remove", key="test1.a", val="test_val1")
    run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_list_remove", key="test2", val="test_val2")

    val = run_tiltfile_func("tilt_env/Tiltfile", "tilt_env_get", key="test1")
    assert val == {
      'a': ['test_val2']
    }
