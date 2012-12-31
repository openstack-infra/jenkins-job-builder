#!/usr/bin/env python

import jenkins_jobs.builder
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
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='update, test or delete job',
                                      dest='command')
    parser_update = subparser.add_parser('update')
    parser_update.add_argument('path', help='Path to YAML file or directory')
    parser_update.add_argument('name', help='name of job', nargs='?')
    parser_test = subparser.add_parser('test')
    parser_test.add_argument('path', help='Path to YAML file or directory')
    parser_test.add_argument('-o', dest='output_dir',
                             help='Path to output XML')
    parser_test.add_argument('name', help='name of job', nargs='?')
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

    if not options.command == 'test':
        logger.debug("Reading config from {0}".format(conf))
        conffp = open(conf, 'r')
        config = ConfigParser.ConfigParser()
        config.readfp(conffp)
    else:
        config = {}
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
            options.path, options.name))
        builder.update_job(options.path, options.name)
    elif options.command == 'test':
        builder.update_job(options.path, options.name,
                           output_dir=options.output_dir)

if __name__ == '__main__':
    main()
