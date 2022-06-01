from flask import request
from galatea.tryton import tryton
from flask_babel import gettext as lazy_gettext
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, SelectField, IntegerField, validators

Address = tryton.pool.get('party.address')

_CONTACT_TYPES = [
    ('phone', lazy_gettext('Phone')),
    ('mobile', lazy_gettext('Mobile')),
    ('fax', lazy_gettext('Fax')),
    ('email', lazy_gettext('E-Mail')),
    ('website', 'Website'),
    ('skype', 'Skype'),
    ('irc', 'IRC'),
    ('jabber', 'Jabber'),
]


class AddressForm(Form):
    "Address form"
    name = StringField(lazy_gettext('Name'))
    street = StringField(lazy_gettext('Street'), [validators.InputRequired()])
    city = StringField(lazy_gettext('City'), [validators.InputRequired()])
    postal_code = StringField(lazy_gettext('Postal Code'), [])
    country = SelectField(lazy_gettext('Country'), [validators.InputRequired(), ], coerce=int)
    subdivision = IntegerField(lazy_gettext('Subdivision'), [validators.InputRequired()])
    active = SelectField(lazy_gettext('Active'), choices=[
        ('1', lazy_gettext('Active')),
        ('0', lazy_gettext('Inactive')),
        ])
    if hasattr(Address, 'contact_mechanisms'):
        email = StringField(lazy_gettext('E-Mail'))
        phone = StringField(lazy_gettext('Phone'))
        mobile = StringField(lazy_gettext('Mobile'))
        fax = StringField(lazy_gettext('Fax'))
    if hasattr(Address, 'delivery'):
        delivery = BooleanField(lazy_gettext('Delivery Address'))
    if hasattr(Address, 'invoice'):
        invoice = BooleanField(lazy_gettext('Invoice Address'))
    if hasattr(Address, 'comment_shipment'):
        comment_shipment = StringField(lazy_gettext('Shipment Comment'))

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        return True

    def load(self, address, website):
        self.name.data = address.party_name
        self.street.data = address.street
        self.city.data = address.city
        self.postal_code.data = address.postal_code
        self.country.data = ((address.country and address.country.id)
            or (website.country and website.country.id) or None)
        self.subdivision.data = address.subdivision.id if address.subdivision else None
        self.active.data = '1' if address.active else '0'
        if hasattr(Address, 'contact_mechanisms'):
            self.email.data = address.email
            self.phone.data = address.phone
            self.mobile.data = address.mobile
            self.fax.data = address.fax
        if hasattr(Address, 'delivery'):
            self.delivery.data = 'on' if address.delivery else None
        if hasattr(Address, 'invoice'):
            self.invoice.data = 'on' if address.invoice else None

    def reset(self):
        self.name.data = ''
        self.street.data = ''
        self.city.data = ''
        self.postal_code.data = ''
        self.country.data = ''
        self.subdivision.data = ''
        self.active.data = ''

    def get_address(self):
        address = Address()
        address.party_name = request.form.get('name')
        address.street = request.form.get('street')
        address.city = request.form.get('city')
        address.postal_code = request.form.get('postal_code')
        country = request.form.get('country')
        subdivision = request.form.get('subdivision')
        address.country = int(country) if country and country != '0' else None
        address.subdivision = (int(subdivision)
            if subdivision and subdivision != '0' else None)
        # change active to True/False
        if request.form.get('active'):
            if request.form.get('active') == '0':
                address.active = False
            else:
                address.active = True
        if hasattr(Address, 'contact_mechanisms'):
            address.email = request.form.get('email')
            address.phone = request.form.get('phone')
            address.mobile = request.form.get('mobile')
            address.fax = request.form.get('fax')
        if hasattr(Address, 'delivery'):
            address.delivery = True if request.form.get('delivery') == 'on' else False
        if hasattr(Address, 'invoice'):
            address.invoice = True if request.form.get('invoice') == 'on' else False
        return address


class ContactMechanismForm(Form):
    "Contact Mechanism form"
    type = SelectField(lazy_gettext('Type'), choices=_CONTACT_TYPES)
    value = StringField(lazy_gettext('Value'), [validators.InputRequired()])
    active = SelectField(lazy_gettext('Active'), choices=[
        ('1', lazy_gettext('Active')),
        ('0', lazy_gettext('Inactive')),
        ])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False
        return True

    def reset(self):
        self.type.data = ''
        self.value.data = ''
        self.active.data = ''
