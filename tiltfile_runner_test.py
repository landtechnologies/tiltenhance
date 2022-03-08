import pytest
from unittest.mock import Mock
from tiltfile_runner import run_tiltfile_func

def test_runs_basic_tiltfile():
  result = run_tiltfile_func("test/basic/Tiltfile", "simple", arg=10)
  assert result == 11

def test_handles_local_file_imports():
  result = run_tiltfile_func("test/load/Tiltfile", "test_func", arg=15)
  assert result == 16

def test_doesnt_pollute_scope_with_non_imported_functions():
  with pytest.raises(NameError):
    run_tiltfile_func("test/load/failure/Tiltfile", "test_func", arg=15)

def test_handles_multiple_function_imports():
  result = run_tiltfile_func("test/load/multi_import/Tiltfile", "test_func", arg=15)
  assert result == 15

def test_handles_ext_package_imports():
  result = run_tiltfile_func("test/load/ext/Tiltfile", "test_func", str="hi")
  assert result == "hi"

def test_can_mock_functions():
  k8s_yaml = Mock()
  run_tiltfile_func("test/mock/Tiltfile", "mock_a_function", mocks={'k8s_yaml': k8s_yaml}, arg="hi")
  assert k8s_yaml.call_count == 1
  k8s_yaml.assert_any_call("hi")

def test_imports_should_not_pollute_global_scope():
  run_tiltfile_func("test/load/multi_import/Tiltfile", "test_func", arg=15)
  with pytest.raises(NameError):
    run_tiltfile_func("test/load/failure/Tiltfile", "test_func", arg=15)

def test_mocks_do_not_bleed_scope():
  fail = Mock()
  run_tiltfile_func("test/fail/Tiltfile", "should_fail", mocks={'fail': fail})

  with pytest.raises(Exception):
    run_tiltfile_func("test/fail/Tiltfile", "should_fail")