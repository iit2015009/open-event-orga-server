from flask import request, current_app
from flask_jwt import current_identity, _jwt_required
from flask_rest_jsonapi import ResourceDetail, ResourceList, ResourceRelationship
from flask_rest_jsonapi.exceptions import ObjectNotFound
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

from app.api.bootstrap import api
from app.api.schema.events import EventSchemaPublic, EventSchema
from app.api.helpers.permission_manager import has_access
# models
from app.models import db
from app.models.access_code import AccessCode
from app.models.custom_form import CustomForms
from app.models.discount_code import DiscountCode
from app.models.event import Event
from app.models.event_invoice import EventInvoice
from app.models.role_invite import RoleInvite
from app.models.session import Session
from app.models.session_type import SessionType
from app.models.speaker import Speaker
from app.models.speakers_call import SpeakersCall
from app.models.sponsor import Sponsor
from app.models.ticket import Ticket
from app.models.ticket import TicketTag
from app.models.track import Track
from app.models.user import User, ATTENDEE, ORGANIZER, COORGANIZER
from app.models.users_events_role import UsersEventsRoles
from app.models.role import Role
from app.models.ticket_holder import TicketHolder
from app.api.helpers.db import save_to_db, safe_query
from app.api.helpers.files import create_save_image_sizes
from app.models.microlocation import Microlocation
from app.models.email_notification import EmailNotification
from app.models.social_link import SocialLink
from app.models.tax import Tax
from app.models.event_copyright import EventCopyright
from app.models.order import Order


class EventList(ResourceList):
    def before_get(self, args, kwargs):
        if 'Authorization' in request.headers and has_access('is_admin'):
            self.schema = EventSchema
        else:
            self.schema = EventSchemaPublic

    def query(self, view_kwargs):
        query_ = self.session.query(Event).filter_by(state='published')
        if 'Authorization' in request.headers:
            _jwt_required(current_app.config['JWT_DEFAULT_REALM'])
            query2 = self.session.query(Event)
            query2 = query2.join(Event.roles).filter_by(user_id=current_identity.id).join(UsersEventsRoles.role). \
                filter(or_(Role.name == COORGANIZER, Role.name == ORGANIZER))
            query_ = query_.union(query2)

        if view_kwargs.get('user_id') and 'GET' in request.method:
            user = safe_query(db, User, 'id', view_kwargs['user_id'], 'user_id')
            query_ = query_.join(Event.roles).filter_by(user_id=user.id).join(UsersEventsRoles.role). \
                filter(Role.name != ATTENDEE)

        if view_kwargs.get('event_type_id') and 'GET' in request.method:
            query_ = self.session.query(Event).filter(
                getattr(Event, 'event_type_id') == view_kwargs['event_type_id'])

        if view_kwargs.get('event_topic_id') and 'GET' in request.method:
            query_ = self.session.query(Event).filter(
                getattr(Event, 'event_topic_id') == view_kwargs['event_topic_id'])

        if view_kwargs.get('event_sub_topic_id') and 'GET' in request.method:
            query_ = self.session.query(Event).filter(
                getattr(Event, 'event_sub_topic_id') == view_kwargs['event_sub_topic_id'])

        if view_kwargs.get('discount_code_id') and 'GET' in request.method:
            query_ = self.session.query(Event).filter(
                getattr(Event, 'discount_code_id') == view_kwargs['discount_code_id'])

        return query_

    def after_create_object(self, event, data, view_kwargs):
        role = Role.query.filter_by(name=ORGANIZER).first()
        user = User.query.filter_by(id=view_kwargs['user_id']).first()
        uer = UsersEventsRoles(user, event, role)
        save_to_db(uer, 'Event Saved')
        if data.get('original_image_url'):
            uploaded_images = create_save_image_sizes(data['original_image_url'], 'event', event.id)
            self.session.query(Event).filter_by(id=event.id).update(uploaded_images)

    # This permission decorator ensures, you are logged in to create an event
    # and have filter ?withRole to get events associated with logged in user
    decorators = (api.has_permission('create_event'),)
    schema = EventSchema
    data_layer = {'session': db.session,
                  'model': Event,
                  'methods': {'after_create_object': after_create_object,
                              'query': query
                              }}


