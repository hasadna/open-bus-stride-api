import os
import json
import typing
import inspect
import itertools

import fastapi
import pydantic
import sqlalchemy
import sqlalchemy.orm

from open_bus_stride_db.db import _sessionmaker, get_session


DEFAULT_LIMIT = 100
MAX_LIMIT = 500000
QUERY_PAGE_SIZE = 1000
DEBUG = bool(os.environ.get('DEBUG'))


FILTER_DOCS = {
    "list": 'Filter by {what_singular}. Comma-separated list of values.',
    "prefix": 'Filter by {what_singular} prefix. Only return items which start with given string.',
    "equals": 'Filter by {what_singular}. Only return items which exactly match given string.',
    "contains": 'Filter by {what_singular}. Only return items which contain given string.',
    "datetime_from": 'Filter by {what_singular}. Only return items which have date/time after or equals to given value. Format: "YYYY-MM-DDTHH:MM:SS+Z", e.g. "2021-11-03T15:48:49+02:00". '
                     'Note that all date/times must have a timezone specification.',
    "datetime_to": 'Filter by {what_singular}. Only return items which have date/time before or equals to given value. Format: "YYYY-MM-DDTHH:MM:SS+Z", e.g. "2021-11-03T15:48:49+02:00". '
        'Note that all date/times must have a timezone specification.',
    "date_from": 'Filter by {what_singular}. Only return items which have a date after or equals to given value. Format: "YYYY-MM-DD", e.g. "2021-11-03".',
    "date_to": 'Filter by {what_singular}. Only return items which have a date before or equals to given value. Format: "YYYY-MM-DD", e.g. "2021-11-03".',
    "hour_from": 'Filter by {what_singular}. Only return items which have an hour date after or equals to given value. Format: 0(12AM)-23',
    "hour_to": 'Filter by {what_singular}. Only return items which have a date before or equals to given value. Format: 0(12AM)-23',
    "greater_or_equal": 'Filter by {what_singular}. Only return items which have a numeric value greater than or equal to given value',
    "lower_or_equal": 'Filter by {what_singular}. Only return items which have a numeric value lower than or equal to given value',
}


def debug_print(*args):
    if DEBUG:
        print(*args)


def post_process_response_obj(obj, convert_to_dict):
    if convert_to_dict is None:
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return obj._asdict()
    else:
        return convert_to_dict(obj)


def streaming_response_iterator(session, first_items, q_iterator, convert_to_dict):
    try:
        yield b"["
        for i, obj in enumerate(itertools.chain(first_items, q_iterator)):
            item = post_process_response_obj(obj, convert_to_dict)
            item = fastapi.encoders.jsonable_encoder(item)
            if i > 0:
                yield b","
            yield json.dumps(item).encode()
            if i == 0:
                debug_print(f'yielded first item: {item}')
            if i + 1 >= MAX_LIMIT:
                raise Exception("Too many results, please limit the query")
        yield b"]"
    finally:
        session.close()


def get_list(*args, convert_to_dict=None, **kwargs):
    debug_print(f'start get_list {args}')
    session = _sessionmaker()
    try:
        q = get_list_query(session, *args, **kwargs)
        if kwargs.get('get_count'):
            debug_print(f'Getting count for query {q}')
            q_count = q.count()
            session.close()
            return fastapi.Response(content=str(q_count), media_type="application/json")
        else:
            debug_print(f'Getting results for query: {q}')
            data = [post_process_response_obj(obj, convert_to_dict) for obj in q]
            session.close()
            return data
            # if not hasattr(q, '__q_limit') or not q.__q_limit or q.__q_limit > QUERY_PAGE_SIZE:
            #     debug_print(f'adding yield_per({QUERY_PAGE_SIZE}) to query')
            #     q = q.yield_per(QUERY_PAGE_SIZE)
            # q_iterator = (obj for obj in q)
            # first_items = list(itertools.islice(q_iterator, QUERY_PAGE_SIZE + 1))
            # if len(first_items) <= QUERY_PAGE_SIZE:
            #     debug_print(f'got {len(first_items)} items - returning without streaming')
            #     data = [post_process_response_obj(obj, convert_to_dict) for obj in first_items]
            #     session.close()
            #     return data
            # else:
            #     debug_print(f'got {len(first_items)} items - returning using streaming')
            #     return fastapi.responses.StreamingResponse(
            #         streaming_response_iterator(session, first_items, q_iterator, convert_to_dict),
            #         media_type="application/json"
            #     )
    except:
        session.close()
        raise


def get_base_session_query(session, db_model, pydantic_model=...):
    # we have to set select fields for queries otherwise database migrations which add fields
    # cause the api to fail with "no such column" because it tries to select all fields which
    # are defined in stride db model
    assert pydantic_model is not ...
    if pydantic_model is None:
        # This is not recommended, because it relies on db model matching the DB migrations and
        # in some cases they may be mismatched, if migrations failed to run or if api was updated
        # before migrations were applied.
        session_query = session.query(db_model)
    else:
        session_query = session.query(*[
            getattr(db_model, key)
            for key
            in pydantic_model.schema()['properties'].keys()
        ])
    return session_query


