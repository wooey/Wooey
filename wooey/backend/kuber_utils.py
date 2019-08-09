import logging
import yaml

from django.conf import settings
from django.template import loader
from kubernetes import client, config

LOG = logging.getLogger(__name__)


class BaseKubernetesObject:
    @staticmethod
    def _load_manifest(manifest, context):
        return yaml.safe_load(loader.get_template(manifest).render(context))

    @staticmethod
    def load_config(kube_config_path=None):
        try:
            config.load_kube_config(kube_config_path)
        except (FileNotFoundError, TypeError):
            config.load_incluster_config()


class KubernetesPod(BaseKubernetesObject):
    def __init__(self, manifest, name=None, namespace=None, env_variables=None, context=None, body=''):
        self.body = body
        if not body:
            self.body = self._load_manifest(manifest, context if context else {})

        self.name = name if name else self.body['metadata']['name']
        self.body['metadata']['name'] = self.name

        if env_variables:
            env = []
            for key, value in env_variables.items():
                env.append({'name': key, 'value': value})
            self.body['spec']['template']['spec']['containers'][0]['env'] = env

        self.namespace = namespace if namespace else settings.KUBERNETES_NAMESPACE
        self.load_config()
        self.api_instance = client.CoreV1Api()

    def create(self, dry_run=None):
        res = self.api_instance.create_namespaced_pod(
            namespace=self.namespace, body=self.body, dry_run=dry_run
        )
        LOG.info("Creating POD with name '%s'.", self.body['metadata']['name'])
        LOG.debug("POD status:\n%s", res.status)

    def edit_container_command(self, label, arg, container_index=0):
        for i, command in enumerate(self.body['spec']['containers'][container_index]['command']):
            if label in command:
                self.body['spec']['containers'][container_index]['command'][i] = \
                    self.body['spec']['containers'][container_index]['command'][i].replace(label, arg)

    def edit_container(self, config_dict, container_index=0):
        self.body['spec']['containers'][container_index].update(config_dict)

    def extend_container_env(self, env_vars, container_index=0):
        self.body['spec']['containers'][container_index]['env'].extend(env_vars)

    def set_image(self, image_name):
        if image_name:
            self.edit_container({'image': '/'.join((settings.KUBERNETES_URL, image_name))})

    def delete(self, name=None):
        name = name if name else self.name
        self.api_instance.delete_namespaced_pod(name=name,
                                                namespace=self.namespace,
                                                body=client.V1DeleteOptions())
        LOG.info("Deleting POD with name '%s'.", name)

    def get_status(self, name=None):
        name = name if name else self.name
        return self.api_instance.read_namespaced_pod_status(name, self.namespace).status

    def get_logs(self, lines=200):
        return self.api_instance.read_namespaced_pod_log(self.name, self.namespace, tail_lines=lines)
