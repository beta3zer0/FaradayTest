import json

import flask
from flask import abort, g
from flask_classful import FlaskView
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.inspection import inspect
from sqlalchemy import func
from marshmallow import Schema
from marshmallow.compat import with_metaclass
from marshmallow_sqlalchemy import ModelConverter
from marshmallow_sqlalchemy.schema import ModelSchemaMeta, ModelSchemaOpts
from webargs.flaskparser import FlaskParser, parser, abort
from webargs.core import ValidationError
from server.models import Workspace, db
import server.utils.logger

logger = server.utils.logger.get_logger(__name__)


def output_json(data, code, headers=None):
    content_type = 'application/json'
    dumped = json.dumps(data)
    if headers:
        headers.update({'Content-Type': content_type})
    else:
        headers = {'Content-Type': content_type}
    response = flask.make_response(dumped, code, headers)
    return response


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


# TODO: Require @view decorator to enable custom routes
class GenericView(FlaskView):
    """Abstract class to provide helpers. Inspired in `Django REST
    Framework generic viewsets`_.

    To create new views, you should create a class inheriting from
    GenericView (or from one of its subclasses) and set the model_class,
    schema_class, and optionally the rest of class attributes.

    .. _Django REST Framework generic viewsets: http://www.django-rest-framework.org/api-guide/viewsets/#genericviewset
    """

    # Must-implement attributes

    #: **Required**. The class of the SQLAlchemy model this view will handle
    model_class = None

    #: **Required** (unless _get_schema_class is overwritten).
    #: A subclass of `marshmallow.Schema` to serialize and deserialize the
    #: data provided by the user
    schema_class = None

    # Default attributes

    #: The prefix where the endpoint should be registered.
    #: This is useful for API versioning
    route_prefix = '/v2/'

    #: Arguments that are passed to the view but shouldn't change the route
    #: rule. This should be used when route_prefix is parametrized
    #:
    #: You tipically won't need this, unless you're creating nested views.
    #: For example GenericWorkspacedView use this so the workspace name is
    #: prepended to the view URL
    base_args = []

    #: Decides how you want to format the output response. It is set to dump a
    #: JSON object by default.
    #: See http://flask-classful.teracy.org/#adding-resource-representations-get-real-classy-and-put-on-a-top-hat
    #: for more information
    representations = {
        'application/json': output_json,
        'flask-classful/default': output_json,
    }

    ""
    #: Name of the field of the model used to get the object instance in
    #: retrieve, update and delete endpoints.
    #:
    #: For example, if you have a `Tag` model, maybe a `slug` would be good
    #: lookup field.
    #:
    #: .. note::
    #:     You have to use a unique field here instead of one allowing
    #:     duplicate values
    lookup_field = 'id'

    #: A function that converts the string paremeter passed in the URL to the
    #: value that will be queried in the database.
    #: It defaults to int to match the type of the default lookup_field_type
    #: (id)
    lookup_field_type = int

    # List of field names that the _validate_uniqueness method will use
    # to detect duplicate object creation/update
    unique_fields = []  # Fields unique

    def _get_schema_class(self):
        """Documentame"""
        assert self.schema_class is not None, "You must define schema_class"
        return self.schema_class

    def _get_lookup_field(self):
        return getattr(self.model_class, self.lookup_field)

    def _validate_object_id(self, object_id):
        try:
            self.lookup_field_type(object_id)
        except ValueError:
            flask.abort(404, 'Invalid format of lookup field')

    def _get_base_query(self):
        return self.model_class.query

    def _filter_query(self, query):
        """Return a new SQLAlchemy query with some filters applied"""
        return query

    def _get_object(self, object_id, **kwargs):
        self._validate_object_id(object_id)
        try:
            obj = self._get_base_query(**kwargs).filter(
                self._get_lookup_field() == object_id).one()
        except NoResultFound:
            flask.abort(404, 'Object with id "%s" not found' % object_id)
        return obj

    def _dump(self, obj, **kwargs):
        return self._get_schema_class()(**kwargs).dump(obj).data

    def _parse_data(self, schema, request, *args, **kwargs):
        return FlaskParser().parse(schema, request, locations=('json',),
                                   *args, **kwargs)

    def _validate_uniqueness(self, obj, object_id=None):
        # TODO: Implement this
        return True

    @classmethod
    def register(cls, app, *args, **kwargs):
        """Register and add JSON error handler. Use error code
        400 instead of 422"""
        super(GenericView, cls).register(app, *args, **kwargs)
        @app.errorhandler(422)
        def handle_unprocessable_entity(err):
            # webargs attaches additional metadata to the `data` attribute
            exc = getattr(err, 'exc')
            if exc:
                # Get validations from the ValidationError object
                messages = exc.messages
            else:
                messages = ['Invalid request']
            return flask.jsonify({
                'messages': messages,
            }), 400

        @app.errorhandler(InvalidUsage)
        def handle_invalid_usage(error):
            response = flask.jsonify(error.to_dict())
            response.status_code = error.status_code
            return response


