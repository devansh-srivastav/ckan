# encoding: utf-8

import datetime
import re

import requests

from ckan.common import config
from ckan.common import asbool, asint
import six
from six import text_type, string_types

from ckan.common import _, json
import ckan.lib.maintain as maintain

log = __import__('logging').getLogger(__name__)

TIMEOUT = asint(config.get('ckan.requests.timeout', 5))

class License(object):
    """Domain object for a license."""

    def __init__(self, data):
        # convert old keys if necessary
        if 'is_okd_compliant' in data:
            data['od_conformance'] = 'approved' \
                if asbool(data['is_okd_compliant']) else ''
            del data['is_okd_compliant']
        if 'is_osi_compliant' in data:
            data['osd_conformance'] = 'approved' \
                if asbool(data['is_osi_compliant']) else ''
            del data['is_osi_compliant']

        self._data = data
        for (key, value) in self._data.items():
            if key == 'date_created':
                # Parse ISO formatted datetime.
                value = datetime.datetime(
                    *list(int(item) for item in re.split(r'[^\d]', value)))
                self._data[key] = value
            elif isinstance(value, str):
                if six.PY2:
                    # Convert str to unicode
                    # (keeps Pylons and SQLAlchemy happy).
                    value = six.ensure_text(value)
                self._data[key] = value

    def __getattr__(self, name):
        if name == 'is_okd_compliant':
            log.warn('license.is_okd_compliant is deprecated - use '
                     'od_conformance instead.')
            return self._data['od_conformance'] == 'approved'
        if name == 'is_osi_compliant':
            log.warn('license.is_osi_compliant is deprecated - use '
                     'osd_conformance instead.')
            return self._data['osd_conformance'] == 'approved'
        try:
            return self._data[name]
        except KeyError as e:
            # Python3 strictly requires `AttributeError` for correct
            # behavior of `hasattr`
            raise AttributeError(*e.args)

    @maintain.deprecated("License.__getitem__() is deprecated and will be "
                         "removed in a future version of CKAN. Instead, "
                         "please use attribute access.")
    def __getitem__(self, key):
        '''NB This method is deprecated and will be removed in a future version
        of CKAN. Instead, please use attribute access.
        '''
        return self.__getattr__(key)

    def isopen(self):
        if not hasattr(self, '_isopen'):
            self._isopen = self.od_conformance == 'approved' or \
                self.osd_conformance == 'approved'
        return self._isopen

    @maintain.deprecated("License.as_dict() is deprecated and will be "
                         "removed in a future version of CKAN. Instead, "
                         "please use attribute access.")
    def as_dict(self):
        '''NB This method is deprecated and will be removed in a future version
        of CKAN. Instead, please use attribute access.
        '''
        data = self._data.copy()
        if 'date_created' in data:
            value = data['date_created']
            value = value.isoformat()
            data['date_created'] = value

        # deprecated keys
        if 'od_conformance' in data:
            data['is_okd_compliant'] = data['od_conformance'] == 'approved'
        if 'osd_conformance' in data:
            data['is_osi_compliant'] = data['osd_conformance'] == 'approved'

        return data


