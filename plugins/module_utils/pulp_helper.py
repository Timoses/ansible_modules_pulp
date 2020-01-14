# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from importlib import import_module

from ansible.module_utils.basic import AnsibleModule

try:
    from pulpcore.client import pulpcore
    HAS_PULPCORE_CLIENT = True
except ImportError:
    pulpcore = None
    HAS_PULPCORE_CLIENT = False
    PULPCORE_CLIENT_IMPORT_ERROR = traceback.format_exc()

try:
    from pulpcore.client import pulp_file
    HAS_PULP_FILE_CLIENT = True
except ImportError:
    pulp_file = None
    HAS_PULP_FILE_CLIENT = False
    PULP_FILE_CLIENT_IMPORT_ERROR = traceback.format_exc()




PAGE_LIMIT = 20


class PulpAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec={}, **kwargs):
        spec = dict(
            pulp_url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            validate_certs=dict(type='bool', default=True),
        )
        spec.update(argument_spec)
        kwargs['supports_check_mode'] = kwargs.get('supports_check_mode', True)
        super(PulpAnsibleModule, self).__init__(argument_spec=spec, **kwargs)

        self._changed = False

    def exit_json(self, changed=False, **kwargs):
        changed |= self._changed
        super(PulpAnsibleModule, self).exit_json(changed=changed, **kwargs)


class PulpEntityAnsibleModule(PulpAnsibleModule):
    def __init__(self, argument_spec={}, **kwargs):
#        self._entity_name = kwargs.pop('entity_name')
#        self._entity_plural = kwargs.pop('entity_plural')
#        self._entity_plugin = kwargs.pop('entity_plugin')
#        self._entity_ctlr = None
        spec = dict(
            state=dict(
                choices=['present', 'absent'],
            ),
        )
        spec.update(argument_spec)
        super(PulpEntityAnsibleModule, self).__init__(
            argument_spec=spec,
            **kwargs
        )

#    @property
#    def entity_ctlr(self):
#        if not self._entity_ctlr:
#            self._entity_ctlr = PulpEntityController(
#                self,
#                self._entity_name,
#                self._entity_plural,
#                self._entity_plugin
#            )
#        return self._entity_ctlr

#    def process_entity(self, natural_key, desired_attributes):
#        if None not in natural_key.values():
#            entity = self.entity_ctlr.find(
#                natural_key=natural_key,
#            )
#            entity = self.ensure_entity_state(
#                entity=entity,
#                natural_key=natural_key,
#                desired_attributes=desired_attributes,
#            )
#            if entity:
#                entity = entity.to_dict()
#            self.exit_json(**{self._entity_name: entity})
#        else:
#            entities = self.entity_ctlr.list()
#            self.exit_json(**{self._entity_plural: [entity.to_dict() for entity in entities]})

#    def ensure_entity_state(self, entity, natural_key, desired_attributes):
#        if self.params['state'] == 'present':
#            if entity:
#                entity = self.entity_ctlr.update(entity, desired_attributes)
#            else:
#                entity = self.entity_ctlr.create(natural_key, desired_attributes)
#        if self.params['state'] == 'absent' and entity is not None:
#            entity = self.entity_ctlr.delete(entity)
#        return entity

    def process_entity(self, pulp_entity):
        if None not in pulp_entity.id.values():
            entity = pulp_entity.find()
            if self.params['state'] == 'present':
                if entity is None:
                    entity = pulp_entity.create()
                else:
                    entity = pulp_entity.update()
            elif self.params['state'] == 'absent' and entity is not None:
                entity = pulp_entity.delete()

            if entity:
                entity = entity.to_dict()
            self.exit_json(**{pulp_entity._name_singular: entity})
        else:
            entities = pulp_entity.list()
            self.exit_json(**{pulp_entity._name_plural: [entity.to_dict() for entity in entities]})


