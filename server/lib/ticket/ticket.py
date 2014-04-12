from lib.ticket.ticket_tables import TicketGroupDatabase, TicketDatabase
from lib.database import connection as dbconn
from lib.database.basic_tables import ServiceGroupDatabase, ServerDatabase, ServiceDatabase


# Is called before or after flush so commit _should_ follow
# Is probably bit hairy
def create_ticket(service_group_id, new, old):
    ticket_group = TicketGroupDatabase()
    ticket_group.save()

    sg = ServiceGroupDatabase.query().filter(ServiceGroupDatabase.id == service_group_id).one()

    services = ServiceDatabase.query().filter(ServiceDatabase.service_group_id == sg.id).all()
    for s in services:
        ticket = TicketDatabase()
        ticket.old_data = old
        ticket.new_data = new
        ticket.ticket_group_id = ticket_group.id
        ticket.save()