def get_id(view_kwargs):
    if view_kwargs.get('identifier'):
        event = safe_query(db, Event, 'identifier', view_kwargs['identifier'], 'identifier')
        view_kwargs['id'] = event.id

    if view_kwargs.get('sponsor_id') is not None:
        sponsor = safe_query(db, Sponsor, 'id', view_kwargs['sponsor_id'], 'sponsor_id')
        if sponsor.event_id is not None:
            view_kwargs['id'] = sponsor.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('copyright_id') is not None:
        copyright = safe_query(db, EventCopyright, 'id', view_kwargs['copyright_id'], 'copyright_id')
        if copyright.event_id is not None:
            view_kwargs['id'] = copyright.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('track_id') is not None:
        track = safe_query(db, Track, 'id', view_kwargs['track_id'], 'track_id')
        if track.event_id is not None:
            view_kwargs['id'] = track.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('session_type_id') is not None:
        session_type = safe_query(db, SessionType, 'id', view_kwargs['session_type_id'], 'session_type_id')
        if session_type.event_id is not None:
            view_kwargs['id'] = session_type.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('event_invoice_id') is not None:
        event_invoice = safe_query(db, EventInvoice, 'id', view_kwargs['event_invoice_id'], 'event_invoice_id')
        if event_invoice.event_id is not None:
            view_kwargs['id'] = event_invoice.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('discount_code_id') is not None:
        discount_code = safe_query(db, DiscountCode, 'id', view_kwargs['discount_code_id'], 'discount_code_id')
        if discount_code.event_id is not None:
            view_kwargs['id'] = discount_code.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('session_id') is not None:
        sessions = safe_query(db, Session, 'id', view_kwargs['session_id'], 'session_id')
        if sessions.event_id is not None:
            view_kwargs['id'] = sessions.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('social_link_id') is not None:
        social_link = safe_query(db, SocialLink, 'id', view_kwargs['social_link_id'], 'social_link_id')
        if social_link.event_id is not None:
            view_kwargs['id'] = social_link.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('tax_id') is not None:
        tax = safe_query(db, Tax, 'id', view_kwargs['tax_id'], 'tax_id')
        if tax.event_id is not None:
            view_kwargs['id'] = tax.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('user_id') is not None:
        try:
            discount_code = db.session.query(DiscountCode).filter_by(
                id=view_kwargs['discount_code_id']).one()
        except NoResultFound:
            raise ObjectNotFound({'parameter': 'discount_code_id'},
                                 "DiscountCode: {} not found".format(view_kwargs['discount_code_id']))
        else:
            if discount_code.event_id is not None:
                view_kwargs['id'] = discount_code.event_id
            else:
                view_kwargs['id'] = None

    if view_kwargs.get('speakers_call_id') is not None:
        speakers_call = safe_query(db, SpeakersCall, 'id', view_kwargs['speakers_call_id'], 'speakers_call_id')
        if speakers_call.event_id is not None:
            view_kwargs['id'] = speakers_call.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('ticket_id') is not None:
        ticket = safe_query(db, Ticket, 'id', view_kwargs['ticket_id'], 'ticket_id')
        if ticket.event_id is not None:
            view_kwargs['id'] = ticket.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('ticket_tag_id') is not None:
        ticket_tag = safe_query(db, TicketTag, 'id', view_kwargs['ticket_tag_id'], 'ticket_tag_id')
        if ticket_tag.event_id is not None:
            view_kwargs['id'] = ticket_tag.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('role_invite_id') is not None:
        role_invite = safe_query(db, RoleInvite, 'id', view_kwargs['role_invite_id'], 'role_invite_id')
        if role_invite.event_id is not None:
            view_kwargs['id'] = role_invite.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('users_events_role_id') is not None:
        users_events_role = safe_query(db, UsersEventsRoles, 'id', view_kwargs['users_events_role_id'],
                                       'users_events_role_id')
        if users_events_role.event_id is not None:
            view_kwargs['id'] = users_events_role.event_id

    if view_kwargs.get('access_code_id') is not None:
        access_code = safe_query(db, AccessCode, 'id', view_kwargs['access_code_id'], 'access_code_id')
        if access_code.event_id is not None:
            view_kwargs['id'] = access_code.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('speaker_id'):
        try:
            speaker = db.session.query(Speaker).filter_by(id=view_kwargs['speaker_id']).one()
        except NoResultFound:
            raise ObjectNotFound({'parameter': 'speaker_id'},
                                 "Speaker: {} not found".format(view_kwargs['speaker_id']))
        else:
            if speaker.event_id:
                view_kwargs['id'] = speaker.event_id
            else:
                view_kwargs['id'] = None

    if view_kwargs.get('email_notification_id'):
        try:
            email_notification = db.session.query(EmailNotification).filter_by(
                id=view_kwargs['email_notification_id']).one()
        except NoResultFound:
            raise ObjectNotFound({'parameter': 'email_notification_id'},
                                 "Email Notification: {} not found".format(view_kwargs['email_notification_id']))
        else:
            if email_notification.event_id:
                view_kwargs['id'] = email_notification.event_id
            else:
                view_kwargs['id'] = None

    if view_kwargs.get('microlocation_id'):
        try:
            microlocation = db.session.query(Microlocation).filter_by(id=view_kwargs['microlocation_id']).one()
        except NoResultFound:
            raise ObjectNotFound({'parameter': 'microlocation_id'},
                                 "Microlocation: {} not found".format(view_kwargs['microlocation_id']))
        else:
            if microlocation.event_id:
                view_kwargs['id'] = microlocation.event_id
            else:
                view_kwargs['id'] = None

    if view_kwargs.get('attendee_id'):
        attendee = safe_query(db, TicketHolder, 'id', view_kwargs['attendee_id'], 'attendee_id')
        if attendee.event_id is not None:
            view_kwargs['id'] = attendee.event_id
        else:
            view_kwargs['id'] = None

    if view_kwargs.get('custom_form_id') is not None:
        custom_form = safe_query(db, CustomForms, 'id', view_kwargs['custom_form_id'], 'custom_form_id')
        if custom_form.event_id is not None:
            view_kwargs['id'] = custom_form.event_id
        else:
            view_kwargs['id'] = None

    return view_kwargs