def process_list_query_order_by_limit_offset(skip_order_by, order_by, get_count, limit, offset, skip_order_by_id_field=False):
    order_by_args = None
    res_limit = None
    res_offset = None
    if skip_order_by:
        assert not order_by
    else:
        order_by_args = []
        order_by_has_id_field = False
        if order_by:
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
                if field_name.lower() == 'id':
                    order_by_has_id_field = True
                order_by_args.append((('desc' if direction == 'desc' else 'asc'), field_name))
        if not get_count:
            if limit != -1 and not order_by_has_id_field and not skip_order_by_id_field:
                order_by_args.append(('desc', 'id'))
    if limit and limit != -1:
        res_limit = limit
    if offset:
        res_offset = offset
    return order_by_args, res_limit, res_offset


def get_list_query(session, db_model, limit, offset, filters=None, default_limit=DEFAULT_LIMIT,
                   order_by=None, skip_order_by=False, get_count=False,
                   post_session_query_hook=None, pydantic_model=...,
                   get_base_session_query_callback=None):
    debug_print(f'get_list_query: limit={limit}, offset={offset}, order_by={order_by}')
    if get_count:
        limit, offset, default_limit, order_by = None, None, None, None
    elif not limit and default_limit:
        limit = default_limit
    if limit:
        limit = int(limit)
    assert 0 < limit <= 1000, "due to abuse, maximum limit per request is 1000 items, contact us if you need more"
    if filters is None:
        filters = []
    if get_base_session_query_callback is None:
        session_query = get_base_session_query(session, db_model, pydantic_model)
    else:
        session_query = get_base_session_query_callback(session)
    if post_session_query_hook:
        session_query = post_session_query_hook(session_query)
    for filter in filters:
        session_query = globals()['get_list_query_filter_{}'.format(filter['type'])](session_query, filters, filter)
    q_order_by_args, q_limit, q_offset = process_list_query_order_by_limit_offset(skip_order_by, order_by, get_count, limit, offset)
    if q_order_by_args is not None:
        order_by_args = []
        for direction, field_name in q_order_by_args:
            order_by_args.append((sqlalchemy.desc if direction == 'desc' else sqlalchemy.asc)(getattr(db_model, field_name)))
        session_query = session_query.order_by(*order_by_args)
    if q_limit is not None:
        session_query = session_query.limit(q_limit)
    if q_offset is not None:
        session_query = session_query.offset(q_offset)
    session_query.__q_limit = q_limit
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


