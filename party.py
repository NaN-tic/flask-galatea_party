from flask import Blueprint, render_template, abort, g, url_for, request, \
    current_app, flash, redirect, session
from galatea.tryton import tryton
from galatea.helpers import login_required
from flask.ext.babel import gettext as _, lazy_gettext
from flask.ext.wtf import Form
from wtforms import TextField, SelectField, IntegerField, validators
from trytond.transaction import Transaction

party = Blueprint('party', __name__, template_folder='templates')

GALATEA_WEBSITE = current_app.config.get('TRYTON_GALATEA_SITE')

Website = tryton.pool.get('galatea.website')
Party = tryton.pool.get('party.party')
Address = tryton.pool.get('party.address')
ContactMechanism = tryton.pool.get('party.contact_mechanism')

_CONTACT_TYPES = [
    ('phone', lazy_gettext('Phone')),
    ('mobile', lazy_gettext('Mobile')),
    ('fax', lazy_gettext('Fax')),
    ('email', 'E-Mail'),
    ('website', 'Website'),
    ('skype', 'Skype'),
    ('irc', 'IRC'),
    ('jabber', 'Jabber'),
]


class AddressForm(Form):
    "Address form"
    name = TextField(lazy_gettext('Name'))
    street = TextField(lazy_gettext('Street'), [validators.Required()])
    city = TextField(lazy_gettext('City'), [validators.Required()])
    zip = TextField(lazy_gettext('Zip'), [validators.Required()])
    country = SelectField(lazy_gettext('Country'), [validators.Required(), ], coerce=int)
    subdivision = IntegerField(lazy_gettext('Subdivision'), [validators.Required()])
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
        self.name.data = ''
        self.street.data = ''
        self.city.data = ''
        self.zip.data = ''
        self.country.data = ''
        self.subdivision.data = ''
        self.active.data = ''


class ContactMechanismForm(Form):
    "Contact Mechanism form"
    type = SelectField(lazy_gettext('Type'), choices=_CONTACT_TYPES)
    value = TextField(lazy_gettext('Value'), [validators.Required()])
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


@party.route("/address/save", methods=["GET", "POST"], endpoint="address-save")
@login_required
@tryton.transaction()
def address_save(lang):
    '''Save Address'''
    if request.method == 'GET':
        return redirect(url_for('.party', lang=g.language))

    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        parties = Party.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = Party.browse(parties)

    form = AddressForm(active='1')
    if website.countries:
        countries = [(c.id, c.name) for c in website.countries]
    else:
        countries = [(website.country.id, website.country.name)]
    form.country.choices = countries

    if form.validate_on_submit():
        data = {
            'name': request.form.get('name', None),
            'street': request.form.get('street'),
            'city': request.form.get('city'),
            'zip': request.form.get('zip'),
            'country': request.form.get('country'),
            'subdivision': request.form.get('subdivision'),
            }

        # change active to True/False
        if request.form.get('active'):
            if request.form.get('active') == '0':
                data['active'] = False
            else:
                data['active'] = True

        if request.form.get('id'):
            with Transaction().set_context(active_test=False):
                addresses = Address.search([
                    ('party', '=', party),
                    ('id', '=', request.form.get('id')),
                    ], limit=1)
            if not addresses:
                flash(_('You try edit an address and not have permissions!'),
                    'danger')
                return redirect(url_for('.party', lang=g.language))
            Address.write(addresses, data)
        else:
            data['party'] = party
            Address.create([data])

        flash(_('Address saved successfully!'))
    else:
        flash(_('Error saved Address!'), 'danger')

    form.reset()
    return redirect(url_for('.party', lang=g.language))

@party.route("/address/<int:id>", endpoint="address-edit")
@login_required
@tryton.transaction()
def address_edit(lang, id):
    '''Edit Address'''
    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        addresses = Address.search([
            ('id', '=', id),
            ('party', '=', customer),
            ], limit=1)
        if not addresses:
            abort(404)
        address, = Address.browse(addresses)
        party = address.party

    form = AddressForm(
        name = address.name,
        street = address.street,
        city = address.city,
        zip = address.zip,
        country = address.country.id if address.country else website.country.id,
        subdivision = address.subdivision.id if address.subdivision else None,
        active = '1' if address.active else '0',
        )
    if website.countries:
        countries = [(c.id, c.name) for c in website.countries]
    else:
        countries = [(website.country.id, website.country.name)]
    form.country.choices = countries

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('my-account', lang=g.language),
        'name': _('My Account'),
        }, {
        'slug': url_for('.party', lang=g.language),
        'name': address.party.rec_name,
        }]

    return render_template('party-address.html',
            breadcrumbs=breadcrumbs,
            party=party,
            address=address,
            form=form,
            )

