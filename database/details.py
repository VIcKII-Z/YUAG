"""Script to show the detailed info of certain object"""
import sys

from sqlite3 import connect, IntegrityError, OperationalError, DatabaseError
from contextlib import closing


DB_FILE = 'lux.sqlite'

def validate_id(conn, obj_id):
    """
    Check if the argument ID is valid.
    """
    if not obj_id.isdigit():
        raise TypeError(f"Input Object id : {obj_id} is not digit. Please check.")

    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM objects where objects.id={obj_id}")
    if cursor.fetchone() is None:
        raise IntegrityError("Record not found. The database does not have " \
                            f"any objects with ID {obj_id}. Please check.")
    return True

def get_filter_term_by_id(obj_id):
    """
    Generate query by fileter and output required information.
    """
    label = f"""select o.label, o.accession_no, o.date, group_concat(ifnull(p.label, ''), ',')
            from objects o 
            left outer join objects_places op on op.obj_id = o.id
            left outer join places p on p.id = op.pl_id
            where o.id = {obj_id};
            """

    produce_by = f"""select group_concat(IFNULL(p.part, 'null'), '||'),
                group_concat(IFNULL(a.name, 'null'), '||'),
                group_concat(IFNULL(a.end_date, 'null'), '||'), 
                group_concat(IFNULL(a.begin_date, 'null'), '||'), 
                group_concat(IFNULL(an.nations, 'null'), '||')
                from
                objects o
                LEFT OUTER JOIN productions p on o.id = p.obj_id
                LEFT OUTER JOIN agents a ON p.agt_id = a.id
                LEFT OUTER JOIN(
                select a.name name, group_concat(n.descriptor, '|') nations from
                agents a
                LEFT OUTER JOIN agents_nationalities ON agents_nationalities.agt_id = a.id
                LEFT OUTER JOIN nationalities n ON agents_nationalities.nat_id = n.id
                group by a.name
                ) an ON an.name = a.name
                                    

                where o.id = {obj_id}
                group by o.id;
                """
    classification = f"""select group_concat(name, ",")
                    from objects o
                    left outer join objects_classifiers oc on o.id = oc.obj_id
                    left outer join classifiers c on oc.cls_id = c.id
                where o.id = {obj_id}
                """
    information = f"""select group_concat(IFNULL(r.type, ''), '|'),
                    group_concat(IFNULL(r.content, ''), '|') from 
                    objects o
                    LEFT OUTER JOIN "references" r  ON o.id = r.obj_id
                    where o.id = {obj_id};
                """
    return label, produce_by, classification, information

def get_filter_objects_details(filter_term):
    """
    Get objects from database by filter query.
    """

    try:
        with connect(DB_FILE) as connection:
            # Check if empty database
            # validate_id(connection, args.id)

            with closing(connection.cursor()) as cursor:
                try:
                    rows = []
                    for query in filter_term:
                        cursor.execute(query)
                        rows.append(cursor.fetchall())
                # corrupted database
                except DatabaseError as ex:
                    print(f"Error executing the query: {ex}", file=sys.stderr)
                    sys.exit(1)
        return rows

    # database cannot be opened/connected
    except OperationalError as ex:
        print(f"Error connecting to the database: {ex}", file=sys.stderr)
        sys.exit(1)

def process_date(date):
    """
    Take in date and output year.
    """
    if date=='null':
        return ''
    year = date.split('-', 1)[0]
    return year

def help_format(row, sep_str):
    """
    help convert to table rows
    """
    if row:
        return list(zip(*[ele.split(sep_str) for ele in row]))
    return ''


def output_objects(row):
    """
    Format the output.
    """
    object_info, produce_by, classification, information = row[0][0], row[1][0], \
                                                    row[2][0][0], help_format(row[3][0], '|')

    timespans = []
    for stt_date, end_date in zip(produce_by[-2].split('||'), produce_by[-3].split('||')):
        timespans.append(process_date(stt_date) + '-' + process_date(end_date))
    timespan = '||'.join(timespans)
    produce_by_new= []
    for i, ele in enumerate(produce_by):
        if i not in (2, 3):
            produce_by_new.append(ele)
    produce_by_new.append(timespan)
    produce_by_new = help_format(produce_by_new, '||')

    return {'label': object_info[0], 'accession_no': object_info[1],
            'date': object_info[2], 'place': object_info[3],
            'classification': classification, 'agents': produce_by_new, 
            'references': information}

def get_obj_by_id(obj_id):
    """get object by id"""
    sql = get_filter_term_by_id(obj_id)
    rows = get_filter_objects_details(sql)
    obj = output_objects(rows)
    obj['id'] = obj_id
    return obj
