"""Exception classes for jenkins_jobs errors"""


class JenkinsJobsException(Exception):
    pass


class YAMLFormatError(JenkinsJobsException):
    pass
