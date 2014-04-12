from .ticket_tables import *
from lib.database import connection as dbconn

def create_ticket():
    ticketgroup = TicketGroupDatabase()
    ticketgroup.save()
    dbconn.session.safe_commit()
    
    print("Create ticketgroup " + str(ticketgroup.id))