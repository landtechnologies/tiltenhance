from tiltfile_runner import run_tiltfile_func, TiltConfig
from unittest.mock import Mock
import unittest
import pytest
import yaml


class DockerLocalTest(unittest.TestCase):
    def test_delegates_to_local_resource_for_build(self):
        local_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_local",
                          mocks={'local_resource': local_resource},
                          ref="my_image",
                          context="./path/to/dockerfile")

        local_resource.assert_any_call(
            "my_image_build", "docker build -t my_image ./path/to/dockerfile")

    def test_delegates_to_local_resource_for_run(self):
        local_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_local",
                          mocks={'local_resource': local_resource},
                          ref="my_image",
                          context="./path/to/dockerfile")

        local_resource.assert_called_with("my_image",
                                          "docker run --rm my_image",
                                          resource_deps=["my_image_build"])

    def test_adds_optional_recource_deps_to_run(self):
        local_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_local",
                          mocks={'local_resource': local_resource},
                          ref="my_image",
                          context="./path/to/dockerfile",
                          runtime_deps=["something", "else"])

        local_resource.assert_called_with(
            "my_image",
            "docker run --rm my_image",
            resource_deps=["something", "else", "my_image_build"])

    def test_adds_optional_env_vars_to_run(self):
        local_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_local",
                          mocks={'local_resource': local_resource},
                          ref="my_image",
                          context="./path/to/dockerfile",
                          env_vars={
                              "DOG": 1,
                              "CAT": "two"
                          })

        local_resource.assert_called_with(
            "my_image",
            'docker run --rm -e DOG="1" -e CAT="two" my_image',
            resource_deps=["my_image_build"])

    def test_adds_optional_run_command_array(self):
        local_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_local",
                          mocks={'local_resource': local_resource},
                          ref="my_image",
                          context="./path/to/dockerfile",
                          run_cmd=["sh", "echo", "hi"])

        local_resource.assert_called_with(
            "my_image",
            'docker run --rm my_image sh echo hi',
            resource_deps=["my_image_build"])


