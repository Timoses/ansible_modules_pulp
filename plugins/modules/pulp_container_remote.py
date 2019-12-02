# -*- coding: utf-8 -*-

# copyright (c) 2019, Matthias Dellweg
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
---
module: pulp_container_remote
short_description: Manage container remotes of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on container remotes in a pulp api server instance."
options:
  name:
    description:
      - Name of the remote to query or manipulate
    type: str
  url:
    description:
      - URL of an external content source
    type: str
  download_concurrency:
    description:
      - How many downloads should be attempted in parallel
    type: int
  policy:
    description:
      - Whether downloads should be performed immediately, or lazy.
    type: str
    choices:
      - immediate
      - on-demand
      - streamed
  state:
    description:
      - State the remote should be in
    type: str
    choices:
      - present
      - absent
  upstream_name:
    description:
      - Name of the upstream repository
    type: str
extends_documentation_fragment:
  - pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of container remotes from pulp api server
  pulp_container_remote:
    api_url: localhost:24817
    username: admin
    password: password
  register: remote_status
- name: Report pulp container remotes
  debug:
    var: remote_status
- name: Create a container remote
  pulp_container_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_container_remote
    url: https://registry-1.docker.io
    upstream_name: pulp/test-fixture-1
    state: present
- name: Delete a container remote
  pulp_container_remote:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_container_remote
    state: absent
'''

RETURN = r'''
  remotes:
    description: List of container remotes
    type: list
    return: when no name is given
  remote:
    description: Container remote details
    type: dict
    return: when name is given
'''


from ansible.module_utils.pulp_helper import (
    PulpEntityAnsibleModule,
)


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            name=dict(),
            url=dict(),
            download_concurrency=dict(type=int),
            policy=dict(
                choices=['immediate', 'on-demand', 'streamed'],
            ),
            upstream_name=dict()
        ),
        required_if=[
            ('state', 'present', ['name']),
            ('state', 'absent', ['name']),
        ],
        entity_name='remote',
        entity_plural='remotes',
        entity_plugin='container'
    )

    natural_key = {
        'name': module.params['name'],
    }
    desired_attributes = {
        key: module.params[key] for key in ['url', 'download_concurrency', 'policy', 'upstream_name'] if module.params[key] is not None
    }

    module.process_entity(natural_key, desired_attributes)


if __name__ == '__main__':
    main()
