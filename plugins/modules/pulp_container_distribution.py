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
module: pulp_container_distribution
short_description: Manage container distributions of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on container distributions in a pulp api server instance."
options:
  name:
    description:
      - Name of the distribution to query or manipulate
    type: str
    required: false
  base_path:
    description:
      - Base path to distribute a publication
    type: str
  repository:
    description:
      - Href of the repository to be served
    type: str
  repository_version:
    description:
      - RepositoryVersion to be served
    type: str
  content_guard:
    description:
      - Name of the content guard for the served content
    type: str
  state:
    description:
      - State the distribution should be in
    type: str
    choices:
      - present
      - absent
extends_documentation_fragment:
  - pulp
author:
  - Matthias Dellweg (@mdellweg)
'''

EXAMPLES = r'''
- name: Read list of container distributions from pulp api server
  pulp_container_distribution:
    api_url: localhost:24817
    username: admin
    password: password
  register: distribution_status
- name: Report pulp container distributions
  debug:
    var: distribution_status

- name: Create a container distribution
  pulp_container_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_container_distribution
    base_path: new/container/dist
    publication: /pub/api/v3/publications/container/container/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/
    state: present
- name: Delete a container distribution
  pulp_container_distribution:
    api_url: localhost:24817
    username: admin
    password: password
    name: new_container_distribution
    state: absent
'''

RETURN = r'''
  distributions:
    description: List of container distributions
    type: list
    return: when no name is given
  distribution:
    description: Container distribution details
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
            base_path=dict(),
            publication=dict(),
            content_guard=dict(),
        ),
        required_if=[
            ('state', 'present', ['name', 'base_path']),
            ('state', 'absent', ['name']),
        ],
        entity_name='distribution',
        entity_plural='distributions',
        entity_plugin='container'
    )

    if module.params['content_guard']:
        module.fail_json(msg="Content guard features are not yet supportet in this module.")

    natural_key = {
        'name': module.params['name'],
    }
    desired_attributes = {
        key: module.params[key] for key in ['base_path', 'content_guard', 'repository', 'repository_version'] if module.params[key] is not None
    }

    module.process_entity(natural_key, desired_attributes)


if __name__ == '__main__':
    main()