class DockerRemoteTest(unittest.TestCase):
    def test_delegates_to_docker_build_for_build(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          readiness_probe=None)

        docker_build.assert_called_with("my-image", "./path/to/dockerfile")

    def test_uses_repository_instead_if_provided(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          docker_repo="my.aws/repo",
                          build_context="./path/to/dockerfile",
                          readiness_probe=None)

        docker_build.assert_called_with("my.aws/repo", "./path/to/dockerfile")

    def test_generates_k8_yaml_job_with_defaults_for_image(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile")

        expected_spec = yaml.safe_load("""
          apiVersion: batch/v1
          kind: Job
          metadata:
            name: my-image
          spec:
            parallelism: 1
            completions: 1
            backoffLimit: 0
            template:
              metadata:
                annotations:
                  sidecar.istio.io/inject: "false"
              spec:
                containers:
                - name: main
                  image: my-image
                  readinessProbe:
                    exec:
                      command:
                        - 'false'
                    initialDelaySeconds: 120
                    periodSeconds: 120
                  resources:
                    requests:
                      cpu: 1
                      memory: 2056Mi
                    limits:
                      cpu: 1
                      memory: 2056Mi
                restartPolicy: Never
        """)

        assert k8s_yaml.call_count == 1
        print(k8s_yaml.call_args[0][0])
        assert yaml.safe_load(k8s_yaml.call_args[0][0]) == expected_spec

    def test_can_overwrite_resource_requirements(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          docker_repo="my.aws/repo",
                          build_context="./path/to/dockerfile",
                          cpu="2000m",
                          memory="4Gi",
                          readiness_probe=None)

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["spec"]["template"]["spec"]["containers"][0][
            "resources"] == yaml.safe_load("""
          requests:
            cpu: 2000m
            memory: 4Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        """)

    def test_includes_image_repo_if_provided(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          docker_repo="my.aws/repo",
                          build_context="./path/to/dockerfile",
                          readiness_probe=None)

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["spec"]["template"]["spec"]["containers"][0][
            "image"] == "my.aws/repo"

    def test_defines_k8_job_namespace_if_provided(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          namespace="somewhere",
                          readiness_probe=None)

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["metadata"]["namespace"] == "somewhere"

    def test_creates_dependent_k8s_resource_for_yaml(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          namespace="somewhere",
                          readiness_probe=None,
                          runtime_deps=["a", "b"])

        assert k8s_resource.call_count == 1
        k8s_resource.assert_called_with("my-image", resource_deps=["a", "b"])

    def test_passes_env_vars_to_container_spec(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          namespace="somewhere",
                          readiness_probe=None,
                          env_vars={
                              "DOG": 1,
                              "CAT": "two"
                          })

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["spec"]["template"]["spec"]["containers"][0][
            "env"] == yaml.safe_load("""
          - name: DOG
            value: 1
          - name: CAT
            value: two
        """)

    def test_creates_specified_readiness_probe(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          namespace="somewhere",
                          readiness_probe={"httpGet": {
                              "path": "/health"
                          }})

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["spec"]["template"]["spec"]["containers"][0][
            "readinessProbe"] == yaml.safe_load("""
          httpGet:
            path: /health
        """)

    def test_passes_command_array_to_container_spec(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          namespace="somewhere",
                          readiness_probe=None,
                          run_cmd=["bloop", "--something", "--another-thing"])

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["spec"]["template"]["spec"]["containers"][0]["args"] == [
            "bloop", "--something", "--another-thing"
        ]

    def test_adds_custom_pod_annotations(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_remote",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          namespace="somewhere",
                          annotations={
                              'custom': 'annotation'
                          })

        assert k8s_yaml.call_count == 1
        job = yaml.safe_load(k8s_yaml.call_args[0][0])
        assert job["spec"]["template"]["metadata"]["annotations"] == {
            "sidecar.istio.io/inject": "false",
            'custom': 'annotation'
        }

    def test_errors_if_resource_name_contains_invalid_char(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        with pytest.raises(Exception):
            run_tiltfile_func(
                "docker_task/Tiltfile",
                "docker_remote",
                mocks={
                    'docker_build': docker_build,
                    "k8s_yaml": k8s_yaml,
                    "k8s_resource": k8s_resource
                },
                ref="my_image",
                build_context="./path/to/dockerfile",
            )


class DockerTaskTest(unittest.TestCase):
    def test_delegates_to_local_resource_for_build(self):
        local_resource = Mock()
        k8s_yaml = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_task",
                          mocks={
                              'local_resource': local_resource,
                              'k8s_yaml': k8s_yaml
                          },
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          run_remote=False)

        local_resource.assert_any_call(
            "my-image_build", "docker build -t my-image ./path/to/dockerfile")
        k8s_yaml.call_count == 0

    def test_strips_out_non_local_args(self):
        local_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_task",
                          mocks={'local_resource': local_resource},
                          ref="my-image",
                          build_context="./path/to/dockerfile",
                          run_remote=False,
                          namespace="dave",
                          docker_repo="test",
                          readiness_probe="1234")

        local_resource.assert_any_call(
            "my-image_build", "docker build -t my-image ./path/to/dockerfile")

    def test_runs_on_remote(self):
        docker_build = Mock()
        k8s_yaml = Mock()
        k8s_resource = Mock()

        run_tiltfile_func("docker_task/Tiltfile",
                          "docker_task",
                          mocks={
                              'docker_build': docker_build,
                              "k8s_yaml": k8s_yaml,
                              "k8s_resource": k8s_resource
                          },
                          ref="my-image",
                          run_remote=True,
                          build_context="./path/to/dockerfile",
                          readiness_probe=None)

        assert k8s_yaml.call_count == 1
