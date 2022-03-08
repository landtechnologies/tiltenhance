from tiltfile_runner import run_tiltfile_func, TiltConfig, local
from unittest.mock import Mock
import unittest
import os
import boto3
from botocore.client import ClientError
import pytest
import credstash
import random
import string

s3 = boto3.resource('s3')
ecr = boto3.client('ecr')

STATIC_PREFIX = 'tilt'


def random_string(n):
    return ''.join(random.choices(string.ascii_uppercase + string.digits,
                                  k=n)).lower()


def local_resource_integration(name, cmd):
    local(cmd)


def test_delegates_to_local_resource_when_not_tilt_down():
    local_resource = Mock()
    on_destroy = Mock()
    run_tiltfile_func("local_resource_ext/Tiltfile",
                      "local_resource_ext",
                      mocks={'local_resource': local_resource},
                      name="my_resource",
                      cmd="something",
                      on_destroy=on_destroy,
                      random="kwarg")

    assert local_resource.call_count == 1
    local_resource.assert_called_with("my_resource",
                                      "something",
                                      random="kwarg")
    assert on_destroy.call_count == 0

def test_executes_on_destroy_when_tilt_down():
    local_resource = Mock()
    on_destroy = Mock()

    run_tiltfile_func("local_resource_ext/Tiltfile",
                      "local_resource_ext",
                      mocks={
                          'local_resource': local_resource,
                          'config': TiltConfig('down')
                      },
                      name="my_resource",
                      cmd="something",
                      on_destroy=on_destroy,
                      random="kwarg")
    assert on_destroy.call_count == 1

def test_registers_null_resource_on_tilt_down():
    local_resource = Mock()
    on_destroy = Mock()

    run_tiltfile_func("local_resource_ext/Tiltfile",
                      "local_resource_ext",
                      mocks={
                          'local_resource': local_resource,
                          'config': TiltConfig('down')
                      },
                      name="my_resource",
                      cmd="something",
                      on_destroy=on_destroy,
                      random="kwarg")
    assert local_resource.call_count == 1
    local_resource.assert_called_with("my_resource", "true")
class S3BucketUnitTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(".tiltenv"):
            os.remove(".tiltenv")

    def test_it_creates_s3_bucket_name_if_not_present(self):
        local_resource = Mock()

        bucket_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={'local_resource': local_resource},
            resource_name="my_bucket",
        )

        assert local_resource.call_count == 1
        assert local_resource.call_args[0][0] == "my_bucket"
        assert bucket_name in local_resource.call_args[0][1]

    def test_it_uses_s3_bucket_name_if_present(self):
        local_resource = Mock()

        run_tiltfile_func("tilt_env/Tiltfile",
                          "tilt_env_set",
                          key="my_bucket",
                          val="bucket_id")

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={'local_resource': local_resource},
            resource_name="my_bucket",
        )

        assert local_resource.call_count == 1
        assert local_resource.call_args[0][0] == "my_bucket"
        assert "bucket_id" in local_resource.call_args[0][1]


class S3BucketIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.prefix = f"{STATIC_PREFIX}-{random_string(15)}-"
        os.environ['TEST_BUCKET_PREFIX'] = self.prefix
        if os.path.exists(".tiltenv"):
            os.remove(".tiltenv")

    def tearDown(self):
        for bucket in s3.buckets.all():
            if len(self.prefix) > len(
                    STATIC_PREFIX) and bucket.name.startswith(self.prefix):
                bucket.delete()

    def test_creates_bucket_on_first_run(self):
        bucket_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_bucket",
        )

        s3.meta.client.head_bucket(Bucket=bucket_name)

    def test_noop_on_second_run(self):
        bucket_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_bucket",
        )

        bucket_name2 = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_bucket",
        )

        assert bucket_name == bucket_name2
        s3.meta.client.head_bucket(Bucket=bucket_name)

    def test_deletes_on_teardown(self):
        bucket_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_bucket",
        )

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down')
            },
            resource_name="my_bucket",
        )

        with pytest.raises(ClientError):
            s3.meta.client.head_bucket(Bucket=bucket_name)
        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_bucket") == None

    def test_doesnt_fail_teardown_if_bucket_is_not_created(self):
        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "s3_bucket",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down')
            },
            resource_name="my_bucket",
        )

        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_bucket") == None


class ECRRepoUnitTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(".tiltenv"):
            os.remove(".tiltenv")

    def test_it_creates_ecr_repo_name_if_not_present(self):
        local_resource = Mock()

        repo_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource},
            resource_name="my_repo",
        )

        assert local_resource.call_count == 1
        assert local_resource.call_args[0][0] == "my_repo"
        assert repo_name in local_resource.call_args[0][1]

    def test_it_uses_ecr_repo_name_if_present(self):
        local_resource = Mock()

        run_tiltfile_func("tilt_env/Tiltfile",
                          "tilt_env_set",
                          key="my_repo",
                          val="repo_id")

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource},
            resource_name="my_repo",
        )

        assert local_resource.call_count == 1
        assert local_resource.call_args[0][0] == "my_repo"
        assert "repo_id" in local_resource.call_args[0][1]


class ECRRepoIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.prefix = f"{STATIC_PREFIX}-{random_string(15)}-"
        os.environ['TEST_REPO_PREFIX'] = self.prefix
        if os.path.exists(".tiltenv"):
            os.remove(".tiltenv")

    def tearDown(self):
        for repo in ecr.describe_repositories()['repositories']:
            name = repo['repositoryName']
            if len(self.prefix) > len(STATIC_PREFIX) and name.startswith(
                    self.prefix):
                ecr.delete_repository(repositoryName=name, force=True)

    def test_creates_repo_on_first_run(self):
        repo_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_repo",
        )

        ecr.describe_repositories(repositoryNames=[repo_name])

    def test_noop_on_second_run(self):
        repo_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_repo",
        )

        repo_name2 = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_repo",
        )

        assert repo_name == repo_name2
        ecr.describe_repositories(repositoryNames=[repo_name])

    def test_deletes_on_teardown(self):
        repo_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_repo",
        )

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down')
            },
            resource_name="my_repo",
        )

        with pytest.raises(ClientError):
            ecr.describe_repositories(repositoryNames=[repo_name])
        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_repo") == None


    def test_does_not_delete_presistent_repo_on_teardown(self):
        repo_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_repo",
            persistent=True
        )

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down')
            },
            resource_name="my_repo",
            persistent=True
        )

        ecr.describe_repositories(repositoryNames=[repo_name])
        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_repo") == repo_name

    
    def test_force_delete_presistent_repo_on_teardown(self):
        repo_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_repo",
            persistent=True
        )

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down', {'delete-persistent-repos': True})
            },
            resource_name="my_repo",
            persistent=True
        )
        
        with pytest.raises(ClientError):
            ecr.describe_repositories(repositoryNames=[repo_name])
        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_repo") == None

    def test_doesnt_fail_teardown_if_repo_is_not_created(self):
        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "ecr_repo",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down')
            },
            resource_name="my_repo",
        )

        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_repo") == None


class CredstashKeyUnitTest(unittest.TestCase):
    def setUp(self):
        if os.path.exists(".tiltenv"):
            os.remove(".tiltenv")

    def test_it_creates_credstash_key_name_if_not_present(self):
        local_resource = Mock()

        key_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={'local_resource': local_resource},
            resource_name="my_key",
            val="my_secret",
        )

        assert local_resource.call_count == 1
        assert local_resource.call_args[0][0] == "my_key"
        assert key_name in local_resource.call_args[0][1]
        assert "my_secret" in local_resource.call_args[0][1]

    def test_it_uses_credstash_key_name_if_present(self):
        local_resource = Mock()

        run_tiltfile_func("tilt_env/Tiltfile",
                          "tilt_env_set",
                          key="my_key",
                          val="key_name")

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={'local_resource': local_resource},
            resource_name="my_key",
            val="my_secret",
        )

        assert local_resource.call_count == 1
        assert local_resource.call_args[0][0] == "my_key"
        assert "key_name" in local_resource.call_args[0][1]
        assert "my_secret" in local_resource.call_args[0][1]


class CredstashKeyIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.prefix = f"tilt/{random_string(15)}-"
        os.environ['TEST_CREDSTASH_PREFIX'] = self.prefix
        if os.path.exists(".tiltenv"):
            os.remove(".tiltenv")

    def tearDown(self):
        secretKeys = set([key['name'] for key in credstash.listSecrets()])
        for secret in secretKeys:
            if secret.startswith(self.prefix):
                credstash.deleteSecrets(secret)

    def test_creates_key_on_first_run(self):
        key_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_key",
            val="my_secret",
        )

        assert credstash.getSecret(key_name) == 'my_secret'

    def test_upserts_on_second_run(self):
        key_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_key",
            val="my_secret",
        )

        key_name2 = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_key",
            val="my_new_secret",
        )

        assert key_name == key_name2
        assert credstash.getSecret(key_name) == 'my_new_secret'

    def test_deletes_on_teardown(self):
        key_name = run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={'local_resource': local_resource_integration},
            resource_name="my_key",
            val="my_secret",
        )

        run_tiltfile_func(
            "local_resource_ext/Tiltfile",
            "credstash_key",
            mocks={
                'local_resource': local_resource_integration,
                'config': TiltConfig('down')
            },
            resource_name="my_key",
            val="my_secret",
        )

        with pytest.raises(credstash.ItemNotFound):
            credstash.getSecret(key_name)
        assert run_tiltfile_func("tilt_env/Tiltfile",
                                 "tilt_env_get",
                                 key="my_key") == None
