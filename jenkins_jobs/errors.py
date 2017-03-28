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
        module_name = '<unresolved>'
        while frame and co_name != 'run':
            # XML generation called via dispatch
            if co_name == 'dispatch':
                data = frame.f_locals
                module_name = "%s.%s" % (data['component_type'], data['name'])
                break
            # XML generation done directly by class using gen_xml or root_xml
            if co_name == 'gen_xml' or co_name == 'root_xml':
                data = frame.f_locals['data']
                module_name = next(iter(data.keys()))
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

    def __init__(self, missing_attribute, module_name=None):
        module = module_name or self.get_module_name()
        if is_sequence(missing_attribute):
            message = "One of {0} must be present in '{1}'".format(
                ', '.join("'{0}'".format(value)
                          for value in missing_attribute), module)
        else:
            message = "Missing {0} from an instance of '{1}'".format(
                missing_attribute, module)

        super(MissingAttributeError, self).__init__(message)


class AttributeConflictError(ModuleError):

    def __init__(
        self, attribute_name, attributes_in_conflict, module_name=None
    ):
        module = module_name or self.get_module_name()
        message = (
            "Attribute '{0}' can not be used together with {1} in {2}".format(
                attribute_name,
                ', '.join(
                    "'{0}'".format(value) for value in attributes_in_conflict
                ), module
            )
        )

        super(AttributeConflictError, self).__init__(message)


class YAMLFormatError(JenkinsJobsException):
    pass


class JJBConfigException(JenkinsJobsException):
    pass
