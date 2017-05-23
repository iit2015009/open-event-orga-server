from flask import current_app as app, Blueprint
from flask_rest_jsonapi import Api
from app.api.users import UserList, UserDetail, UserRelationship, UserDetailList, UserDetailDetail, UserDetailRelationship

api_v1 = Blueprint('api', __name__, url_prefix='/api/v1')
print('anything')
api = Api(app, api_v1)

api.route(UserList, 'user_list', '/users')
api.route(UserDetail, 'user_detail', '/users/<int:id>')
api.route(UserRelationship, 'user_user_detail', '/users/<int:id>/relationships/user_detail')
api.route(UserDetailList, 'user_detail_list', '/user_detail', '/users/<int:id>/user_detail')
api.route(UserDetailDetail, 'user_detail_detail', '/user_detail/<int:id>')
api.route(UserDetailRelationship, 'user', 'user_detail/<int:id>/relationships/user')

