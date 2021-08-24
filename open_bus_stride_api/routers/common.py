from open_bus_stride_db.db import get_session


def get_list(*args, **kwargs):
    return [obj.__dict__ for obj in get_list_query(*args, **kwargs)]


def get_list_query(db_model, limit, offset, filters, max_limit=1000):
    with get_session() as session:
        session_query = session.query(db_model)
        for filter in filters:
            session_query = globals()['get_list_query_filter_{}'.format(filter['type'])](session_query, filters, filter)
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


def get_list_query_filter_date_in_range(session_query, filters, filter):
    if filter['value'] is not None:
        min_field, max_field = filter['fields']
        session_query = session_query.filter(filter['value'] >= min_field, filter['value'] <= max_field)
    return session_query


def get_item(db_model, field, value):
    with get_session() as session:
        return session.query(db_model).filter(field == value).one().__dict__
