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

# Jenkins Job module for publishing via ftp
# publish:
#   site: 'docs.openstack.org'
#   remote_dir: 'dest/dir'
#   source_files: 'base/source/dir/**'
#   remove_prefix: 'base/source/dir'
#   excludes: '**/*.exludedfiletype'
#
# This will upload everything under $workspace/base/source/dir to
# docs.openstack.org $ftpdir/dest/dir exluding the excluded file type.

import xml.etree.ElementTree as XML

class publisher_ftp(object):
    def __init__(self, data):
        self.data = data

    def gen_xml(self, xml_parent):
        """
        Example XML:
        <publishers>
          <jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin>
            <consolePrefix>FTP: </consolePrefix>
            <delegate>
              <publishers>
                <jenkins.plugins.publish__over__ftp.BapFtpPublisher>
                  <configName>docs.openstack.org</configName>
                  <verbose>true</verbose>
                  <transfers>
                    <jenkins.plugins.publish__over__ftp.BapFtpTransfer>
                      <remoteDirectory></remoteDirectory>
                      <sourceFiles>openstack-identity-api/target/docbkx/webhelp/api/openstack-identity-service/2.0/**</sourceFiles>
                      <excludes>**/*.xml,**/null*</excludes>
                      <removePrefix>openstack-identity-api/target/docbkx/webhelp</removePrefix>
                      <remoteDirectorySDF>false</remoteDirectorySDF>
                      <flatten>false</flatten>
                      <cleanRemote>false</cleanRemote>
                      <asciiMode>false</asciiMode>
                    </jenkins.plugins.publish__over__ftp.BapFtpTransfer>
                  </transfers>
                  <useWorkspaceInPromotion>false</useWorkspaceInPromotion>
                  <usePromotionTimestamp>false</usePromotionTimestamp>
                </jenkins.plugins.publish__over__ftp.BapFtpPublisher>
              </publishers>
              <continueOnError>false</continueOnError>
              <failOnError>false</failOnError>
              <alwaysPublishFromMaster>false</alwaysPublishFromMaster>
              <hostConfigurationAccess class="jenkins.plugins.publish_over_ftp.BapFtpPublisherPlugin" reference="../.."/>
            </delegate>
          </jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin>
        </publishers>
        """
        publish = self.data['publisher']
        outer_publishers = XML.SubElement(xml_parent, 'publishers')
        outer_ftp = XML.SubElement(outer_publishers, 'jenkins.plugins.publish__over__ftp.BapFtpPublisherPlugin')
        XML.SubElement(outer_ftp, 'consolePrefix').text = 'FTP: '
        delegate = XML.SubElement(outer_ftp, 'delegate')
        publishers = XML.SubElement(delegate, 'publishers')
        ftp = XML.SubElement(publishers, 'jenkins.plugins.publish__over__ftp.BapFtpPublisher')
        XML.SubElement(ftp, 'configName').text = publish['site']
        XML.SubElement(ftp, 'verbose').text = 'true'

        transfers = XML.SubElement(ftp, 'transfers')
        ftp_transfers = XML.SubElement(transfers, 'jenkins.plugins.publish__over__ftp.BapFtpTransfer')
        # TODO: the next four fields are where the magic happens. Fill them in.
        XML.SubElement(ftp_transfers, 'remoteDirectory').text = publish['remote_dir']
        XML.SubElement(ftp_transfers, 'sourceFiles').text = publish['source_files']
        XML.SubElement(ftp_transfers, 'excludes').text = publish['excludes']
        XML.SubElement(ftp_transfers, 'removePrefix').text = publish['remove_prefix']
        XML.SubElement(ftp_transfers, 'remoteDirectorySDF').text = 'false'
        XML.SubElement(ftp_transfers, 'flatten').text = 'false'
        XML.SubElement(ftp_transfers, 'cleanRemote').text = 'false'
        XML.SubElement(ftp_transfers, 'asciiMode').text = 'false'

        XML.SubElement(ftp, 'useWorkspaceInPromotion').text = 'false'
        XML.SubElement(ftp, 'usePromotionTimestamp').text = 'false'
        XML.SubElement(delegate, 'continueOnError').text = 'false'
        XML.SubElement(delegate, 'failOnError').text = 'false'
        XML.SubElement(delegate, 'alwaysPublishFromMaster').text = 'false'
        XML.SubElement(delegate, 'hostConfigurationAccess',
                {'class': 'jenkins.plugins.publish_over_ftp.BapFtpPublisherPlugin',
                 'reference': '../..'})