class LicenseRegister(object):
    """Dictionary-like interface to a group of licenses."""

    def __init__(self):
        group_url = config.get('licenses_group_url', None)
        if group_url:
            self.load_licenses(group_url)
        else:
            default_license_list = [
                L0(),
                L1(),
                L2(),
                L3(),
                L4(),
                L5(),
                L6(),
                L7(),
                L8(),
                L9(),
                L10(),
                L11(),
                L12(),
                L13(),
                L14(),
                L15(),
                L16(),
                L17(),
                L18(),
                L19(),
                L20(),
                L21(),
                L22(),
                L23(),
                L24(),
                L25(),
                L26(),
                L27(),
                L28(),
                L29(),
                L30(),
                L31(),
                L32(),
                L33(),
                L34()
                ]
            self._create_license_list(default_license_list)

    def load_licenses(self, license_url):
        try:
            if license_url.startswith('file://'):
                with open(license_url.replace('file://', ''), 'r') as f:
                    license_data = json.load(f)
            else:
                response = requests.get(license_url, timeout=TIMEOUT)
                license_data = response.json()
        except requests.RequestException as e:
            msg = "Couldn't get the licenses file {}: {}".format(license_url, e)
            raise Exception(msg)
        except ValueError as e:
            msg = "Couldn't parse the licenses file {}: {}".format(license_url, e)
            raise Exception(msg)
        for license in license_data:
            if isinstance(license, string_types):
                license = license_data[license]
        self._create_license_list(license_data, license_url)

    def _create_license_list(self, license_data, license_url=''):
        if isinstance(license_data, dict):
            self.licenses = [License(entity) for entity in license_data.values()]
        elif isinstance(license_data, list):
            self.licenses = [License(entity) for entity in license_data]
        else:
            msg = "Licenses at %s must be dictionary or list" % license_url
            raise ValueError(msg)

    def __getitem__(self, key, default=Exception):
        for license in self.licenses:
            if key == license.id:
                return license
        if default != Exception:
            return default
        else:
            raise KeyError("License not found: %s" % key)

    def get(self, key, default=None):
        return self.__getitem__(key, default=default)

    def keys(self):
        return [license.id for license in self.licenses]

    def values(self):
        return self.licenses

    def items(self):
        return [(license.id, license) for license in self.licenses]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.licenses)


class DefaultLicense(dict):
    ''' The license was a dict but this did not allow translation of the
    title.  This is a slightly changed dict that allows us to have the title
    as a property and so translated. '''

    domain_content = False
    domain_data = False
    domain_software = False
    family = ''
    is_generic = False
    od_conformance = 'not reviewed'
    osd_conformance = 'not reviewed'
    maintainer = ''
    status = 'active'
    url = ''
    title = ''
    id = ''

    keys = ['domain_content',
            'id',
            'domain_data',
            'domain_software',
            'family',
            'is_generic',
            'od_conformance',
            'osd_conformance',
            'maintainer',
            'status',
            'url',
            'title']

    def __getitem__(self, key):
        ''' behave like a dict but get from attributes '''
        if key in self.keys:
            value = getattr(self, key)
            if isinstance(value, str):
                return text_type(value)
            else:
                return value
        else:
            raise KeyError(key)

    def copy(self):
        ''' create a dict of the license used by the licenses api '''
        out = {}
        for key in self.keys:
            out[key] = text_type(getattr(self, key))
        return out

# class LicenseNotSpecified(DefaultLicense):
#     id = "notspecified"
#     is_generic = True

#     @property
#     def title(self):
#         return _("License not specified")

# class LicenseOpenDataCommonsPDDL(DefaultLicense):
#     domain_data = True
#     id = "odc-pddl"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/odc-pddl"

#     @property
#     def title(self):
#         return _("Open Data Commons Public Domain Dedication and License (PDDL)")

# class LicenseOpenDataCommonsOpenDatabase(DefaultLicense):
#     domain_data = True
#     id = "odc-odbl"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/odc-odbl"

#     @property
#     def title(self):
#         return _("Open Data Commons Open Database License (ODbL)")

# class LicenseOpenDataAttribution(DefaultLicense):
#     domain_data = True
#     id = "odc-by"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/odc-by"

#     @property
#     def title(self):
#         return _("Open Data Commons Attribution License")

# class LicenseCreativeCommonsZero(DefaultLicense):
#     domain_content = True
#     domain_data = True
#     id = "cc-zero"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/cc-zero"

#     @property
#     def title(self):
#         return _("Creative Commons CCZero")

# class LicenseCreativeCommonsAttribution(DefaultLicense):
#     id = "cc-by"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/cc-by"

#     @property
#     def title(self):
#         return _("Creative Commons Attribution")

