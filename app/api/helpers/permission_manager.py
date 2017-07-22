from flask import current_app as app
from flask_jwt import _jwt_required, current_identity
from app.api.helpers.errors import ForbiddenError, NotFoundError
from app.api.helpers.permissions import jwt_required
from sqlalchemy.orm.exc import NoResultFound
from flask import request

from app.models.event import Event


@jwt_required
def auth_required(view, view_args, view_kwargs, *args, **kwargs):
    return view(*view_args, **view_kwargs)


@jwt_required
def is_super_admin(view, view_args, view_kwargs, *args, **kwargs):
    """
    Permission function for things allowed exclusively to super admin.
    Do not use this if the resource is also accessible by a normal admin, use the is_admin decorator instead.
    :return:
    """
    user = current_identity
    if not user.is_super_admin:
        return ForbiddenError({'source': ''}, 'Super admin access is required').respond()
    return view(*view_args, **view_kwargs)


@jwt_required
def is_admin(view, view_args, view_kwargs, *args, **kwargs):

    user = current_identity
    if not user.is_admin and not user.is_super_admin:
        return ForbiddenError({'source': ''}, 'Admin access is required').respond()

    return view(*view_args, **view_kwargs)


@jwt_required
def is_organizer(view, view_args, view_kwargs, *args, **kwargs):
    user = current_identity

    if user.is_staff:
        return view(*view_args, **view_kwargs)

    if not user.is_organizer(kwargs['event_id']):
        return ForbiddenError({'source': ''}, 'Organizer access is required').respond()

    return view(*view_args, **view_kwargs)


@jwt_required
def is_coorganizer(view, view_args, view_kwargs, *args, **kwargs):
    user = current_identity

    if user.is_staff:
        return view(*view_args, **view_kwargs)

    if user.is_organizer(kwargs['event_id']) or user.is_coorganizer(kwargs['event_id']):
        return view(*view_args, **view_kwargs)

    return ForbiddenError({'source': ''}, 'Co-organizer access is required.').respond()


def is_coorganizer_without_jwt_required(view, view_args, view_kwargs, *args, **kwargs):
    if 'Authorization' in request.headers:
        _jwt_required(app.config['JWT_DEFAULT_REALM'])
        user = current_identity

        if user.is_staff:
            return view(*view_args, **view_kwargs)

        if user.is_organizer(kwargs['event_id']) or user.is_coorganizer(kwargs['event_id']):
            return view(*view_args, **view_kwargs)

    return ForbiddenError({'source': ''}, 'Co-organizer access is required.').respond()


@jwt_required
def is_user_itself(view, view_args, view_kwargs, *args, **kwargs):
    """
    Allows admin and super admin access to any resource irrespective of id.
    Otherwise the user can only access his/her resource.
    """
    user = current_identity
    if not user.is_admin and not user.is_super_admin and user.id != kwargs['id']:
        return ForbiddenError({'source': ''}, 'Access Forbidden').respond()
    return view(*view_args, **view_kwargs)


@jwt_required
def is_coorganizer_or_user_itself(view, view_args, view_kwargs, *args, **kwargs):
    """
    Allows admin and super admin access to any resource irrespective of id.
    Otherwise the user can only access his/her resource.
    """
    user = current_identity
    if user.is_admin or user.is_super_admin or user.id == kwargs['user_id']:
        return view(*view_args, **view_kwargs)

    if user.is_staff:
        return view(*view_args, **view_kwargs)

    if user.is_organizer(kwargs['event_id']) or user.is_coorganizer(kwargs['event_id']):
        return view(*view_args, **view_kwargs)

    return ForbiddenError({'source': ''}, 'Co-organizer access is required.').respond()


@jwt_required
def is_registrar(view, view_args, view_kwargs, *args, **kwargs):
    """
    Allows Organizer, Co-organizer and registrar to access the event resources.x`
    """
    user = current_identity
    event_id = kwargs['event_id']

    if user.is_staff:
        return view(*view_args, **view_kwargs)
    if user.is_registrar(event_id) or user.is_organizer(event_id) or user.is_coorganizer(event_id):
        return view(*view_args, **view_kwargs)
    return ForbiddenError({'source': ''}, 'Registrar Access is Required.').respond()


@jwt_required
def is_track_organizer(view, view_args, view_kwargs, *args, **kwargs):
    """
    Allows Organizer, Co-organizer and Track Organizer to access the resource(s).
    """
    user = current_identity
    event_id = kwargs['event_id']

    if user.is_staff:
        return view(*view_args, **view_kwargs)
    if user.is_track_organizer(event_id) or user.is_organizer(event_id) or user.is_coorganizer(event_id):
        return view(*view_args, **view_kwargs)
    return ForbiddenError({'source': ''}, 'Track Organizer access is Required.').respond()


@jwt_required
def is_moderator(view, view_args, view_kwargs, *args, **kwargs):
    """
    Allows Organizer, Co-organizer and Moderator to access the resource(s).
    """
    user = current_identity
    event_id = kwargs['event_id']
    if user.is_staff:
        return view(*view_args, **view_kwargs)
    if user.is_moderator(event_id) or user.is_organizer(event_id) or user.is_coorganizer(event_id):
        return view_kwargs(*view_args, **view_kwargs)
    return ForbiddenError({'source': ''}, 'Moderator Access is Required.').respond()


@jwt_required
def user_event(view, view_args, view_kwargs, *args, **kwargs):
    user = current_identity
    view_kwargs['user_id'] = user.id
    return view(*view_args, **view_kwargs)