class PulpEntity(object):

    def __init__(self, module):

        self.module = module
        self._api = None
        self._api_client = None

        self._api_config = pulpcore.Configuration()
        self._api_config.host = self.module.params['pulp_url']
        self._api_config.username = self.module.params['username']
        self._api_config.password = self.module.params['password']
        self._api_config.verify_ssl = self.module.params['validate_certs']
        self._api_config.safe_chars_for_path_param = '/'

        self.entity = None


        self._client = None
        self._tasks_api = None

    @property
    def api(self):
        if not self._api:
            self._api = self._api_class(self.api_client)
        return self._api


    @property
    def api_client(self):
        if not self._api_client:
            self._api_client = self._api_client_class(self._api_config)
        return self._api_client

    def find(self):
        id = self.id
        search_result = self.api.list(**id)
        if search_result.count == 1:
            self.entity = search_result.results[0]
            return self.entity
        else:
            return None

    def list(self):
        entities = []
        offset = 0
        search_result = self.api.list(limit=PAGE_LIMIT, offset=offset)
        entities.extend(search_result.results)
        while search_result.next:
            offset += PAGE_LIMIT
            search_result = self.api.list(limit=PAGE_LIMIT, offset=offset)
            entities.extend(search_result.results)
        return entities

    def create(self):
        if not hasattr(self.api, 'create'):
            self.module.fail_json(msg="This entity is not creatable.")
        kwargs = dict()
        kwargs.update(self.id)
        kwargs.update(self.desired_state)
        entity = self._api_entity_class(**kwargs)
        if not self.module.check_mode:
            response = self.api.create(entity)
            if getattr(response, 'task', None):
                task = self.api_client.wait_for_task(response.task)
                entity = self.api.read(task.created_resources[0])
            else:
                entity = response
        self.module._changed = True
        self.entity = entity
        return self.entity

    def update(self):
        changed = False

        desired_attributes = self.desired_state
        # drop 'file' because artifacts as well as content units are immutable anyway
        desired_attributes.pop('file', None)
        for key, value in desired_attributes.items():
            if getattr(self.entity, key, None) != value:
                setattr(self.entity, key, value)
                changed = True
        if changed:
            if not hasattr(self.api, 'update'):
                self.module.fail_json(msg="This entity is immutable.")
            if not self.module.check_mode:
                response = self.api.update(self.entity.pulp_href, self.entity)
                if getattr(response, 'task', None):
                    self.wait_for_task(response.task)
                    entity = self.api.read(self.entity.pulp_href)
                else:
                    entity = response
                self.entity = entity
            self.module._changed = True
        return self.entity

    def delete(self):
        if not hasattr(self.api, 'delete'):
            self.module.fail_json(msg="This entity is not deletable.")
        if not self.module.check_mode:
            response = self.api.delete(self.entity.pulp_href)
            if getattr(response, 'task', None):
                self.wait_for_task(response.task)
        self.module._changed = True
        return None

    @property
    def client(self):
        if not self._client:
            self._client = pulpcore.ApiClient(self._api_config)
        return self._client
    @property
    def tasks_api(self):
        if not self._tasks_api:
            self._tasks_api = pulpcore.TasksApi(self.client)
        return self._tasks_api
    def wait_for_task(self, task_href):
        from time import sleep
        task = self.tasks_api.read(task_href)
        while task.state not in ['completed', 'failed', 'canceled']:
            sleep(2)
            task = self.tasks_api.read(task.pulp_href)
        if task.state != 'completed':
            self.module.fail_json(msg='Task failed to complete. ({}; {})'.format(task.state, task.error['description']))
        return task


class PulpFileEntity(PulpEntity):

    _api_client_class = pulp_file.ApiClient

    def __init__(self, module):
        if not HAS_PULP_FILE_CLIENT:
            self.fail_json(
                msg=missing_required_lib("pulp_file-client"),
                exception=PULP_FILE_CLIENT_IMPORT_ERROR,
            )
        super(PulpEntity, self).__init__(
            module=module
        )


