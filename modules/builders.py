#! /usr/bin/env python
# Copyright (C) 2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Jenkins Job module for builders
# To use add the folowing into your YAML:
# builders:
#   - 'gerrit_git_prep'
#   - 'python26'

import xml.etree.ElementTree as XML


def register(registry):
    mod = Builders(registry)
    registry.registerModule(mod)


class Builders(object):
    sequence = 60
    
    def __init__(self, registry):
        self.registry = registry
        for f in dir(self):
            if not f.startswith('_builder_'):
                continue
            self.registry.registerHandler('builder', f[len('_builder_'):],
                                          getattr(self, f))

    def handle_data(self, data):
        self.data = data

    def gen_xml(self, xml_parent, data):
        for alias in ['prebuilders', 'builders', 'postbuilders']:
            if alias in data:
                builders = XML.SubElement(xml_parent, alias)
                for builder in data[alias]:
                    if isinstance(builder, dict):
                        for key, value in builder.items():
                            func = self.registry.getHandler('builder', key)
                            func(builders, value)
                    else:
                        func = self.registry.getHandler('builder', builder)
                        func(builders)

    def _add_script(self, xml_parent, script):
        shell = XML.SubElement(xml_parent, 'hudson.tasks.Shell')
        XML.SubElement(shell, 'command').text = script

    def _builder_coverage(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-cover.sh')

    def _builder_docs(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-docs.sh')

    def _builder_gerrit_git_prep(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/gerrit-git-prep.sh {site}'.format(site=self.data['main']['review_site']))

    def _builder_maven_test(self, xml_parent):
        self._add_script(xml_parent, 'mvn test')

    def _builder_maven_package(self, xml_parent):
        self._add_script(xml_parent, 'mvn package')

    def _builder_gerrit_package(self, xml_parent):
        self._add_script(xml_parent,
            '/usr/local/jenkins/slave_scripts/package-gerrit.sh')

    def _builder_gerrit_preclean(self, xml_parent):
        self._add_script(xml_parent, "#!/bin/bash -xe\n\
rm -fr ~/.m2\n\
rm -fr ~/.java\n\
./tools/version.sh --release")

    def _builder_gerrit_postrun(self, xml_parent):
        self._add_script(xml_parent, "./tools/version.sh --reset")

    def _builder_pep8(self, xml_parent):
        self._add_script(xml_parent, 'set -o pipefail ; tox -v -epep8 | tee pep8.txt ; set +o pipefail')

    def _builder_pyflakes(self, xml_parent):
        self._add_script(xml_parent, 'tox -v -epyflakes')

    def _builder_puppet_syntax(self, xml_parent):
        self._add_script(xml_parent, """
find . -iname *.pp | xargs puppet parser validate --modulepath=`pwd`/modules
for f in `find . -iname *.erb` ; do
  erb -x -T '-' $f | ruby -c
done
""")

    def _builder_shell(self, xml_parent, data):
        self._add_script(xml_parent, data)

    def _builder_trigger_builds(self, xml_parent, data):
        tbuilder = XML.SubElement(xml_parent, 'hudson.plugins.parameterizedtrigger.TriggerBuilder')
        configs = XML.SubElement(tbuilder, 'configs')
        for project_def in data:
            tconfig = XML.SubElement(configs, 'hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig')
            tconfigs = XML.SubElement(tconfig, 'configs')
            if project_def.has_key('predefined_parameters'):
                params = XML.SubElement(tconfigs,
                                        'hudson.plugins.parameterizedtrigger.PredefinedBuildParameters')
                properties = XML.SubElement(params, 'properties')
                properties.text = project_def['predefined_parameters']
            else:
                tconfigs.set('class', 'java.util.Collections$EmptyList')
            projects = XML.SubElement(tconfig, 'projects')
            projects.text = project_def['project']
            condition = XML.SubElement(tconfig, 'condition')
            condition.text = 'ALWAYS'
            trigger_with_no_params = XML.SubElement(tconfig, 'triggerWithNoParameters')
            trigger_with_no_params.text = 'false'
            build_all_nodes_with_label = XML.SubElement(tconfig, 'buildAllNodesWithLabel')
            build_all_nodes_with_label.text = 'false'
            
    def _builder_python26(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-tox.sh 26')

    def _builder_python27(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-tox.sh 27')

    def _builder_python26_essex(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-tox.sh 26-essex')

    def _builder_python27_essex(self, xml_parent):
        self._add_script(xml_parent, '/usr/local/jenkins/slave_scripts/run-tox.sh 27-essex')

    def _builder_tarball(self, xml_parent):
        self._add_script(xml_parent,
          '/usr/local/jenkins/slave_scripts/create-tarball.sh %s' % self.data['main']['project'])

    def _builder_ppa(self, xml_parent):
        self._add_script(xml_parent, 'rm -rf build dist.zip\n\
mkdir build')
        copy = XML.SubElement(xml_parent, 'hudson.plugins.copyartifact.CopyArtifact')
        XML.SubElement(copy, 'projectName').text = '%s-tarball' % self.data['main']['project']
        XML.SubElement(copy, 'filter').text = 'dist/*.tar.gz'
        XML.SubElement(copy, 'target').text = 'build'
        selector = XML.SubElement(copy, 'selector', {'class':'hudson.plugins.copyartifact.StatusBuildSelector'})
        XML.SubElement(selector, 'parameterName').text = 'BUILD_SELECTOR'
        self._add_script(xml_parent, '#!/bin/bash\n\
\n\
#export DO_UPLOAD=&quot;no&quot;\n\
export PROJECT=&quot;<%= project %>&quot;\n\
export GERRIT_REFNAME=$BRANCH\n\
/usr/local/jenkins/slave_scripts/create-ppa-package.sh')
