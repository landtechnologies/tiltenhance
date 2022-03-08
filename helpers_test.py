from tiltfile_runner import run_tiltfile_func
import unittest
import pytest

def gen_service(name, ports=[("test", 1234)], namespace="dave"):
  port_str = '\n'.join([f"""
  - name: {port_name}
    port: {port}
    protocol: TCP
    targetPort: test
  """ for port_name, port in ports])
  return f"""
apiVersion: apps/v1
kind: Service
metadata:
  name: {name}
  namespace: test
spec:
  ports:
{port_str}
"""

class GetServiceUrlTest(unittest.TestCase):

  def test_it_finds_single_service_and_port(self):
    url = run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
      yaml=f"""
{gen_service("dave")}
"""
    )

    assert url == "dave.test:1234"

  def test_it_fails_if_multiple_services(self):
    with pytest.raises(Exception, match=r".*Tiltfile failed.*"):
      run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
        yaml=f"""
{gen_service("dave")}
---
{gen_service("dave2")}
"""
      )

  def test_it_fails_if_no_services_found(self):
    with pytest.raises(Exception, match=r".*Tiltfile failed.*"):
      run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
        yaml=f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dave
  namespace: test
"""
      )

  def test_it_fails_if_multiple_ports(self):
    with pytest.raises(Exception, match=r".*Tiltfile failed.*"):
      run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
        yaml=f"""
{gen_service("dave", [("test", 1234), ("test2", 5678)])}
"""
      )

  def test_it_fails_if_no_ports(self):
    with pytest.raises(Exception, match=r".*Tiltfile failed.*"):
      run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
        yaml=f"""
apiVersion: apps/v1
kind: Service
metadata:
  name: "dave"
  namespace: test
spec:
  ports: []
"""
      )

  def test_it_can_match_service_on_name(self):
    url = run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
      service_name="dave",
      yaml=f"""
{gen_service("dave")}
---
{gen_service("dave2")}
"""
    )

    assert url == "dave.test:1234"

  def test_it_can_match_port_on_name(self):
    url = run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
      port="port1",
      yaml=f"""
{gen_service("dave", [("port1", 1234), ("port2", 5678)])}
"""
    )

    assert url == "dave.test:1234"

  def test_it_can_match_port_on_number(self):
    url = run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
      port=1234,
      yaml=f"""
{gen_service("dave", [("port1", 1234), ("port2", 5678)])}
"""
    )

    assert url == "dave.test:1234"

#   def test_it_fails_if_multiple_services(self):
#     with pytest.raises(Exception, match=r".*Tiltfile failed.*"):
#       run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
#         yaml="""
# apiVersion: apps/v1
# kind: Service
# metadata:
#   name: dave
#   namespace: test
# spec:
#   ports:
#   - name: test
#     port: 6379
#     protocol: TCP
#     targetPort: test
# ---
# apiVersion: apps/v1
# kind: Service
# metadata:
#   name: dave2
#   namespace: test
# spec:
#   ports:
#   - name: test
#     port: 6379
#     protocol: TCP
#     targetPort: test
#   """
#       )

#   def test_it_fails_if_multiple_ports(self):
#     with pytest.raises(Exception, match=r".*Tiltfile failed.*"):
#       run_tiltfile_func("helpers/Tiltfile", "get_service_url", 
#         yaml="""
# apiVersion: apps/v1
# kind: Service
# metadata:
#   name: dave
#   namespace: test
# spec:
#   ports:
#   - name: test
#     port: 6379
#     protocol: TCP
#     targetPort: test
#   - name: test2
#     port: 6380
#     protocol: TCP
#     targetPort: test2
#   """
#       )