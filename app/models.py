from app import db

class Event(db.Model):
    """
    A table to store data on scheduling.
    """

    #__tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200))
    date = db.Column(db.String(64))
    location = db.Column(db.String(200))
    start_time = db.Column(db.String(64))
    end_time = db.Column(db.String(64))

    def __repr__(self):
        return '<Evnet %r>' % (self.description)