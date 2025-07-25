# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import datetime
from unittest.mock import MagicMock, call, patch

import pytest

yandexcloud = pytest.importorskip("yandexcloud")

from airflow.models.dag import DAG
from airflow.providers.yandex.operators.dataproc import (
    DataprocCreateClusterOperator,
    DataprocCreateHiveJobOperator,
    DataprocCreateMapReduceJobOperator,
    DataprocCreatePysparkJobOperator,
    DataprocCreateSparkJobOperator,
    DataprocDeleteClusterOperator,
)

# Airflow connection with type "yandexcloud"
CONNECTION_ID = "yandexcloud_default"

# Name of the datacenter where Dataproc cluster will be created
AVAILABILITY_ZONE_ID = "ru-central1-c"

CLUSTER_NAME = "dataproc_cluster"
CLUSTER_IMAGE_VERSION = "1.4"

# https://cloud.yandex.com/docs/resource-manager/operations/folder/get-id
FOLDER_ID = "my_folder_id"

# Subnetwork id should belong to the availability zone set above
SUBNET_ID = "my_subnet_id"

# Dataproc cluster jobs will produce logs in specified s3 bucket
S3_BUCKET_NAME_FOR_LOGS = "my_bucket_name"

# https://cloud.yandex.com/docs/iam/concepts/users/service-accounts
SERVICE_ACCOUNT_ID = "my_service_account_id"

# https://cloud.yandex.com/docs/iam/concepts/authorization/oauth-token
OAUTH_TOKEN = "my_oauth_token"

# Ssh public keys will be placed to Dataproc cluster nodes, allowing to get a root shell at the nodes
SSH_PUBLIC_KEYS = [
    "ssh-rsa AAA5B3NzaC1yc2EAA1ADA2ABA3AA4QCxO38tKA0XIs9ivPxt7AYdf3bgtAR1ow3Qkb9GPQ6wkFHQq"
    "cFDe6faKCxH6iDRt2o4D8L8Bx6zN42uZSB0nf8jkIxFTcEU3mFSXEbWByg78ao3dMrAAj1tyr1H1pON6P0="
]

# https://cloud.yandex.com/docs/logging/concepts/log-group
LOG_GROUP_ID = "my_log_group_id"

try:
    import importlib.util

    if not importlib.util.find_spec("airflow.sdk.bases.hook"):
        raise ImportError

    BASEHOOK_PATCH_PATH = "airflow.sdk.bases.hook.BaseHook"
except ImportError:
    BASEHOOK_PATCH_PATH = "airflow.hooks.base.BaseHook"


