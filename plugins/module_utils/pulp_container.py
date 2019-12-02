# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.pulp_core import PulpCoreApiClient
from ansible.module_utils.pulp_helper import PulpEntityController

try:
    from pulpcore.client import pulp_container
    HAS_PULP_CONTAINER_CLIENT = True
except ImportError:
    pulp_container = None
    HAS_PULP_CONTAINER_CLIENT = False
    PULP_CONTAINER_CLIENT_IMPORT_ERROR = traceback.format_exc()


class PulpContainerApiClient(PulpCoreApiClient):

    def __init__(self, module):
        PulpCoreApiClient.__init__(self, module)

        self._distributions_api = None
        self._remotes_api = None
        self._repositories_api = None

    @property
    def plugin_client(self):
        if not self._plugin_client:
            if not HAS_PULP_CONTAINER_CLIENT:
                self.fail_json(
                    msg=missing_required_lib("pulp-container-client"),
                    exception=PULP_CONTAINER_CLIENT_IMPORT_ERROR,
                )
            self._plugin_client = pulp_container.ApiClient(self._api_config)
        return self._plugin_client

    @property
    def distributions_api(self):
        if not self._distributions_api:
            self._distributions_api = pulp_file.DistributionsFileApi(self.plugin_client)
        return self._distributions_api

    @property
    def distribution_class(self):
        return pulp_file.FileFileDistribution

    @property
    def repositories_api(self):
        if not self._repositories_api:
            self._repositories_api = pulp_container.RepositoriesContainerApi(self.plugin_client)
        return self._repositories_api

    @property
    def repository_class(self):
        return pulp_container.ContainerContainerRepository

    @property
    def remotes_api(self):
        if not self._remotes_api:
            self._remotes_api = pulp_container.RemotesContainerApi(self.plugin_client)
        return self._remotes_api

    @property
    def remote_class(self):
        return pulp_container.ContainerContainerRemote