class GenericWorkspacedView(GenericView):
    """Abstract class for a view that depends on the workspace, that is
    passed in the URL"""

    # Default attributes
    route_prefix = '/v2/ws/<workspace_name>/'
    base_args = ['workspace_name']  # Required to prevent double usage of <workspace_name>
    unique_fields = []  # Fields unique together with workspace_id

    def _get_workspace(self, workspace_name):
        try:
            ws = Workspace.query.filter_by(name=workspace_name).one()
        except NoResultFound:
            flask.abort(404, "No such workspace: %s" % workspace_name)
        return ws

    def _get_base_query(self, workspace_name):
        base = super(GenericWorkspacedView, self)._get_base_query()
        return base.join(Workspace).filter(
            Workspace.id==self._get_workspace(workspace_name).id)

    def _get_object(self, object_id, workspace_name):
        self._validate_object_id(object_id)
        try:
            obj = self._get_base_query(workspace_name).filter(
                self._get_lookup_field() == object_id).one()
        except NoResultFound:
            flask.abort(404, 'Object with id "%s" not found' % object_id)
        return obj

    def _validate_uniqueness(self, obj, object_id=None):
        # TODO: Use implementation of GenericView
        assert obj.workspace is not None, "Object must have a " \
            "workspace attribute set to call _validate_uniqueness"
        primary_key_field = inspect(self.model_class).primary_key[0]
        for field_name in self.unique_fields:
            field = getattr(self.model_class, field_name)
            value = getattr(obj, field_name)
            query = self._get_base_query(obj.workspace.name).filter(
                field==value)
            if object_id is not None:
                # The object already exists in DB, we want to fetch an object
                # different to this one but with the same unique field
                query = query.filter(primary_key_field != object_id)
            if query.one_or_none():
                db.session.rollback()
                abort(422, ValidationError('Existing value for %s field: %s' % (
                    field_name, value
                )))


class ListMixin(object):
    """Add GET / route"""

    def _envelope_list(self, objects, pagination_metadata=None):
        """Override this method to define how a list of objects is
        rendered"""
        return objects

    def _paginate(self, query):
        return query, None

    def index(self, **kwargs):
        query = self._filter_query(self._get_base_query(**kwargs))
        objects, pagination_metadata = self._paginate(query)
        return self._envelope_list(self._dump(objects, many=True),
                                   pagination_metadata)


class PaginatedMixin(object):
    """Add pagination for list route"""
    per_page_parameter_name = 'page_size'
    page_number_parameter_name = 'page'

    def _paginate(self, query):
        if self.per_page_parameter_name in flask.request.args:

            try:
                page = int(flask.request.args.get(
                    self.page_number_parameter_name, 1))
            except (TypeError, ValueError):
                flask.abort(404, 'Invalid page number')

            try:
                per_page = int(flask.request.args[
                    self.per_page_parameter_name])
            except (TypeError, ValueError):
                flask.abort(404, 'Invalid per_page value')

            pagination_metadata = query.paginate(page=page, per_page=per_page, error_out=False)
            return pagination_metadata.items, pagination_metadata
        return super(PaginatedMixin, self)._paginate(query)


class FilterAlchemyMixin(object):
    """Add querystring parameter filtering to list route

    It is done by setting the ViewClass.filterset_class class
    attribute
    """

    filterset_class = None

    def _filter_query(self, query):
        assert self.filterset_class is not None, 'You must define a filterset'
        return self.filterset_class(query).filter()


class ListWorkspacedMixin(ListMixin):
    """Add GET /<workspace_name>/ route"""
    # There are no differences with the non-workspaced implementations. The code
    # inside the view generic methods is enough
    pass


class RetrieveMixin(object):
    """Add GET /<id>/ route"""

    def get(self, object_id, **kwargs):
        return self._dump(self._get_object(object_id, **kwargs))


class RetrieveWorkspacedMixin(RetrieveMixin):
    """Add GET /<workspace_name>/<id>/ route"""
    # There are no differences with the non-workspaced implementations. The code
    # inside the view generic methods is enough
    pass


class ReadOnlyView(ListMixin,
                   RetrieveMixin,
                   GenericView):
    """A generic view with list and retrieve endpoints"""
    pass


class ReadOnlyWorkspacedView(ListWorkspacedMixin,
                             RetrieveWorkspacedMixin,
                             GenericWorkspacedView):
    """A workspaced generic view with list and retrieve endpoints"""
    pass


