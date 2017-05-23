from flask import current_app as app
from flask_rest_jsonapi import Api, ResourceDetail, ResourceList, ResourceRelationship
from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields
from app.models import db
from app.models.user import User


class UserSchema(Schema):
    class Meta:
        type = 'user'
        self_view = 'user'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'user_list'

    id = fields.Int(dump_only=True)
    email = fields.Str()
    avatar = fields.Str()
    is_super_admin = fields.Email()
    is_admin = fields.Boolean()
    is_verified = fields.Boolean()
    signup_at = fields.DateTime()
    last_accessed_at = fields.DateTime()
    user_detail = Relationship(self_view='user_user_detail',
                               self_view_kwargs={'user_detail_id': '<id>'},
                               related_view='computer_list',
                               related_view_kwargs={'user_detail_id': '<id>'},
                               many=False,
                               schema='UserDetailSchema',
                               type_='user_detail')
    created_at = fields.DateTime()
    deleted_at = fields.DateTime()


class UserDetailSchema(Schema):
    class Meta:
        type = 'user_detail'
        self_view = 'user_user_detail'
        self_view_kwargs = 'id'
        self_view_many = 'user_detail_list'

    id = fields.Int(dump_only=True)
    firstname = fields.Str()
    lastname = fields.Str()
    details = fields.Str()
    avatar = fields.Str()
    contact = fields.Str()
    facebook = fields.Str()
    twitter = fields.Str()
    instagram = fields.Str()
    google = fields.Str()
    avatar_uploaded = fields.Str()
    thumbnail = fields.Str()
    small = fields.Str()
    icon = fields.Str()
    user_id = fields.Int()


class UserList(ResourceList):
    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': User}


class UserDetail(ResourceDetail):
    def before_get_object(self, view_kwargs):
        if view_kwargs.get('user_detail_id') is not None:
            print("lel, this table shouldn't even exist")

    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': User,
                  'methods': {'before_get_object': before_get_object}}


class UserRelationship(ResourceRelationship):
    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': User}


class UserDetailList(ResourceList):
    schema = UserDetailSchema
    data_layer = {'session': db.session,
                  'model': UserDetail}


class UserDetailDetail(ResourceDetail):
    schema = UserDetailSchema
    data_layer = {'session': db.session,
                  'model': UserDetail}


class UserDetailRelationship(ResourceRelationship):
    schema = UserSchema
    data_layer = {'session': db.session,
                  'model': UserDetail}