class EventDetail(ResourceDetail):
    def before_get(self, args, kwargs):
        kwargs = get_id(kwargs)
        if 'Authorization' in request.headers and has_access('is_coorganizer', event_id=kwargs['id']):
            self.schema = EventSchema
        else:
            self.schema = EventSchemaPublic

    def before_get_object(self, view_kwargs):
        get_id(view_kwargs)

        if view_kwargs.get('order_identifier') is not None:
            order = safe_query(self, Order, 'identifier', view_kwargs['order_identifier'], 'order_identifier')
            if order.event_id is not None:
                view_kwargs['id'] = order.event_id
            else:
                view_kwargs['id'] = None

    def before_update_object(self, event, data, view_kwargs):
        if data.get('original_image_url') and data['original_image_url'] != event.original_image_url:
            uploaded_images = create_save_image_sizes(data['original_image_url'], 'event', event.id)
            data['original_image_url'] = uploaded_images['original_image_url']
            data['large_image_url'] = uploaded_images['large_image_url']
            data['thumbnail_image_url'] = uploaded_images['thumbnail_image_url']
            data['icon_image_url'] = uploaded_images['icon_image_url']

    decorators = (api.has_permission('is_coorganizer', methods="PATCH,DELETE", fetch="id", fetch_as="event_id",
                                     model=Event), )
    schema = EventSchema
    data_layer = {'session': db.session,
                  'model': Event,
                  'methods': {
                      'before_get_object': before_get_object,
                      'before_update_object': before_update_object
                  }}


class EventRelationship(ResourceRelationship):

    def before_get_object(self, view_kwargs):
        if view_kwargs.get('identifier'):
            event = safe_query(db, Event, 'identifier', view_kwargs['identifier'], 'identifier')
            view_kwargs['id'] = event.id

    decorators = (api.has_permission('is_coorganizer', fetch="id", fetch_as="event_id",
                                     model=Event),)
    schema = EventSchema
    data_layer = {'session': db.session,
                  'model': Event,
                  'methods': {'before_get_object': before_get_object}
                  }
