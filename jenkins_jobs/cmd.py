#!/usr/bin/env python
# Copyright (C) 2012 OpenStack Foundation
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

import argparse
import ConfigParser
import logging
import os
import sys


def confirm(question):
    answer = raw_input('%s (Y/N): ' % question).upper().strip()
    if not answer == 'Y':
        sys.exit('Aborted')


def main():
    import jenkins_jobs.builder
    import jenkins_jobs.errors
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='update, test or delete job',
                                      dest='command')
    parser_update = subparser.add_parser('update')
    parser_update.add_argument('path', help='Path to YAML file or directory')
    parser_update.add_argument('names', help='name(s) of job(s)', nargs='*')
    parser_test = subparser.add_parser('test')
    parser_test.add_argument('path', help='Path to YAML file or directory')
    parser_test.add_argument('-o', dest='output_dir',
                             help='Path to output XML')
    parser_test.add_argument('name', help='name(s) of job(s)', nargs='*')
    parser_delete = subparser.add_parser('delete')
    parser_delete.add_argument('name', help='name of job', nargs='+')
    subparser.add_parser('delete-all',
                         help='Delete *ALL* jobs from Jenkins server, '
                         'including those not managed by Jenkins Job '
                         'Builder.')
    parser.add_argument('--conf', dest='conf', help='Configuration file')
    parser.add_argument('-l', '--log_level', dest='log_level', default='info',
                        help="Log level (default: %(default)s)")
    options = parser.parse_args()

    options.log_level = getattr(logging, options.log_level.upper(),
                                logging.INFO)
    logging.basicConfig(level=options.log_level)
    logger = logging.getLogger()

    conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    if options.conf:
        conf = options.conf
    else:
        # Fallback to script directory
        localconf = os.path.join(os.path.dirname(__file__),
                                 'jenkins_jobs.ini')
        if os.path.isfile(localconf):
            conf = localconf

    if os.path.isfile(conf):
        logger.debug("Reading config from {0}".format(conf))
        conffp = open(conf, 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(conffp)
    elif options.command == 'test':
        logger.debug("Not reading config for test output generation")
        config = {}
    else:
        raise jenkins_jobs.errors.JenkinsJobsException(
            "A valid configuration file is required when not run as a test")

    logger.debug("Config: {0}".format(config))
    builder = jenkins_jobs.builder.Builder(config.get('jenkins', 'url'),
                                           config.get('jenkins', 'user'),
                                           config.get('jenkins', 'password'),
                                           config)

    if options.command == 'delete':
        for job in options.name:
            logger.info("Deleting job {0}".format(job))
            builder.delete_job(job)
    elif options.command == 'delete-all':
        confirm('Sure you want to delete *ALL* jobs from Jenkins server?\n'
                '(including those not managed by Jenkins Job Builder)')
        logger.info("Deleting all jobs")
        builder.delete_all_jobs()
    elif options.command == 'update':
        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.names))
        builder.update_job(options.path, options.names)
    elif options.command == 'test':
        builder.update_job(options.path, options.name,
                           output_dir=options.output_dir)

if __name__ == '__main__':
    sys.path.insert(0, '.')
    main()
