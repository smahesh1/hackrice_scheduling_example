from flask import render_template, flash, redirect, session, url_for, request, g
from .models import Event
from .forms import FilterForm, EventForm
from app import app, db

EVENTS_PER_PAGE = 10

def find_largest_id():
    """
    Use clunky and un-pythonic code to find largest id
    TODO:Make this function nicer
    """
    max_id_val= 0
    for event in Event.query.all():
        if event.id > max_id_val:
            max_id_val = event.id
    return max_id_val
    
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET','POST'])
def index(page = 1):
    try:
        form = FilterForm()

        events = Event.query.all()
        events.reverse()
        eventsPager = Event.query.paginate(page, EVENTS_PER_PAGE, False)
        if request.method == 'POST' and form.validate_on_submit():
        	#queryVal = 
            if len(Event.query.filter(Event.date.ilike("%"+form.date.data+"%")).all()) > 0:
                eventsPager = Event.query.filter(Event.date.ilike("%"+form.date.data+"%")).paginate(page, EVENTS_PER_PAGE, False)
                events = eventsPager.items
            else:
                events = Event.query.all()
            return render_template('index.html', 
                title='Event Organizer', form=form, events=events, 
                eventsPager = eventsPager, pageName = "index")
        return render_template('index.html', title = 'Event Organizer', form =form, events = events, eventsPager = eventsPager, pageName = "index")
    except Exception as e:
        return(str(e))


@app.route('/add', methods = ['GET', 'POST'])
def add():
    if len(Event.query.all()) > 0:
        id_val = find_largest_id() + 1
    else:
        id_val = 1
    form = EventForm()
    if form.validate_on_submit():
        event = Event(id = id_val,date=form.date.data, location=form.location.data,
            start_time=form.start_time.data, end_time=form.end_time.data,
            description = form.description.data)
        db.session.add(event)
        db.session.commit()
        flash(event.description + ' is now posted!')
        return redirect(url_for('index'))
    return render_template('add.html',
        title = 'Add Event', form =form)