def accessible_role_based_events(view, view_args, view_kwargs, *args, **kwargs):
    if 'POST' in request.method or 'withRole' in request.args:
        _jwt_required(app.config['JWT_DEFAULT_REALM'])
        user = current_identity

        if 'GET' in request.method and user.is_staff:
            return view(*view_args, **view_kwargs)
        view_kwargs['user_id'] = user.id

    return view(*view_args, **view_kwargs)


def create_event(view, view_args, view_kwargs, *args, **kwargs):
    if 'POST' in request.method or 'withRole' in request.args:
        _jwt_required(app.config['JWT_DEFAULT_REALM'])
        user = current_identity

        if user.can_create_event is False:
            return ForbiddenError({'source': ''}, 'Please verify your email').respond()

        if 'GET' in request.method and user.is_staff:
            return view(*view_args, **view_kwargs)
        view_kwargs['user_id'] = user.id

    return view(*view_args, **view_kwargs)


permissions = {
    'is_super_admin': is_super_admin,
    'is_admin': is_admin,
    'is_organizer': is_organizer,
    'is_coorganizer': is_coorganizer,
    'is_track_organizer': is_track_organizer,
    'is_registrar': is_registrar,
    'is_moderator': is_moderator,
    'user_event': user_event,
    'accessible_role_based_events': accessible_role_based_events,
    'auth_required': auth_required,
    'is_coorganizer_or_user_itself': is_coorganizer_or_user_itself,
    'create_event': create_event,
    'is_user_itself': is_user_itself,
    'is_coorganizer_without_jwt_required': is_coorganizer_without_jwt_required
}


def is_multiple(data):
    if type(data) is list:
        return True
    if type(data) is str:
        if data.find(",") > 0:
            return True
    return False


def permission_manager(view, view_args, view_kwargs, *args, **kwargs):
    """The function use to check permissions

    :param callable view: the view
    :param list view_args: view args
    :param dict view_kwargs: view kwargs
    :param list args: decorator args
    :param dict kwargs: decorator kwargs
    """
    methods = 'GET,POST,DELETE,PATCH'

    if 'id' in kwargs:
        view_kwargs['id'] = kwargs['id']

    if 'methods' in kwargs:
        methods = kwargs['methods']

    if request.method not in methods:
        return view(*view_args, **view_kwargs)

    # leave_if checks if we have to bypass this request on the basis of lambda function
    if 'leave_if' in kwargs:
        check = kwargs['leave_if']
        if check(view_kwargs):
            return view(*view_args, **view_kwargs)

    # A check to ensure it is good to go ahead and check permissions
    if 'check' in kwargs:
        check = kwargs['check']
        if not check(view_kwargs):
            return ForbiddenError({'source': ''}, 'Access forbidden').respond()

    # If event_identifier in route instead of event_id
    if 'event_identifier' in view_kwargs:
        try:
            event = Event.query.filter_by(identifier=view_kwargs['event_identifier']).one()
        except NoResultFound, e:
            return NotFoundError({'parameter': 'event_identifier'}, 'Event not found.').respond()
        view_kwargs['event_id'] = event.id

    if 'fetch' in kwargs:
        fetched = None
        if is_multiple(kwargs['fetch']):
            kwargs['fetch'] = [f.strip() for f in kwargs['fetch'].split(",")]
            for f in kwargs['fetch']:
               if f in view_kwargs:
                    fetched = view_kwargs.get(f)
                    break
        elif kwargs['fetch'] in view_kwargs:
            fetched = view_kwargs[kwargs['fetch']]
        if not fetched:
            model = kwargs['model']
            fetch = kwargs['fetch']
            fetch_as = kwargs['fetch_as']
            fetch_key_url = 'id'
            fetch_key_model = 'id'
            if 'fetch_key_url' in kwargs:
                fetch_key_url = kwargs['fetch_key_url']

            if 'fetch_key_model' in kwargs:
                fetch_key_model = kwargs['fetch_key_model']

            if not is_multiple(model):
                model = [model]

            if is_multiple(fetch_key_url):
                fetch_key_url = fetch_key_url.split(",")

            found = False
            for index, mod in enumerate(model):
                if is_multiple(fetch_key_url):
                    f_url = fetch_key_url[index].strip()
                else:
                    f_url = fetch_key_url
                if not view_kwargs.get(f_url):
                    continue
                try:
                    data = mod.query.filter(getattr(mod, fetch_key_model) == view_kwargs[f_url]).one()
                except NoResultFound, e:
                    pass
                else:
                    found = True
                    break

            if not found:
                return NotFoundError({'source': ''}, 'Object not found.').respond()

            fetched = None
            if is_multiple(fetch):
                for f in fetch:
                    if hasattr(data, f):
                        fetched = getattr(data, f)
                        break
            else:
                fetched = getattr(data, fetch) if hasattr(data, fetch) else None

        if fetched:
            kwargs[kwargs['fetch_as']] = fetched
        else:
            return NotFoundError({'source': ''}, 'Object not found.').respond()

    if args[0] in permissions:
        return permissions[args[0]](view, view_args, view_kwargs, *args, **kwargs)
    else:
        return ForbiddenError({'source': ''}, 'Access forbidden').respond()


def has_access(access_level, **kwargs):
    if access_level in permissions:
        auth = permissions[access_level](lambda *a, **b: True, (), {}, (), **kwargs)
        if type(auth) is bool and auth is True:
            return True
    return False
