from flask_wtf import Form
from wtforms import StringField, BooleanField, SelectField
from wtforms.validators import DataRequired

class FilterForm(Form):
	 date = StringField('event_date')

class EventForm(Form):
	date = StringField('event_date', validators = [DataRequired()])
	location = StringField('event_location', validators = [DataRequired()])
	start_time = StringField('event_start_time', validators = [DataRequired()])
	end_time = StringField('event_end_time', validators = [DataRequired()])
	description = StringField('event_description', validators = [DataRequired()])