# class LicenseCreativeCommonsAttributionShareAlike(DefaultLicense):
#     domain_content = True
#     id = "cc-by-sa"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/cc-by-sa"

#     @property
#     def title(self):
#         return _("Creative Commons Attribution Share-Alike")

# class LicenseGNUFreeDocument(DefaultLicense):
#     domain_content = True
#     id = "gfdl"
#     od_conformance = 'approved'
#     url = "http://www.opendefinition.org/licenses/gfdl"
#     @property
#     def title(self):
#         return _("GNU Free Documentation License")

# class LicenseOtherOpen(DefaultLicense):
#     domain_content = True
#     id = "other-open"
#     is_generic = True
#     od_conformance = 'approved'

#     @property
#     def title(self):
#         return _("Other (Open)")

# class LicenseOtherPublicDomain(DefaultLicense):
#     domain_content = True
#     id = "other-pd"
#     is_generic = True
#     od_conformance = 'approved'

#     @property
#     def title(self):
#         return _("Other (Public Domain)")

# class LicenseOtherAttribution(DefaultLicense):
#     domain_content = True
#     id = "other-at"
#     is_generic = True
#     od_conformance = 'approved'

#     @property
#     def title(self):
#         return _("Other (Attribution)")

# class LicenseOpenGovernment(DefaultLicense):
#     domain_content = True
#     id = "uk-ogl"
#     od_conformance = 'approved'
#     # CS: bad_spelling ignore
#     url = "http://reference.data.gov.uk/id/open-government-licence"

#     @property
#     def title(self):
#         # CS: bad_spelling ignore
#         return _("UK Open Government Licence (OGL)")

# class LicenseCreativeCommonsNonCommercial(DefaultLicense):
#     id = "cc-nc"
#     url = "http://creativecommons.org/licenses/by-nc/2.0/"

#     @property
#     def title(self):
#         return _("Creative Commons Non-Commercial (Any)")

# class LicenseOtherNonCommercial(DefaultLicense):
#     id = "other-nc"
#     is_generic = True

#     @property
#     def title(self):
#         return _("Other (Non-Commercial)")

# class LicenseOtherClosed(DefaultLicense):
#     id = "other-closed"
#     is_generic = True

#     @property
#     def title(self):
#         return _("Other (Not Open)")


# class LicenseInflow(DefaultLicense):
#     id = "inflow"
#     url = ''

#     @property
#     def title(self):
#         return _("Inflow")

# class L0(DefaultLicense):
#     id = "L0"
#     url=''

#     @property
#     def title(self):
#         return _("License Nicht Angeben")

# class L1(DefaultLicense):
#     id = "L1"
#     url = ''

#     @property
#     def title(self):
#         return _("Amtliches Werk, lizenzfrei nach §5 Abs. 1 UrhG")

# class L2(DefaultLicense):
#     id = "L2"
#     url = ''

#     @property
#     def title(self):
#         return _("Andere Freeware Lizenz")

# class L3(DefaultLicense):
#     id = "L2"
#     url = ''

#     @property
#     def title(self):
#         return _("Andere geschlossene Lizenz")

# class L4(DefaultLicense):
#     id = "L4"
#     url = ''

#     @property
#     def title(self):
#         return _("Andere kommerzielle Lizenz")

# class L5(DefaultLicense):
#     id = "L5"
#     url = ''

#     @property
#     def title(self):
#         return _("Andere offene Lizenz")

# class L6(DefaultLicense):
#     id = "L6"
#     url = ''

#     @property
#     def title(self):
#         return _("Andere Open Source Lizenz")

# class L7(DefaultLicense):
#     id = "L7"
#     url = ''

#     @property
#     def title(self):
#         return _("BSD Lizenz")

class L8(DefaultLicense):
    id = "L8"
    url = ''

    @property
    def title(self):
        return _("Creative Commons CC Zero Licence (cc-zero)")

class L9(DefaultLicense):
    id = "L9"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung (CC-BY)")