class PulpFileRemote(PulpFileEntity):

    _api_class = pulp_file.RemotesFileApi
    _api_entity_class = pulp_file.FileFileRemote

    _name_singular = 'remote'
    _name_plural = 'remotes'

    def __init__(self, module):
        super(PulpFileEntity, self).__init__(
            module=module
        )

        self.id = {
            'name': module.params['name'],
        }

        self.desired_state = {
            key: self.module.params[key] for key in ['url', 'download_concurrency', 'policy'] if self.module.params[key] is not None
        }


class PulpFileRepository(PulpFileEntity):

    _api_class = pulp_file.RepositoriesFileApi
    _api_entity_class = pulp_file.FileFileRepository

    _name_singular = 'repository'
    _name_plural = 'repositories'

    def __init__(self, module):
        super(PulpFileEntity, self).__init__(
            module=module
        )

        self.id = {
            'name': module.params['name'],
        }

        self.desired_state = {}
        if self.module.params['description'] is not None:
            # In case of an empty string we try to nullify the description
            # Which does not yet work
            self.desired_state['description'] = module.params['description'] or None


#class PulpEntityController:
#
#    def __init__(self, module, entity_name, entity_plural, entity_plugin):
#        self.module = module
#        # TODO: Why does dynamic 'import_module' fail without below manual import?
#        import ansible.module_utils.pulp_file  # noqa: F401
#        self._api_client = getattr(import_module("ansible.module_utils.pulp_%s" % entity_plugin.lower()),
#                                   "Pulp%sApiClient" % entity_plugin.lower().capitalize()
#                                   )(self.module)
#        self._api = getattr(self._api_client, entity_plural + '_api')
#        self._api_class = getattr(self._api_client, entity_name + '_class')
#
#    @property
#    def api(self):
#        return self._api
#
#    @property
#    def api_client(self):
#        return self._api_client
#
#    def find(self, natural_key):
#        search_result = self._api.list(**natural_key)
#        if search_result.count == 1:
#            return search_result.results[0]
#        else:
#            return None
#
#    def list(self):
#        entities = []
#        offset = 0
#        search_result = self._api.list(limit=PAGE_LIMIT, offset=offset)
#        entities.extend(search_result.results)
#        while search_result.next:
#            offset += PAGE_LIMIT
#            search_result = self._api.list(limit=PAGE_LIMIT, offset=offset)
#            entities.extend(search_result.results)
#        return entities
#
#    def create(self, natural_key, desired_attributes):
#        if not hasattr(self._api, 'create'):
#            self.module.fail_json(msg="This entity is not creatable.")
#        kwargs = dict()
#        kwargs.update(natural_key)
#        kwargs.update(desired_attributes)
#        entity = self._api_class(**kwargs)
#        if not self.module.check_mode:
#            response = self._api.create(entity)
#            if getattr(response, 'task', None):
#                task = self._api_client.wait_for_task(response.task)
#                entity = self._api.read(task.created_resources[0])
#            else:
#                entity = response
#        self.module._changed = True
#        return entity
#
#    def update(self, entity, desired_attributes):
#        changed = False
#        # drop 'file' because artifacts as well as content units are immutable anyway
#        desired_attributes.pop('file', None)
#        for key, value in desired_attributes.items():
#            if getattr(entity, key, None) != value:
#                setattr(entity, key, value)
#                changed = True
#        if changed:
#            if not hasattr(self._api, 'update'):
#                self.module.fail_json(msg="This entity is immutable.")
#            if not self.module.check_mode:
#                response = self._api.update(entity.pulp_href, entity)
#                if getattr(response, 'task', None):
#                    self._api_client.wait_for_task(response.task)
#                    entity = self._api.read(entity.pulp_href)
#                else:
#                    entity = response
#        if changed:
#            self.module._changed = True
#        return entity
#
#    def delete(self, entity):
#        if not hasattr(self._api, 'delete'):
#            self.module.fail_json(msg="This entity is not deletable.")
#        if not self.module.check_mode:
#            response = self._api.delete(entity.pulp_href)
#            if getattr(response, 'task', None):
#                self._api_client.wait_for_task(response.task)
#        self.module._changed = True
#        return None



