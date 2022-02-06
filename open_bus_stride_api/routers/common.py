import pydantic
import sqlalchemy

from open_bus_stride_db.db import get_session


def get_list(*args, convert_to_dict=None, **kwargs):
    if convert_to_dict is None:
        return [obj.__dict__ for obj in get_list_query(*args, **kwargs)]
    else:
        return [convert_to_dict(obj) for obj in get_list_query(*args, **kwargs)]


def get_list_query(db_model, limit, offset, filters=None, max_limit=1000,
                   order_by=None, allowed_order_by_fields=None,
                   post_session_query_hook=None):
    if filters is None:
        filters = []
    with get_session() as session:
        session_query = session.query(db_model)
        if post_session_query_hook:
            session_query = post_session_query_hook(session_query)
        for filter in filters:
            session_query = globals()['get_list_query_filter_{}'.format(filter['type'])](session_query, filters, filter)
        if order_by:
            order_by_args = []
            for ob in order_by.split(','):
                ob = ob.strip()
                if not ob:
                    continue
                ob = ob.split()
                if len(ob) == 1:
                    field_name = ob[0]
                    direction = None
                else:
                    field_name, direction = ob
                assert not allowed_order_by_fields or field_name in allowed_order_by_fields, 'field name is not in allowed order_by fields: {}'.format(field_name)
                order_by_args.append((sqlalchemy.desc if direction == 'desc' else sqlalchemy.asc)(getattr(db_model, field_name)))
            session_query = session_query.order_by(*order_by_args)
        if not limit and max_limit:
            limit = max_limit
        if limit:
            session_query = session_query.limit(limit)
        if offset:
            session_query = session_query.offset(offset)
        return session_query


def get_list_query_filter_equals(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'] == filter['value'])
    return session_query


def get_list_query_filter_in(session_query, filters, filter):
    value = filter['value']
    if value is not None:
        if isinstance(value, str):
            value = value.split(',')
        if len(value) > 0:
            assert len(value) <= 1000, 'too many items in list, maximum allowed is 1000 items'
            session_query = session_query.filter(filter['field'].in_(value))
    return session_query


def get_list_query_filter_datetime_from(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'] >= filter['value'])
    return session_query


def get_list_query_filter_datetime_to(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'] <= filter['value'])
    return session_query


def get_list_query_filter_prefix(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'].like('{}%'.format(filter['value'])))
    return session_query


def get_list_query_filter_contains(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'].like('%{}%'.format(filter['value'])))
    return session_query


def get_list_query_filter_date_in_range(session_query, filters, filter):
    if filter['value'] is not None:
        min_field, max_field = filter['fields']
        session_query = session_query.filter(filter['value'] >= min_field, filter['value'] <= max_field)
    return session_query


def get_item(db_model, field, value):
    with get_session() as session:
        return session.query(db_model).filter(field == value).one().__dict__


class PydanticRelatedModel():

    def __init__(self, field_name_prefix, pydantic_model, exclude_field_names=None):
        self.field_name_prefix = field_name_prefix
        self.pydantic_model = pydantic_model
        self.exclude_field_names = exclude_field_names

    def update_create_model_kwargs(self, kwargs):
        for name, field in self.pydantic_model.__fields__.items():
            if self.exclude_field_names and name in self.exclude_field_names:
                continue
            default = field.default
            if default is ...:
                default = None
            kwargs['{}{}'.format(self.field_name_prefix, name)] = (field.type_, default)

    def add_orm_obj_to_dict_res(self, orm_obj, res):
        if orm_obj:
            for name in self.pydantic_model.__fields__.keys():
                if self.exclude_field_names and name in self.exclude_field_names:
                    continue
                res['{}{}'.format(self.field_name_prefix, name)] = getattr(orm_obj, name)


def pydantic_create_model_with_related(model_name, base_model, *related_models):
    kwargs = {}
    for name, field in base_model.__fields__.items():
        kwargs[name] = (field.type_, field.default)
    for related_model in related_models:
        related_model.update_create_model_kwargs(kwargs)
    return pydantic.create_model(model_name, **kwargs)