class L10(DefaultLicense):
    id = "L10"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung 3.0 Deutschland (CC BY 3.0 DE)")

class L11(DefaultLicense):
    id = "L11"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung — 4.0 International (CC BY 4.0)")

class L12(DefaultLicense):
    id = "L12"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - Keine Bearbeitung (CC BY-ND)")

class L13(DefaultLicense):
    id = "L13"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung -- Keine Bearbeitung 3.0 Unported (CC BY-ND 3.0)")

class L14(DefaultLicense):
    id = "L14"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - - Keine Bearbeitung 4.0 International (CC BY-ND 4.0)")

class L15(DefaultLicense):
    id = "L15"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - Nicht kommerziell (CC BY-NC)")

class L16(DefaultLicense):
    id = "L16"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung-Nicht kommerziell 3.0 Deutschland (CC BY-NC 3.0 DE)")

class L17(DefaultLicense):
    id = "L17"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - Nicht kommerziell 4.0 International (CC BY-NC 4.0)")

class L18(DefaultLicense):
    id = "L18"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - Weitergabe unter gleichen Bedingungen (CC-BY-SA)")

class L19(DefaultLicense):
    id = "L19"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - Weitergabe unter gleichen Bedingungen 3.0 Deutschland (CC BY-SA 3.0 DE)")

class L20(DefaultLicense):
    id = "L20"
    url = ''

    @property
    def title(self):
        return _("Creative Commons Namensnennung - Weitergabe unter gleichen Bedingungen 4.0 International (CC-BY-SA 4.0)")

class L21(DefaultLicense):
    id = "L21"
    url = ''

    @property
    def title(self):
        return _("Datenlizenz Deutschland Namensnennung 1.0")

class L22(DefaultLicense):
    id = "L22"
    url = ''

    @property
    def title(self):
        return _("Datenlizenz Deutschland Namensnennung 2.0")

# class L23(DefaultLicense):
#     id = "L23"
#     url = ''

#     @property
#     def title(self):
#         return _("Datenlizenz Deutschland Namensnennung nicht-kommerziell 1.0")

class L24(DefaultLicense):
    id = "L24"
    url = ''

    @property
    def title(self):
        return _("Datenlizenz Deutschland — Zero — Version 2.0")

# class L25(DefaultLicense):
#     id = "L25"
#     url = ''

#     @property
#     def title(self):
#         return _("Freie Softwarelizenz der Apache Software Foundation")

class L26(DefaultLicense):
    id = "L26"
    url = ''

    @property
    def title(self):
        return _("GNU Free Documentation License (GFDL)")

class L27(DefaultLicense):
    id = "L27"
    url = ''

    @property
    def title(self):
        return _("GNU General Public License version 3.0 (GPLv3)")

# class L28(DefaultLicense):
#     id = "L28"
#     url = ''

#     @property
#     def title(self):
#         return _("Mozilla Public License 2.0 (MPL)")

class L29(DefaultLicense):
    id = "L29"
    url = ''

    @property
    def title(self):
        return _("Nutzungsbestimmungen fur die Bereitstellung von Geodaten des Bundes")

# class L30(DefaultLicense):
#     id = "L30"
#     url = ''

#     @property
#     def title(self):
#         return _("Nutzungsbestimmungen fur die Bereitstellung von Geodaten des Landes Berlin")

class L31(DefaultLicense):
    id = "L31"
    url = ''

    @property
    def title(self):
        return _("Open Data Commons Attribution License (ODC-BY 1.0)")

class L32(DefaultLicense):
    id = "L32"
    url = ''

    @property
    def title(self):
        return _("Open Data Commons Open Database License (ODbL)")

class L33(DefaultLicense):
    id = "L33"
    url = ''

    @property
    def title(self):
        return _("Open Data Commons Public Domain Dedication and Licence (ODC PDDL)")

# class L34(DefaultLicense):
#     id = "L34"
#     url = ''

#     @property
#     def title(self):
#         return _("Public Domain Mark 1.0 (PDM)")