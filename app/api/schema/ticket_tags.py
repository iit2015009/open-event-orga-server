from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema, Relationship

from app.api.helpers.utilities import dasherize


class TicketTagSchema(Schema):
    """
    Api schema for TicketTag Model
    """

    class Meta:
        """
        Meta class for TicketTag Api Schema
        """
        type_ = 'ticket-tag'
        self_view = 'v1.ticket_tag_detail'
        self_view_kwargs = {'id': '<id>'}
        inflect = dasherize

    id = fields.Str(dump_only=True)
    name = fields.Str(allow_none=True)
    tickets = Relationship(attribute='tickets',
                           self_view='v1.ticket_tag_ticket',
                           self_view_kwargs={'id': '<id>'},
                           related_view='v1.ticket_list',
                           related_view_kwargs={'ticket_tag_id': '<id>'},
                           schema='TicketSchema',
                           many=True,
                           type_='ticket')
    event = Relationship(attribute='event',
                         self_view='v1.ticket_tag_event',
                         self_view_kwargs={'id': '<id>'},
                         related_view='v1.event_detail',
                         related_view_kwargs={'ticket_tag_id': '<id>'},
                         schema='EventSchema',
                         type_='event')
