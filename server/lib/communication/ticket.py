from lib.communication.ticket_tables import TicketGroupDatabase, TicketDatabase
from lib.database import connection as dbconn
from lib.database.basic_tables import ServiceGroupDatabase, ServerDatabase, ServiceDatabase

import logging
logger = logging.getLogger('ticket')

def create_ticket(user_data_table):
    logger.info("Creating ticket for renkiSrv instances")
    service_group_id = user_data_table.get_service_group_id()

    ticket_group = TicketGroupDatabase()
    ticket_group.save()
    dbconn.session.flush()

    user_data_table.ticket_group_id = ticket_group.id
    user_data_table.real_save()
    dbconn.session.flush()
    
    new_data = str(user_data_table.as_dict())

    History = user_data_table.__history_mapper__.class_

    try:
        History.query().filter(History.id == user_data_table.id).one()
        old_data = "old"
    except:
        old_data = "new"

    # Find all the servers that the ticket needs to be sent to
    sg = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.id == service_group_id).one()
    services = ServiceDatabase.query().filter(ServiceDatabase.service_group_id == sg.id).all()
    for s in services:
        ticket = TicketDatabase()
        ticket.old_data = old_data
        ticket.new_data = new_data
        ticket.ticket_group_id = ticket_group.id
        ticket.save()

def create_delete_ticket(user_data_table):
    service_group_id = user_data_table.get_service_group_id()

    ticket_group = TicketGroupDatabase()
    ticket_group.save()
    dbconn.session.flush()

    # Find all the servers that the ticket needs to be sent to
    sg = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.id == service_group_id).one()
    services = ServiceDatabase.query().filter(ServiceDatabase.service_group_id == sg.id).all()
    for s in services:
        ticket = TicketDatabase()
        ticket.old_data = str(user_data_table.as_dict())
        ticket.new_data = "deleted"
        ticket.ticket_group_id = ticket_group.id
        ticket.save()
