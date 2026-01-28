import itertools

import fastapi

from open_bus_stride_db.db import _sessionmaker

from ..routers import common


QUERY_PAGE_SIZE = 1000


def list_(sql, sql_params, default_limit, limit, offset, get_count, order_by, skip_order_by):
    session = _sessionmaker()
    try:
        if get_count:
            sql = f'select count(1) from ({sql}) as count'
            cnt = list(session.execute(sql, sql_params))[0][0]
            session.close()
            return fastapi.Response(content=str(cnt), media_type="application/json")
        else:
            if get_count:
                limit, offset, default_limit, order_by = None, None, None, None
            elif not limit and default_limit:
                limit = default_limit
            if limit:
                limit = int(limit)
            order_by_args, limit, offset = common.process_list_query_order_by_limit_offset(skip_order_by, order_by, get_count, limit, offset, skip_order_by_id_field=True)
            sql_order_by, sql_limit, sql_offset = '', '', ''
            if order_by_args is not None:
                sql_order_by = ' order by ' + ', '.join([f'{fieldname} {direction}' for direction, fieldname in order_by_args])
            if limit is not None:
                sql_limit = f' limit {limit}'
            assert get_count or (sql_limit and 0 < limit <= 15000), "due to abuse, limit must be between 1 and 15000, contact us if you need more"
            if offset is not None:
                sql_offset = f' offset {offset}'
            if sql_order_by or sql_limit or sql_offset:
                sql = f'select * from ({sql}) a {sql_order_by}{sql_limit}{sql_offset}'
            data = [common.post_process_response_obj(obj, None) for obj in session.execute(sql, sql_params)]
            session.close()
            return data
            # iterator = (o for o in session.execute(sql, sql_params, execution_options={'stream_results': True}))
            # first_items = list(itertools.islice(iterator, QUERY_PAGE_SIZE + 1))
            # if len(first_items) <= QUERY_PAGE_SIZE:
            #     common.debug_print(f'got {len(first_items)} items - returning without streaming')
            #     data = [common.post_process_response_obj(obj, None) for obj in first_items]
            #     session.close()
            #     return data
            # else:
            #     common.debug_print(f'got {len(first_items)} items - returning using streaming')
            #     return fastapi.responses.StreamingResponse(
            #         common.streaming_response_iterator(session, first_items, iterator, None),
            #         media_type="application/json"
            #     )
    except:
        session.close()
        raise
