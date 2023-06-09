"""Script to filter the database by certain terms"""
import os
import sys
from contextlib import closing
from sqlite3 import connect, OperationalError, DatabaseError

DB_FILE = 'lux.sqlite'
_DATABASE_URL = 'file:lux.sqlite?mode=ro'


if not os.path.isfile(DB_FILE):
    print(f"Database file not found: {DB_FILE}", file=sys.stderr)


class EmptyDatabaseError(Exception):
    """
    Error if database is empty.
    """

def validate_if_table_has_data(conn, table_name):
    """
    Check if table is empty.
    """
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    if cursor.fetchone() is None:
        raise EmptyDatabaseError(f"The table '{table_name}' does not have any data.")
    return True

def get_filter_terms(by_agt='', by_dep='', by_cls='', by_label=''):
    """
    Generate query by the filter terms.
    """

    product = """select id, group_concat(name, '|') as product_agent_names,
                        group_concat(name||' ('||part||')', '|') as product from (
                        select o.id, a.name as name, p.part as part
                        from objects o
                        left outer join productions p on o.id = p.obj_id 
                        left outer join agents a on a.id = p.agt_id  
                        order by lower(a.name), lower(p.part)
                    )
                    group by id
                """
    department = """select id, group_concat(name,'|') as department from (
                        select o.id, d.name as name
                        from objects o
                        left outer join objects_departments od on o.id = od.obj_id
                        left outer join departments d on od.dep_id = d.id
                    ) 
                    group by id 
                """
    classified = """select id, group_concat(name, '|') as classified from (
                        select o.id, c.name as name
                        from objects o
                        left outer join objects_classifiers oc on o.id = oc.obj_id
                        left outer join classifiers c on oc.cls_id = c.id
                        order by lower(c.name)
                    )
                    group by id
                """
    query = f"""select id, label, date, product, classified from (
        select oo.id, oo.label, p.product product, p.product_agent_names product_agent_names, oo.date, dd.department department, cc.classified classified
        from objects oo
        left outer join ({product}) as p on oo.id=p.id
        left outer join ({department}) as dd on oo.id=dd.id
        left outer join ({classified}) as cc on oo.id=cc.id
    ) as full_table

    """

    exist_agmt = False
    if by_agt:
        # print('a:', by_agt)
        query += f" where full_table.product_agent_names like '%{by_agt}%' "
        exist_agmt = True
    if by_cls:
        # print('c:', by_cls)

        query += f" where classified like '%{by_cls}%' " if not exist_agmt \
                 else f" and classified like '%{by_cls}%' "
        exist_agmt = True
    if by_dep!='':
        # print('d:', by_dep)

        query += f" where department like '%{by_dep}%' " if not exist_agmt \
                 else f" and department like '%{by_dep}%' "
        exist_agmt = True
    if by_label:
        # print('l:', by_label)

        query += f" where label like '%{by_label}%' " if not exist_agmt \
                 else f" and label like '%{by_label}%' "
        exist_agmt = True

    query += """ GROUP BY
                id
                ORDER BY
                label,
                date,\n"""

    #sort with arguments

    if by_cls:
        query += 'classified,\nproduct\n'
    else:
        query += 'product,\nclassified\n'

    # limit number
    query += "\nlimit 1000;"
    # print(query)

    return query

def get_filter_objects(filter_term):
    """Get objects from database by filter query."""

    try:
        with connect(DB_FILE) as connection:
            # Check if empty database
            validate_if_table_has_data(connection, 'objects')

            with closing(connection.cursor()) as cursor:
                try:
                    cursor.execute(filter_term)
                    rows = cursor.fetchall()
                # corrupted database
                except DatabaseError as ex:
                    print(f"Error executing the query: {ex}", file=sys.stderr)
                    sys.exit(1)
        return rows

    # database cannot be opened/connected
    except OperationalError as ex:
        print(f"Error connecting to the database: {ex}", file=sys.stderr)
        sys.exit(1)

def search(agent, department, classifier, label):
    """Search objects by filter terms."""
    filters = get_filter_terms(agent, department, classifier, label)
    objects = get_filter_objects(filters)
    # results = [' '.join([str(item) for item in object]) for object in objects]
    return objects
