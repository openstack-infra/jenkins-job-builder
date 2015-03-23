"""Exception classes for jenkins_jobs errors"""

import inspect


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            (hasattr(arg, "__getitem__") or
             hasattr(arg, "__iter__")))


class JenkinsJobsException(Exception):
    pass


class ModuleError(JenkinsJobsException):

    def get_module_name(self):
        frame = inspect.currentframe()
        co_name = frame.f_code.co_name
        while frame and co_name != 'run':
            if co_name == 'dispatch':
                data = frame.f_locals
                module_name = "%s.%s" % (data['component_type'], data['name'])
                break
            frame = frame.f_back
            co_name = frame.f_code.co_name

        return module_name


class InvalidAttributeError(ModuleError):

    def __init__(self, attribute_name, value, valid_values=None):
        message = "'{0}' is an invalid value for attribute {1}.{2}".format(
            value, self.get_module_name(), attribute_name)

        if is_sequence(valid_values):
            message += "\nValid values include: {0}".format(
                ', '.join("'{0}'".format(value)
                          for value in valid_values))

        super(InvalidAttributeError, self).__init__(message)


class MissingAttributeError(ModuleError):

    def __init__(self, missing_attribute):
        if is_sequence(missing_attribute):
            message = "One of {0} must be present in {1}".format(
                ', '.join("'{0}'".format(value)
                          for value in missing_attribute),
                self.get_module_name())
        else:
            message = "Missing {0} from an instance of {1}".format(
                missing_attribute, self.get_module_name())

        super(MissingAttributeError, self).__init__(message)


class YAMLFormatError(JenkinsJobsException):
    pass
