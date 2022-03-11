from flask import (Blueprint, render_template, abort, g, url_for, request,
    current_app, flash, redirect, session, jsonify)
from galatea.tryton import tryton
from galatea.helpers import login_required, manager_required
from flask_babel import gettext as _
from trytond.transaction import Transaction
from .forms import AddressForm, ContactMechanismForm

party = Blueprint('party', __name__, template_folder='templates')

GALATEA_WEBSITE = current_app.config.get('TRYTON_GALATEA_SITE')

Website = tryton.pool.get('galatea.website')
PartyParty = tryton.pool.get('party.party')
Address = tryton.pool.get('party.address')
ContactMechanism = tryton.pool.get('party.contact_mechanism')

BREADCUMB_MY_ACCOUNT = current_app.config.get('BREADCUMB_MY_ACCOUNT')


class Party(object):
    '''
    This object is used to hold the settings used for party configuration.
    '''
    def __init__(self, app=None):
        self.address_form = AddressForm
        self.contact_mechanism_form = ContactMechanismForm

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['Party'] = self


def base_breadcrumbs():
    breadcrumbs = []
    if BREADCUMB_MY_ACCOUNT:
        breadcrumbs.append({
                'slug': url_for(BREADCUMB_MY_ACCOUNT, lang=g.language),
                'name': _('My Account'),
                })
    return breadcrumbs


@party.route("/admin/json/party", endpoint="admin-party-json")
@manager_required
@tryton.transaction()
def admin_party_json(lang):
    '''Admin Party JSON'''

    def date_handler(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    domain = []
    q = request.args.get('q')
    if q:
        domain.append(('rec_name', 'ilike', '%'+q+'%'))
    elif request.args:
        for k, v in request.args.items():
            if k == 'fields_names':
                continue
            if v.isdigit():
                v = int(v)
            domain.append((k, '=', v))

    fields_names = request.args.get('fields_names', 'rec_name').split(',')

    try:
        parties = PartyParty.search_read(domain, fields_names=fields_names)
    except:
        parties = []

    return jsonify(results=parties)

@party.route("/admin/json/address", endpoint="admin-address-json")
@manager_required
@tryton.transaction()
def admin_address_json(lang):
    '''Admin Address JSON'''

    def date_handler(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj

    domain = []
    q = request.args.get('q')
    if q:
        domain.append(('rec_name', 'ilike', '%'+q+'%'))
    elif request.args:
        for k, v in request.args.items():
            if k == 'fields_names':
                continue
            if v.isdigit():
                v = int(v)
            domain.append((k, '=', v))
    fields_names = request.args.get('fields_names', 'rec_name').split(',')

    try:
        addresses = Address.search_read(domain, fields_names=fields_names)
    except:
        addresses = []

    return jsonify(results=addresses)

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
        parties = PartyParty.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = parties

    form = current_app.extensions['Party'].address_form(active='1')
    if website.countries:
        countries = [(c.id, c.name) for c in website.countries]
    else:
        countries = [(website.country.id, website.country.name)]
    form.country.choices = countries

    if form.validate_on_submit():
        address = form.get_address()

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
            Address.write(addresses, address._save_values)
        else:
            address.party = party
            Address.create([address._save_values])
        flash(_('Successfully saved address.'))
        form.reset()
    else:
        errors = [_('Error saved address.')]
        for k, v in form.errors.items():
            errors.append('%s: %s' % (getattr(form, k).label.text, ', '.join(v)))
        flash(errors, 'danger')

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
        address, = addresses
        party = address.party

    form = current_app.extensions['Party'].address_form()
    form.load(address, website)
    if website.countries:
        countries = [(c.id, c.name) for c in website.countries]
    else:
        countries = [(website.country.id, website.country.name)]
    form.country.choices = countries

    #breadcumbs
    breadcrumbs = base_breadcrumbs()
    breadcrumbs.append({
        'slug': url_for('.party', lang=g.language),
        'name': address.party.rec_name,
        })

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
        parties = PartyParty.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = parties

    form = current_app.extensions['Party'].address_form(country=website.country.id, active=True)
    if website.countries:
        countries = [(c.id, c.name) for c in website.countries]
    else:
        countries = [(website.country.id, website.country.name)]
    form.country.choices = countries

    if hasattr(Address, 'delivery'):
        form.delivery.data = 'on'
    if hasattr(Address, 'invoice'):
        form.invoice.data = 'on'

    #breadcumbs
    breadcrumbs = base_breadcrumbs()
    breadcrumbs.append({
        'slug': url_for('.party', lang=g.language),
        'name': party.rec_name,
        })

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
        parties = PartyParty.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = parties

    form = current_app.extensions['Party'].contact_mechanism_form(active='1')
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
        contact_mechanism, = contact_mechanismes
        party = contact_mechanism.party

    form = current_app.extensions['Party'].contact_mechanism_form(
        type = contact_mechanism.type,
        value = contact_mechanism.value,
        active = '1' if contact_mechanism.active else '0',
        )

    #breadcumbs
    breadcrumbs = base_breadcrumbs()
    breadcrumbs.append({
        'slug': url_for('.party', lang=g.language),
        'name': contact_mechanism.party.rec_name,
        })

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
        parties = PartyParty.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = parties

    form = current_app.extensions['Party'].contact_mechanism_form(type='phone', active=True)

    #breadcumbs
    breadcrumbs = base_breadcrumbs()
    breadcrumbs.append({
        'slug': url_for('.party', lang=g.language),
        'name': party.rec_name,
        })

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
        parties = PartyParty.search([
            ('id', '=', customer),
            ], limit=1)
        if not parties:
            abort(404)
        party, = parties

    #breadcumbs
    breadcrumbs = base_breadcrumbs()
    breadcrumbs.append({
        'slug': url_for('.party', lang=g.language),
        'name': party.rec_name,
        })

    return render_template('party.html',
            breadcrumbs=breadcrumbs,
            party=party,
            )