class TestDataprocClusterCreateOperator:
    def setup_method(self):
        dag_id = "test_dag"
        self.dag = DAG(
            dag_id,
            default_args={
                "owner": "airflow",
                "start_date": datetime.datetime.today(),
                "end_date": datetime.datetime.today() + datetime.timedelta(days=1),
            },
            schedule="@daily",
        )

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.create_cluster")
    @patch("yandexcloud.__version__", "0.308.0")
    def test_create_cluster(self, mock_create_cluster, *_):
        operator = DataprocCreateClusterOperator(
            task_id="create_cluster",
            ssh_public_keys=SSH_PUBLIC_KEYS,
            folder_id=FOLDER_ID,
            subnet_id=SUBNET_ID,
            zone=AVAILABILITY_ZONE_ID,
            connection_id=CONNECTION_ID,
            s3_bucket=S3_BUCKET_NAME_FOR_LOGS,
            cluster_image_version=CLUSTER_IMAGE_VERSION,
            log_group_id=LOG_GROUP_ID,
        )
        context = {"task_instance": MagicMock()}
        operator.execute(context)
        mock_create_cluster.assert_called_once_with(
            cluster_description="",
            cluster_image_version="1.4",
            cluster_name=None,
            computenode_count=0,
            computenode_disk_size=None,
            computenode_disk_type=None,
            computenode_resource_preset=None,
            computenode_max_hosts_count=None,
            computenode_measurement_duration=None,
            computenode_warmup_duration=None,
            computenode_stabilization_duration=None,
            computenode_preemptible=False,
            computenode_cpu_utilization_target=None,
            computenode_decommission_timeout=None,
            datanode_count=1,
            datanode_disk_size=None,
            datanode_disk_type=None,
            datanode_resource_preset=None,
            folder_id="my_folder_id",
            masternode_disk_size=None,
            masternode_disk_type=None,
            masternode_resource_preset=None,
            s3_bucket="my_bucket_name",
            service_account_id=None,
            services=("HDFS", "YARN", "MAPREDUCE", "HIVE", "SPARK"),
            ssh_public_keys=[
                "ssh-rsa AAA5B3NzaC1yc2EAA1ADA2ABA3AA4QCxO38tKA0XIs9ivPxt7AYdf3bgtAR1ow3Qkb9GPQ6wkFHQq"
                "cFDe6faKCxH6iDRt2o4D8L8Bx6zN42uZSB0nf8jkIxFTcEU3mFSXEbWByg78ao3dMrAAj1tyr1H1pON6P0="
            ],
            subnet_id="my_subnet_id",
            zone="ru-central1-c",
            log_group_id=LOG_GROUP_ID,
            properties=None,
            enable_ui_proxy=False,
            host_group_ids=None,
            security_group_ids=None,
            labels=None,
            initialization_actions=None,
        )
        context["task_instance"].xcom_push.assert_has_calls(
            [
                call(key="cluster_id", value=mock_create_cluster().response.id),
                call(key="yandexcloud_connection_id", value=CONNECTION_ID),
            ]
        )

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.create_cluster")
    @patch("yandexcloud.__version__", "0.350.0")
    def test_create_cluster_with_350_sdk(self, mock_create_cluster, *_):
        operator = DataprocCreateClusterOperator(
            task_id="create_cluster",
            ssh_public_keys=SSH_PUBLIC_KEYS,
            folder_id=FOLDER_ID,
            subnet_id=SUBNET_ID,
            zone=AVAILABILITY_ZONE_ID,
            connection_id=CONNECTION_ID,
            s3_bucket=S3_BUCKET_NAME_FOR_LOGS,
            cluster_image_version=CLUSTER_IMAGE_VERSION,
            log_group_id=LOG_GROUP_ID,
        )
        context = {"task_instance": MagicMock()}
        operator.execute(context)
        mock_create_cluster.assert_called_once_with(
            cluster_description="",
            cluster_image_version="1.4",
            cluster_name=None,
            computenode_count=0,
            computenode_disk_size=None,
            computenode_disk_type=None,
            computenode_resource_preset=None,
            computenode_max_hosts_count=None,
            computenode_measurement_duration=None,
            computenode_warmup_duration=None,
            computenode_stabilization_duration=None,
            computenode_preemptible=False,
            computenode_cpu_utilization_target=None,
            computenode_decommission_timeout=None,
            datanode_count=1,
            datanode_disk_size=None,
            datanode_disk_type=None,
            datanode_resource_preset=None,
            folder_id="my_folder_id",
            masternode_disk_size=None,
            masternode_disk_type=None,
            masternode_resource_preset=None,
            s3_bucket="my_bucket_name",
            service_account_id=None,
            services=("HDFS", "YARN", "MAPREDUCE", "HIVE", "SPARK"),
            ssh_public_keys=[
                "ssh-rsa AAA5B3NzaC1yc2EAA1ADA2ABA3AA4QCxO38tKA0XIs9ivPxt7AYdf3bgtAR1ow3Qkb9GPQ6wkFHQq"
                "cFDe6faKCxH6iDRt2o4D8L8Bx6zN42uZSB0nf8jkIxFTcEU3mFSXEbWByg78ao3dMrAAj1tyr1H1pON6P0="
            ],
            subnet_id="my_subnet_id",
            zone="ru-central1-c",
            log_group_id=LOG_GROUP_ID,
            properties=None,
            enable_ui_proxy=False,
            host_group_ids=None,
            security_group_ids=None,
            labels=None,
            initialization_actions=None,
            environment=None,
            oslogin_enabled=False,
        )
        context["task_instance"].xcom_push.assert_has_calls(
            [
                call(key="cluster_id", value=mock_create_cluster().response.id),
                call(key="yandexcloud_connection_id", value=CONNECTION_ID),
            ]
        )

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.delete_cluster")
    def test_delete_cluster_operator(self, mock_delete_cluster, *_):
        operator = DataprocDeleteClusterOperator(
            task_id="delete_cluster",
            connection_id=CONNECTION_ID,
        )
        context = {"task_instance": MagicMock()}
        context["task_instance"].xcom_pull.return_value = "my_cluster_id"
        operator.execute(context)
        context["task_instance"].xcom_pull.assert_called_once_with(key="cluster_id")
        mock_delete_cluster.assert_called_once_with("my_cluster_id")

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.create_hive_job")
    def test_create_hive_job_operator(self, mock_create_hive_job, *_):
        operator = DataprocCreateHiveJobOperator(
            task_id="create_hive_job",
            query="SELECT 1;",
            connection_id=CONNECTION_ID,
        )
        context = {"task_instance": MagicMock()}
        context["task_instance"].xcom_pull.return_value = "my_cluster_id"
        operator.execute(context)

        context["task_instance"].xcom_pull.assert_has_calls(
            [
                call(key="cluster_id"),
            ]
        )

        mock_create_hive_job.assert_called_once_with(
            cluster_id="my_cluster_id",
            continue_on_failure=False,
            name="Hive job",
            properties=None,
            query="SELECT 1;",
            query_file_uri=None,
            script_variables=None,
        )

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.create_mapreduce_job")
    def test_create_mapreduce_job_operator(self, mock_create_mapreduce_job, *_):
        operator = DataprocCreateMapReduceJobOperator(
            task_id="run_mapreduce_job",
            connection_id=CONNECTION_ID,
            main_class="org.apache.hadoop.streaming.HadoopStreaming",
            file_uris=[
                "s3a://some-in-bucket/jobs/sources/mapreduce-001/mapper.py",
                "s3a://some-in-bucket/jobs/sources/mapreduce-001/reducer.py",
            ],
            args=[
                "-mapper",
                "mapper.py",
                "-reducer",
                "reducer.py",
                "-numReduceTasks",
                "1",
                "-input",
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "-output",
                "s3a://some-out-bucket/dataproc/job/results",
            ],
            properties={
                "yarn.app.mapreduce.am.resource.mb": "2048",
                "yarn.app.mapreduce.am.command-opts": "-Xmx2048m",
                "mapreduce.job.maps": "6",
            },
        )
        context = {"task_instance": MagicMock()}
        context["task_instance"].xcom_pull.return_value = "my_cluster_id"
        operator.execute(context)

        context["task_instance"].xcom_pull.assert_has_calls(
            [
                call(key="cluster_id"),
            ]
        )

        mock_create_mapreduce_job.assert_called_once_with(
            archive_uris=None,
            args=[
                "-mapper",
                "mapper.py",
                "-reducer",
                "reducer.py",
                "-numReduceTasks",
                "1",
                "-input",
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "-output",
                "s3a://some-out-bucket/dataproc/job/results",
            ],
            cluster_id="my_cluster_id",
            file_uris=[
                "s3a://some-in-bucket/jobs/sources/mapreduce-001/mapper.py",
                "s3a://some-in-bucket/jobs/sources/mapreduce-001/reducer.py",
            ],
            jar_file_uris=None,
            main_class="org.apache.hadoop.streaming.HadoopStreaming",
            main_jar_file_uri=None,
            name="Mapreduce job",
            properties={
                "yarn.app.mapreduce.am.resource.mb": "2048",
                "yarn.app.mapreduce.am.command-opts": "-Xmx2048m",
                "mapreduce.job.maps": "6",
            },
        )

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.create_spark_job")
    def test_create_spark_job_operator(self, mock_create_spark_job, *_):
        operator = DataprocCreateSparkJobOperator(
            task_id="create_spark_job",
            connection_id=CONNECTION_ID,
            main_jar_file_uri="s3a://data-proc-public/jobs/sources/java/dataproc-examples-1.0.jar",
            main_class="ru.yandex.cloud.dataproc.examples.PopulationSparkJob",
            file_uris=[
                "s3a://some-in-bucket/jobs/sources/data/config.json",
            ],
            archive_uris=[
                "s3a://some-in-bucket/jobs/sources/data/country-codes.csv.zip",
            ],
            jar_file_uris=[
                "s3a://some-in-bucket/jobs/sources/java/icu4j-61.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/commons-lang-2.6.jar",
                "s3a://some-in-bucket/jobs/sources/java/opencsv-4.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/json-20190722.jar",
            ],
            args=[
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "s3a://some-out-bucket/dataproc/job/results/${{JOB_ID}}",
            ],
            properties={
                "spark.submit.deployMode": "cluster",
            },
        )
        context = {"task_instance": MagicMock()}
        context["task_instance"].xcom_pull.return_value = "my_cluster_id"
        operator.execute(context)

        context["task_instance"].xcom_pull.assert_has_calls(
            [
                call(key="cluster_id"),
            ]
        )

        mock_create_spark_job.assert_called_once_with(
            archive_uris=["s3a://some-in-bucket/jobs/sources/data/country-codes.csv.zip"],
            args=[
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "s3a://some-out-bucket/dataproc/job/results/${{JOB_ID}}",
            ],
            cluster_id="my_cluster_id",
            file_uris=["s3a://some-in-bucket/jobs/sources/data/config.json"],
            jar_file_uris=[
                "s3a://some-in-bucket/jobs/sources/java/icu4j-61.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/commons-lang-2.6.jar",
                "s3a://some-in-bucket/jobs/sources/java/opencsv-4.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/json-20190722.jar",
            ],
            main_class="ru.yandex.cloud.dataproc.examples.PopulationSparkJob",
            main_jar_file_uri="s3a://data-proc-public/jobs/sources/java/dataproc-examples-1.0.jar",
            name="Spark job",
            properties={"spark.submit.deployMode": "cluster"},
            packages=None,
            repositories=None,
            exclude_packages=None,
        )

    @patch("airflow.providers.yandex.utils.credentials.get_credentials")
    @patch(f"{BASEHOOK_PATCH_PATH}.get_connection")
    @patch("yandexcloud._wrappers.dataproc.Dataproc.create_pyspark_job")
    def test_create_pyspark_job_operator(self, mock_create_pyspark_job, *_):
        operator = DataprocCreatePysparkJobOperator(
            task_id="create_pyspark_job",
            connection_id=CONNECTION_ID,
            main_python_file_uri="s3a://some-in-bucket/jobs/sources/pyspark-001/main.py",
            python_file_uris=[
                "s3a://some-in-bucket/jobs/sources/pyspark-001/geonames.py",
            ],
            file_uris=[
                "s3a://some-in-bucket/jobs/sources/data/config.json",
            ],
            archive_uris=[
                "s3a://some-in-bucket/jobs/sources/data/country-codes.csv.zip",
            ],
            args=[
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "s3a://some-out-bucket/jobs/results/${{JOB_ID}}",
            ],
            jar_file_uris=[
                "s3a://some-in-bucket/jobs/sources/java/dataproc-examples-1.0.jar",
                "s3a://some-in-bucket/jobs/sources/java/icu4j-61.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/commons-lang-2.6.jar",
            ],
            properties={
                "spark.submit.deployMode": "cluster",
            },
        )
        context = {"task_instance": MagicMock()}
        context["task_instance"].xcom_pull.return_value = "my_cluster_id"
        operator.execute(context)

        context["task_instance"].xcom_pull.assert_has_calls(
            [
                call(key="cluster_id"),
            ]
        )

        mock_create_pyspark_job.assert_called_once_with(
            archive_uris=["s3a://some-in-bucket/jobs/sources/data/country-codes.csv.zip"],
            args=[
                "s3a://some-in-bucket/jobs/sources/data/cities500.txt.bz2",
                "s3a://some-out-bucket/jobs/results/${{JOB_ID}}",
            ],
            cluster_id="my_cluster_id",
            file_uris=["s3a://some-in-bucket/jobs/sources/data/config.json"],
            jar_file_uris=[
                "s3a://some-in-bucket/jobs/sources/java/dataproc-examples-1.0.jar",
                "s3a://some-in-bucket/jobs/sources/java/icu4j-61.1.jar",
                "s3a://some-in-bucket/jobs/sources/java/commons-lang-2.6.jar",
            ],
            main_python_file_uri="s3a://some-in-bucket/jobs/sources/pyspark-001/main.py",
            name="Pyspark job",
            properties={"spark.submit.deployMode": "cluster"},
            python_file_uris=["s3a://some-in-bucket/jobs/sources/pyspark-001/geonames.py"],
            packages=None,
            repositories=None,
            exclude_packages=None,
        )