def get_list_query_filter_greater_or_equal(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'] >= float(filter['value']))
    return session_query


def get_list_query_filter_lower_or_equal(session_query, filters, filter):
    if filter['value'] is not None:
        session_query = session_query.filter(filter['field'] <= float(filter['value']))
    return session_query


def get_item(db_model, field, value, pydantic_model=...):
    with get_session() as session:
        session_query = get_base_session_query(session, db_model, pydantic_model)
        obj = session_query.filter(field == value).one()
        return post_process_response_obj(obj, None)


class PydanticRelatedModel():

    def __init__(self, field_name_prefix, pydantic_model, exclude_field_names=None, include_field_names=None):
        self.field_name_prefix = field_name_prefix
        self.pydantic_model = pydantic_model
        self.exclude_field_names = exclude_field_names
        self.include_field_names = include_field_names

    def update_create_model_kwargs(self, kwargs):
        for name, field in self.pydantic_model.__fields__.items():
            if self.include_field_names and name not in self.include_field_names:
                continue
            if self.exclude_field_names and name in self.exclude_field_names:
                continue
            default = field.default
            if default is ...:
                default = None
            kwargs['{}{}'.format(self.field_name_prefix, name)] = (field.type_, default)

    def add_session_query_entities(self, db_model, session_query):
        for name in self.pydantic_model.__fields__.keys():
            if self.exclude_field_names and name in self.exclude_field_names:
                continue
            session_query = session_query.add_entity(getattr(db_model, name).label('{}{}'.format(self.field_name_prefix, name)))
        return session_query


def pydantic_create_model_with_related(model_name, base_model, *related_models):
    kwargs = {}
    for name, field in base_model.__fields__.items():
        kwargs[name] = (field.type_, field.default)
    for related_model in related_models:
        related_model.update_create_model_kwargs(kwargs)
    return pydantic.create_model(model_name, **kwargs)


def param_limit(default_limit=DEFAULT_LIMIT, as_RouteParam=False):
    if as_RouteParam:
        return RouteParam('limit', int, param_limit(default_limit=default_limit))
    else:
        return fastapi.Query(
            None,
            description=f'Limit the number of returned results. '
                        f'If not specified will limit to {default_limit} results. '
                        f'To get more results, you can either use the offset param, '
                        f'alternatively - set the limit to -1 and use http streaming '
                        f'with compatible json streaming decoder to get all results, '
                        f'this method can fetch up to a maximum of {MAX_LIMIT} results.'
        )


def doc_param(what_singular: str, filter_type: str, description: str = "", example: str = "", default: str = None):
    filter_description = FILTER_DOCS.get(filter_type)
    if filter_description:
        description += "\n\n{0}".format(filter_description.format(what_singular=what_singular))
    if example:
        description += "\n\nExample: {0}".format(example)
    return fastapi.Query(default, description=description)


class DocParam:

    def __init__(self, what_singular: str, filter_type: str, description: str = "", example: str = "", default: str = None):
        self.what_singular = what_singular
        self.filter_type = filter_type
        self.description = description
        self.example = example
        self.default = default

    def get_doc_param(self):
        return doc_param(self.what_singular, self.filter_type, self.description, self.example, self.default)

    def get_with_prefix(self, prefix):
        return DocParam(
            f'{prefix} {self.what_singular}',
            self.filter_type, self.description, self.example, self.default
        )


def param_offset(as_RouteParam=False):
    if as_RouteParam:
        return RouteParam('offset', int, param_offset())
    else:
        return fastapi.Query(None, description='Item number to start returning results from. '
                                               'Use in combination with limit for pagination, '
                                               'alternatively, don\'t set offset, set limit to -1 '
                                               'and use http streaming with compatible json streaming '
                                               f'decoder to get all results up to a maximum of {MAX_LIMIT} results.')


def param_get_count(as_RouteParam=False):
    if as_RouteParam:
        return RouteParam('get_count', bool, param_get_count())
    else:
        return fastapi.Query(False, description='Set to "true" to only get the total number of results for given filters. limit/offset/order parameters will be ignored.')


def param_filter_list(what_singular, example='1,2,3'):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Comma-separated list of values, e.g. "{example}".')


def param_filter_prefix(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular} prefix. Only return items which start with given string.')


def param_filter_equals(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which exactly match given string.')


def param_filter_contains(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which contain given string.')


def param_filter_datetime_from(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which have date/time after or equals to given value. Format: "YYYY-MM-DDTHH:MM:SS+Z", e.g. "2021-11-03T15:48:49+02:00". '
                                           f'Note that all date/times must have a timezone specification.')


def param_filter_datetime_to(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which have date/time before or equals to given value. Format: "YYYY-MM-DDTHH:MM:SS+Z", e.g. "2021-11-03T15:48:49+02:00". '
                                           f'Note that all date/times must have a timezone specification.')


def param_filter_date_from(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which have a date after or equals to given value. Format: "YYYY-MM-DD", e.g. "2021-11-03".')


def param_filter_date_to(what_singular):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which have a date before or equals to given value. Format: "YYYY-MM-DD", e.g. "2021-11-03".')


def param_filter_greater_or_equal(what_singular, example):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which have a numeric value greater than or equal to given value. Example value: {example}')


def param_filter_lower_or_equal(what_singular, example):
    return fastapi.Query(None, description=f'Filter by {what_singular}. Only return items which have a numeric value lower than or equal to given value. Example value: {example}')


def param_order_by(default='id asc', as_RouteParam=False):
    if as_RouteParam:
        return RouteParam('order_by', str, param_order_by(default=default))
    else:
        return fastapi.Query(
            default,
            description=f'Order of the results. Comma-separated list of fields and direction. e.g. "field1 asc,field2 desc".'
        )


def router_list(router, tag, pydantic_model, what_plural):
    return router.get("/list", tags=[tag], response_model=typing.List[pydantic_model], description=f'List of {what_plural}.')


class RouteParam():

    def __init__(self,  name, annotation, param, filter_kwargs=None):
        self.name = name
        self.annotation = annotation
        self.param = param
        self.filter_kwargs = filter_kwargs

    def get_signature_parameter(self):
        return inspect.Parameter(
            self.name,
            inspect.Parameter.KEYWORD_ONLY,
            default=self.param.get_doc_param() if isinstance(self.param, DocParam) else self.param,
            annotation=self.annotation,
        )

    def get_filter(self, kwargs):
        return {**self.filter_kwargs, 'value': kwargs[self.name]}

    def get_with_prefix(self, name_prefix, doc_param_prefix):
        assert isinstance(self.param, DocParam)
        return RouteParam(
            f'{name_prefix}{self.name}', self.annotation,
            self.param.get_with_prefix(doc_param_prefix), self.filter_kwargs
        )


def get_route_params_with_prefix(name_prefix, doc_param_prefix, route_params):
    return [
        route_param.get_with_prefix(name_prefix, doc_param_prefix) for route_param in route_params
    ]


def add_api_router_list(router, tag, pydantic_model, what_plural, route_params, description=None):

    def _decorator(func):
        func.__signature__ = inspect.signature(func).replace(parameters=[
            route_param.get_signature_parameter() for route_param in route_params
        ])
        router.add_api_route(
            "/list", func, tags=[tag], response_model=typing.List[pydantic_model],
            description=description if description else f'List of {what_plural}.'
        )
        return func

    return _decorator


def router_get(router, tag, pydantic_model, what_singular):
    return router.get('/get', tags=[tag], response_model=pydantic_model,
                      description=f'Return a single {what_singular} based on id')


def param_get_id(what_singular):
    return fastapi.Query(..., description=f'{what_singular} id to get')
