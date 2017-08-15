from marshmallow import validates_schema, validate
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Schema, Relationship

from app.api.helpers.exceptions import UnprocessableEntity
from app.api.helpers.utilities import dasherize
from app.models.discount_code import DiscountCode


class DiscountCodeSchemaPublic(Schema):
    """
    API Schema for discount_code Model
    For endpoints which allow somebody other than co-organizer/admin to access the resource.
    """

    class Meta:
        type_ = 'discount-code'
        self_view = 'v1.discount_code_detail'
        self_view_kwargs = {'id': '<id>'}
        inflect = dasherize

    id = fields.Integer()
    code = fields.Str(required=True)
    discount_url = fields.Url(allow_none=True)
    value = fields.Float(required=True)
    type = fields.Str(validate=validate.OneOf(choices=["amount", "percent"]), required=True)
    is_active = fields.Boolean()
    event = Relationship(attribute='event',
                         self_view='v1.discount_code_event',
                         self_view_kwargs={'id': '<id>'},
                         related_view='v1.event_detail',
                         related_view_kwargs={'discount_code_id': '<id>'},
                         schema='EventSchema',
                         type_='event')


class DiscountCodeSchemaEvent(DiscountCodeSchemaPublic):
    """
    API Schema for discount_code Model
    """

    class Meta:
        type_ = 'discount-code'
        self_view = 'v1.discount_code_detail'
        self_view_kwargs = {'id': '<id>'}
        inflect = dasherize

    @validates_schema(pass_original=True)
    def validate_quantity(self, data, original_data):
        if 'id' in original_data['data']:
            discount_code = DiscountCode.query.filter_by(id=original_data['data']['id']).one()
            if 'min_quantity' not in data:
                data['min_quantity'] = discount_code.min_quantity

            if 'max_quantity' not in data:
                data['max_quantity'] = discount_code.max_quantity

            if 'tickets_number' not in data:
                data['tickets_number'] = discount_code.tickets_number

        if 'min_quantity' in data and 'max_quantity' in data:
            if data['min_quantity'] >= data['max_quantity']:
                raise UnprocessableEntity({'pointer': '/data/attributes/min-quantity'},
                                          "min-quantity should be less than max-quantity")

        if 'tickets_number' in data and 'max_quantity' in data:
            if data['tickets_number'] < data['max_quantity']:
                raise UnprocessableEntity({'pointer': '/data/attributes/tickets-number'},
                                          "tickets-number should be greater than max-quantity")

    tickets_number = fields.Integer(validate=lambda n: n >= 0, allow_none=True)
    min_quantity = fields.Integer(validate=lambda n: n >= 0, allow_none=True)
    max_quantity = fields.Integer(validate=lambda n: n >= 0, allow_none=True)
    valid_from = fields.DateTime(allow_none=True)
    valid_till = fields.DateTime(allow_none=True)
    tickets = fields.Str(validate=validate.OneOf(choices=["event", "ticket"]), allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    used_for = fields.Str(required=True)


class DiscountCodeSchemaTicket(DiscountCodeSchemaEvent):
    """
    API Schema for discount_code Model
    """

    class Meta:
        type_ = 'discount-code'
        self_view = 'v1.discount_code_detail'
        self_view_kwargs = {'id': '<id>'}
        inflect = dasherize

    @validates_schema(pass_original=True)
    def validate_quantity(self, data, original_data):
        if 'id' in original_data['data']:
            discount_code = DiscountCode.query.filter_by(id=original_data['data']['id']).one()
            if 'min_quantity' not in data:
                data['min_quantity'] = discount_code.min_quantity

            if 'max_quantity' not in data:
                data['max_quantity'] = discount_code.max_quantity

            if 'tickets_number' not in data:
                data['tickets_number'] = discount_code.tickets_number

        if 'min_quantity' in data and 'max_quantity' in data:
            if data['min_quantity'] >= data['max_quantity']:
                raise UnprocessableEntity({'pointer': '/data/attributes/min-quantity'},
                                          "min-quantity should be less than max-quantity")

        if 'tickets_number' in data and 'max_quantity' in data:
            if data['tickets_number'] < data['max_quantity']:
                raise UnprocessableEntity({'pointer': '/data/attributes/tickets-number'},
                                          "tickets-number should be greater than max-quantity")

    marketer = Relationship(attribute='user',
                            self_view='v1.discount_code_user',
                            self_view_kwargs={'id': '<id>'},
                            related_view='v1.user_detail',
                            related_view_kwargs={'discount_code_id': '<id>'},
                            schema='UserSchemaPublic',
                            type_='user')