@party.route("/address/", endpoint="address-new")
@login_required
@tryton.transaction()
def address_new(lang):
    '''New Address'''
    websites = Website.search([
        ('id', '=', GALATEA_WEBSITE),
        ], limit=1)
    if not websites:
        abort(404)
    website, = websites

    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        parties = Party.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = Party.browse(parties)

    form = AddressForm(country=website.country.id, active=True)
    if website.countries:
        countries = [(c.id, c.name) for c in website.countries]
    else:
        countries = [(website.country.id, website.country.name)]
    form.country.choices = countries

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('my-account', lang=g.language),
        'name': _('My Account'),
        }, {
        'slug': url_for('.party', lang=g.language),
        'name': party.rec_name,
        }]

    return render_template('party-address.html',
            breadcrumbs=breadcrumbs,
            party=party,
            address=None,
            form=form,
            )

@party.route("/contact-mechanism/save", methods=["GET", "POST"], endpoint="contact-mechanism-save")
@login_required
@tryton.transaction()
def contact_mechanism_save(lang):
    '''Save Contact Mechanism'''
    if request.method == 'GET':
        return redirect(url_for('.party', lang=g.language))

    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        parties = Party.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = Party.browse(parties)

    form = ContactMechanismForm(active='1')
    if form.validate_on_submit():
        data = {
            'type': request.form.get('type', 'phone'),
            'value': request.form.get('value'),
            }

        # change active to True/False
        if request.form.get('active'):
            if request.form.get('active') == '0':
                data['active'] = False
            else:
                data['active'] = True

        if request.form.get('id'):
            contact_mechanismes = ContactMechanism.search([
                ('party', '=', party),
                ('id', '=', request.form.get('id')),
                ], limit=1)
            if not contact_mechanismes:
                flash(_('You try edit a contact mechanism and not have permissions!'),
                    'danger')
                return redirect(url_for('.party', lang=g.language))
            ContactMechanism.write(contact_mechanismes, data)
        else:
            data['party'] = party
            ContactMechanism.create([data])

        flash(_('Contact Mechanism saved successfully!'))
    else:
        flash(_('Error saved Contact Mechanism!'), 'danger')

    form.reset()
    return redirect(url_for('.party', lang=g.language))

@party.route("/contact-mechanism/<int:id>", endpoint="contact-mechanism-edit")
@login_required
@tryton.transaction()
def contact_mechanism_edit(lang, id):
    '''Edit Contact Mechanism'''
    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        contact_mechanismes = ContactMechanism.search([
            ('id', '=', id),
            ('party', '=', customer),
            ], limit=1)
        if not contact_mechanismes:
            abort(404)
        contact_mechanism, = ContactMechanism.browse(contact_mechanismes)
        party = contact_mechanism.party

    form = ContactMechanismForm(
        type = contact_mechanism.type,
        value = contact_mechanism.value,
        active = '1' if contact_mechanism.active else '0',
        )

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('my-account', lang=g.language),
        'name': _('My Account'),
        }, {
        'slug': url_for('.party', lang=g.language),
        'name': contact_mechanism.party.rec_name,
        }]

    return render_template('party-contact-mechanism.html',
            breadcrumbs=breadcrumbs,
            party=party,
            contact_mechanism=contact_mechanism,
            form=form,
            )

@party.route("/contact-mechanism/", endpoint="contact-mechanism-new")
@login_required
@tryton.transaction()
def contact_mechanism_new(lang):
    '''New Contact Mechanism'''
    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        parties = Party.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = Party.browse(parties)

    form = ContactMechanismForm(type='phone', active=True)

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('my-account', lang=g.language),
        'name': _('My Account'),
        }, {
        'slug': url_for('.party', lang=g.language),
        'name': party.rec_name,
        }]

    return render_template('party-contact-mechanism.html',
            breadcrumbs=breadcrumbs,
            party=party,
            contact_mechanism=None,
            form=form,
            )

@party.route("/", endpoint="party")
@login_required
@tryton.transaction()
def party_detail(lang):
    '''Party Detail'''
    customer = session.get('customer')

    with Transaction().set_context(active_test=False):
        parties = Party.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = Party.browse(parties)

    #breadcumbs
    breadcrumbs = [{
        'slug': url_for('my-account', lang=g.language),
        'name': _('My Account'),
        }, {
        'slug': url_for('.party', lang=g.language),
        'name': party.rec_name,
        }]

    return render_template('party.html',
            breadcrumbs=breadcrumbs,
            party=party,
            )