class CreateMixin(object):
    """Add POST / route"""

    def post(self, **kwargs):
        data = self._parse_data(self._get_schema_class()(strict=True),
                                flask.request)
        created = self._perform_create(data, **kwargs)
        created.creator = g.user
        db.session.commit()
        return self._dump(created), 201

    def _perform_create(self, data, **kwargs):
        obj = self.model_class(**data)
        # assert not db.session.new
        with db.session.no_autoflush:
            # Required because _validate_uniqueness does a select. Doing this
            # outside a no_autoflush block would result in a premature create.
            self._validate_uniqueness(obj)
            db.session.add(obj)
        return obj


class CreateWorkspacedMixin(CreateMixin):
    """Add POST /<workspace_name>/ route"""

    def _perform_create(self, data, workspace_name):
        assert not db.session.new
        workspace = self._get_workspace(workspace_name)
        obj = self.model_class(**data)
        obj.workspace = workspace
        # assert not db.session.new
        with db.session.no_autoflush:
            # Required because _validate_uniqueness does a select. Doing this
            # outside a no_autoflush block would result in a premature create.
            self._validate_uniqueness(obj)
            db.session.add(obj)
        db.session.commit()

        return obj


class UpdateMixin(object):
    """Add PUT /<workspace_name>/<id>/ route"""

    def put(self, object_id, **kwargs):
        data = self._parse_data(self._get_schema_class()(strict=True),
                                flask.request)
        obj = self._get_object(object_id, **kwargs)
        self._update_object(obj, data)
        updated = self._perform_update(object_id, obj, **kwargs)
        return self._dump(obj), 200

    def _update_object(self, obj, data):
        for (key, value) in data.items():
            setattr(obj, key, value)

    def _perform_update(self, object_id, obj):
        with db.session.no_autoflush:
            self._validate_uniqueness(obj, object_id)
        db.session.add(obj)
        db.session.commit()


class UpdateWorkspacedMixin(UpdateMixin):
    """Add PUT /<id>/ route"""

    def _perform_update(self, object_id, obj, workspace_name):
        assert not db.session.new
        with db.session.no_autoflush:
            obj.workspace = self._get_workspace(workspace_name)
        return super(UpdateWorkspacedMixin, self)._perform_update(
            object_id, obj)


class DeleteMixin(object):
    """Add DELETE /<id>/ route"""
    def delete(self, object_id, **kwargs):
        obj = self._get_object(object_id, **kwargs)
        self._perform_delete(obj)
        return None, 204

    def _perform_delete(self, obj):
        db.session.delete(obj)
        db.session.commit()


class DeleteWorkspacedMixin(DeleteMixin):
    """Add DELETE /<workspace_name>/<id>/ route"""
    pass


class CountWorkspacedMixin(object):

    def count(self, **kwargs):
        res = {
            'groups': [],
            'total_count': 0
        }
        group_by = flask.request.args.get('group_by', None)
        # TODO migration: whitelist fields to avoid leaking a confidential
        # field's value.
        # Example: /users/count/?group_by=password
        if not group_by or group_by not in inspect(self.model_class).attrs:
            abort(404)

        workspace_name = kwargs.pop('workspace_name')
        # using format is not a great practice.
        # the user input is group_by, however it's filtered by column name.
        table_name = inspect(self.model_class).tables[0].name
        group_by = '{0}.{1}'.format(table_name, group_by)

        count = self._filter_query(
            db.session.query(self.model_class)
            .join(Workspace)
            .group_by(group_by)
            .filter(Workspace.name == workspace_name))
        for key, count in count.values(group_by, func.count(group_by)):
            res['groups'].append(
                {'count': count,
                 'name': key,
                 # To add compatibility with the web ui
                 flask.request.args.get('group_by'): key,
                 }
            )
            res['total_count'] += count
        return res


class ReadWriteView(CreateMixin,
                    UpdateMixin,
                    DeleteMixin,
                    ReadOnlyView):
    """A generic view with list, retrieve and create endpoints"""
    pass


class ReadWriteWorkspacedView(CreateWorkspacedMixin,
                              UpdateWorkspacedMixin,
                              DeleteWorkspacedMixin,
                              CountWorkspacedMixin,
                              ReadOnlyWorkspacedView):
    """A generic workspaced view with list, retrieve and create
    endpoints"""
    pass


class AutoSchema(with_metaclass(ModelSchemaMeta, Schema)):
    """
    A Marshmallow schema that does field introspection based on
    the SQLAlchemy model specified in Meta.model.
    Unlike the marshmallow_sqlalchemy ModelSchema, it doesn't change
    the serialization and deserialization proccess.
    """
    OPTIONS_CLASS = ModelSchemaOpts


class FilterAlchemyModelConverter(ModelConverter):
    """Use this to make all fields of a model not required.

    It is used to make filteralchemy support not nullable columns"""

    def _add_column_kwargs(self, kwargs, column):
        super(FilterAlchemyModelConverter, self)._add_column_kwargs(kwargs,
                                                                    column)
        kwargs['required'] = False


class FilterSetMeta:
    """Base Meta class of FilterSet objects"""
    parser = parser
    converter = FilterAlchemyModelConverter()