from tiltfile_runner import run_tiltfile_func
from unittest.mock import Mock
import yaml


def test_excludes_test_and_rollback_hook_workloads():
  k8s_yaml = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_yaml': k8s_yaml}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave2
  namespace: test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave3
  namespace: test
  annotations:
    helm.sh/hook: test-success
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave4
  namespace: test
  annotations:
    helm.sh/hook: test-failure
""")

  saved_objs = yaml.safe_load_all(k8s_yaml.call_args.args[0])

  assert [obj["metadata"]["name"] for obj in saved_objs] == ["dave", "dave2"]

def test_errors_on_delete_hooks():
  fail = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'fail': fail}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave3
  namespace: test
  annotations:
    helm.sh/hook: pre-delete
""")

  assert fail.called

def test_makes_non_hook_workloads_dependent_on_pre_install_and_upgrade_hooks():
  k8s_resource = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_resource': k8s_resource}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave2
  namespace: test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave3
  namespace: test
  annotations:
    helm.sh/hook: pre-install
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave4
  namespace: test
  annotations:
    helm.sh/hook: pre-upgrade
""")

  assert k8s_resource.call_count == 2
  k8s_resource.assert_any_call(workload="dave:deployment:test", resource_deps=["dave3:deployment:test", "dave4:deployment:test"])
  k8s_resource.assert_any_call(workload="dave2:deployment:test", resource_deps=["dave3:deployment:test", "dave4:deployment:test"])

def test_makes_post_install_or_upgrade_hook_workloads_dependent_on_other_workloads():
  k8s_resource = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_resource': k8s_resource}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave3
  namespace: test
  annotations:
    helm.sh/hook: pre-install
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave4
  namespace: test
  annotations:
    helm.sh/hook: post-install
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave5
  namespace: test
  annotations:
    helm.sh/hook: post-upgrade
""")

  assert k8s_resource.call_count == 3
  k8s_resource.assert_any_call(workload="dave4:deployment:test", resource_deps=["dave:deployment:test", "dave3:deployment:test"])
  k8s_resource.assert_any_call(workload="dave5:deployment:test", resource_deps=["dave:deployment:test", "dave3:deployment:test"])

def test_doesnt_assign_deps_for_excluded_resources():
  k8s_resource = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_resource': k8s_resource}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
  annotations:
    helm.sh/hook: test-failure
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave3
  namespace: test
  annotations:
    helm.sh/hook: pre-install
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave4
  namespace: test
  annotations:
    helm.sh/hook: post-install
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave5
  namespace: test
  annotations:
    helm.sh/hook: post-upgrade
""")

  assert k8s_resource.call_count == 2
  k8s_resource.assert_any_call(workload="dave4:deployment:test", resource_deps=["dave3:deployment:test"])
  k8s_resource.assert_any_call(workload="dave5:deployment:test", resource_deps=["dave3:deployment:test"])

def test_doesnt_assign_pre_install_deps_when_no_dependencies():
  k8s_resource = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_resource': k8s_resource}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
""")

  assert k8s_resource.call_count == 0

def test_doesnt_assign_post_install_deps_when_no_dependencies():
  k8s_resource = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_resource': k8s_resource}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
  annotations:
    helm.sh/hook: post-install
""")

  assert k8s_resource.call_count == 0

def test_works_for_compound_hooks():
  k8s_resource = Mock()
  run_tiltfile_func("helm_hooks/Tiltfile", "helm_install_handle_hooks", mocks={'k8s_resource': k8s_resource}, yaml="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave3
  namespace: test
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave4
  namespace: test
  annotations:
    helm.sh/hook: post-install,post-upgrade
""")

  k8s_resource.assert_any_call(workload="dave:deployment:test", resource_deps=["dave3:deployment:test"])
  k8s_resource.assert_any_call(workload="dave4:deployment:test", resource_deps=["dave:deployment:test", "dave3:deployment:test"])
  assert k8s_resource.call_count == 2