# Copyright 2018 Openstack Foundation

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
View support for All view-type.

To create an all view specify ``all`` in the ``view-type`` attribute
to the :ref:`view_all` definition.

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view-all-minimal.yaml
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers


class All(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        root = XML.Element('hudson.model.AllView')

        mapping = [
            ('name', 'name', None),
            ('description', 'description', ''),
            ('filter-executors', 'filterExecutors', False),
            ('filter-queue', 'filterQueue', False),
        ]
        helpers.convert_mapping_to_xml(root, data, mapping, fail_required=True)

        XML.SubElement(root, 'properties',
                       {'class': 'hudson.model.View$PropertyList'})

        return root
