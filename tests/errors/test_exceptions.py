from testtools import ExpectedException

from jenkins_jobs import errors
from tests import base


def dispatch(exc, *args):
    component_type = "type"  # noqa
    name = "name"

    for value in [component_type, name]:
        # prevent pep8 F841 "Unused Variable"
        pass

    raise exc(*args)


def gen_xml(exc, *args):
    data = {'module': 'data'}  # noqa

    raise exc(*args)


class TestInvalidAttributeError(base.BaseTestCase):

    def test_no_valid_values(self):
        # When given no valid values, InvalidAttributeError simply displays a
        # message indicating the invalid value, the component type, the
        # component name, and the attribute name.
        message = "'{0}' is an invalid value for attribute {1}.{2}".format(
            "fnord", "type.name", "fubar")
        with ExpectedException(errors.InvalidAttributeError, message):
            dispatch(errors.InvalidAttributeError, "fubar", "fnord")

    def test_with_valid_values(self):
        # When given valid values, InvalidAttributeError displays a message
        # indicating the invalid value, the component type, the component name,
        # and the attribute name; additionally, it lists the valid values for
        # the current component type & name.
        valid_values = ['herp', 'derp']
        message = "'{0}' is an invalid value for attribute {1}.{2}".format(
            "fnord", "type.name", "fubar")
        message += "\nValid values include: {0}".format(
            ', '.join("'{0}'".format(value) for value in valid_values))

        with ExpectedException(errors.InvalidAttributeError, message):
            dispatch(errors.InvalidAttributeError, "fubar", "fnord",
                     valid_values)


class TestMissingAttributeError(base.BaseTestCase):

    def test_with_single_missing_attribute(self):
        # When passed a single missing attribute, display a message indicating
        #  * the missing attribute
        #  * which component type and component name is missing it.
        missing_attribute = 'herp'
        message = "Missing {0} from an instance of '{1}'".format(
            missing_attribute, 'type.name')

        with ExpectedException(errors.MissingAttributeError, message):
            dispatch(errors.MissingAttributeError, missing_attribute)

        with ExpectedException(errors.MissingAttributeError,
                               message.replace('type.name', 'module')):
            gen_xml(errors.MissingAttributeError, missing_attribute)

    def test_with_multiple_missing_attributes(self):
        # When passed multiple missing attributes, display a message indicating
        #  * the missing attributes
        #  * which component type and component name is missing it.
        missing_attribute = ['herp', 'derp']
        message = "One of {0} must be present in '{1}'".format(
            ', '.join("'{0}'".format(value) for value in missing_attribute),
            'type.name')

        with ExpectedException(errors.MissingAttributeError, message):
            dispatch(errors.MissingAttributeError, missing_attribute)

        with ExpectedException(errors.MissingAttributeError,
                               message.replace('type.name', 'module')):
            gen_xml(errors.MissingAttributeError, missing_attribute)
