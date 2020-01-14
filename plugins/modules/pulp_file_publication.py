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
module: pulp_file_publication
short_description: Manage file publications of a pulp api server instance
version_added: "2.8"
description:
  - "This performes CRUD operations on file publications in a pulp api server instance."
options:
  repository:
    description:
      - Name of the repository to be published
    type: str
    required: false
  version:
    description:
      - Version Number to be published
    type: int
    required: false
  manifest:
    description:
      - Name of the pulp manifest file in the publication
    type: str
    required: false
  state:
    description:
      - State the publication should be in
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
- name: Read list of file publications from pulp api server
  pulp_file_publication:
    api_url: localhost:24817
    username: admin
    password: password
  register: publication_status
- name: Report pulp file publications
  debug:
    var: remote_status
- name: Create a file publication
  pulp_file_publication:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    state: present
- name: Delete a file remote
  pulp_file_remote:
    api_url: localhost:24817
    username: admin
    password: password
    repository: my_file_repo
    state: absent
'''

RETURN = r'''
  publications:
    description: List of file publications
    type: list
    return: when no name is given
  publication:
    description: File publication details
    type: dict
    return: when name is given
'''


from ansible.module_utils.pulp_helper import PulpEntityAnsibleModule, PulpEntityController


def main():
    module = PulpEntityAnsibleModule(
        argument_spec=dict(
            repository=dict(),
            version=dict(),
            manifest=dict(),
        ),
        required_if=(
            ['state', 'present', ['repository']],
            ['state', 'absent', ['repository']],
        ),
        entity_name='publication',
        entity_plural='publications',
        entity_plugin='file'
    )

    repository_name = module.params['repository']
    version = module.params['version']
    desired_attributes = {
        key: module.params[key] for key in ['manifest'] if module.params[key] is not None
    }

    repository_ctlr = PulpEntityController(module, 'repository', 'repositories', 'file')
    publication_ctlr = PulpEntityController(module, 'publication', 'publications', 'file')
    if repository_name:
        repository = repository_ctlr.find({'name': repository_name})
        if repository is None:
            module.fail_json(msg="Failed to find repository ({repository_name}).".format(repository_name=repository_name))
        # TODO handle version properly
        if version:
            repository_version_href = repository.versions_href + "{version}/".format(version=version)
        else:
            repository_version_href = repository.latest_version_href
        # TODO proper search
        # entity = module.find_entity(module.file_publications_api, {'repository_version': repository_version_href})
        # ---8<----8<---8<---
        entity = None
        search_result = publication_ctlr.api.list()
        for item in search_result.results:
            if item.repository_version == repository_version_href:
                entity = item
                break
        # ---8<----8<---8<---
        entity = module.ensure_entity_state(
            entity=entity,
            natural_key={'repository_version': repository_version_href},
            desired_attributes=desired_attributes,
        )
        if entity is not None:
            entity = entity.to_dict()
        module.exit_json(publication=entity)
    else:
        entities = publication_ctlr.list()
        module.exit_json(publications=[entity.to_dict() for entity in entities])


if __name__ == '__main__':
    main()
