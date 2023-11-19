from flask import Flask, render_template, request, jsonify, redirect, session
import requests
import sqlite3
import couchdb
import os
from threading import Lock
from datetime import datetime


app = Flask(__name__)

app.secret_key = b'\xfc\xf5w^oV\xff\xee\xbd\xf9R+z\x82\xa3^'

# COUCHDB_URL = 'http://localhost:5984'
# DB_NAME = 'hostel-complaint-management'
# AUTH = ('admin', 'Admin@123')

couch = couchdb.Server('http://admin:Admin%40123@localhost:5984')
cdb = couch['hostel-complaint-management']

sqlite_lock = Lock()

def get_db():
	db = sqlite3.connect('database/users.db')
	db.row_factory = sqlite3.Row
	return db

def init_db():
	with app.app_context():
		db = get_db()
		cursor = db.cursor()
		cursor.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT);''')
		# cursor.execute('''INSERT INTO users (username, password) VALUES ("admin", "nitt@admin");''')
		# cursor.execute('''INSERT INTO users (username, password) VALUES ("h123", "nitt@123");''')
		# cursor.execute('''INSERT INTO users (username, password) VALUES ("h234", "nitt@234");''')
		# cursor.execute('''INSERT INTO users (username, password) VALUES ("h345", "nitt@345");''')
		# cursor.execute('''INSERT INTO users (username, password) VALUES ("h456", "nitt@456");''')
		# cursor.execute('''INSERT INTO users (username, password) VALUES ("h567", "nitt@567");''')
		db.commit()
		db.close()

if not os.path.isfile('database/users.db'):
    init_db()

@app.route('/')
def launchWebPage():
	return render_template('index.html')

@app.route('/goToLogin')
def goToLogin():
	return render_template('login.html')

@app.route('/goToRegistration')
def goToRegistration():
	return render_template('registration.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']

		db = get_db()
		cursor = db.cursor()

		cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
		(username, password))
		user = cursor.fetchone()
		cursor.close()

		if user:
			# flash('Login successful', 'success')
			# return render_template('admin/adminDashboard.html')
			session['user'] = username

			if username == "admin":
				doc = cdb.get(session.get('user'))
				return render_template('admin/adminDashboardProfile.html', doc=doc)
			elif username[0] == 'h':
				doc = cdb.get(session.get('user'))
				session['role'] = doc['role']
				#return jsonify({"doc" : str(doc), "user" : str(session.get('user')), "role" : str(session.get('role'))})
				return render_template('staff/staffDashboardProfile.html', doc=doc)
			else:
				doc = cdb.get(session.get('user'))
				return render_template('students/studentDashboardProfile.html', doc=doc)	
		else:
			return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		firstName = request.form['first_name']
		lastName = request.form['last_name']
		email = request.form['email']
		username = request.form['roll_no']
		hostel = request.form['hostel_name']
		room = request.form['room_no']
		password = request.form['password']
		rePassword = request.form['confirm_password']

		db = get_db()
		cursor = db.cursor()

		cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
				(username, password))
		db.commit()
		db.close()

		data = {
			"_id" : username,
			"firstName" : firstName,
			"lastName" : lastName,
			"email" : email,
			"hostel" : hostel,
			"room" : room,
		}

		try:
			message = cdb.save(data)

			doc = cdb.get('students')
			doc['all_ids'].append(message[0])
			cdb.save(doc)

			return render_template('login.html')
		except Exception as e:
			return jsonify({"error" : str(e)})
		
	return render_template('registration.html')

# students dashboard routes

@app.route('/goToStudentProfile')
def openStudentProfilePage():
	if session.get('user'):
		doc = cdb.get(session.get('user'))
		return render_template('students/studentDashboardProfile.html', doc=doc)
	else:
		return render_template('login.html')

@app.route('/goToNewComplaint')
def openNewComplaintPage():
	return render_template('students/studentDashboardNewComplaint.html')

@app.route('/goToPrevComplaints')
def openPrevComplaintsPage():
	#result = cdb.find({'selector': {'student_id': {'$eq': session.get('user')}}})
	result = cdb.view('myComplaints/prev-complaints')
	result = [row for row in result.rows if row.value['username'] == session.get('user')]
	#return jsonify({"result" : str(result), "user" : str(session.get('user'))})
	return render_template('students/studentDashboardPrevComplaints.html', doc=result)

@app.route('/registerComplaint', methods=['GET', 'POST'])
def writeNewComplaint():
	if request.method == 'POST':
		comTitle = request.form['complaint-title']
		comType = request.form['complaint-type']
		comHostel = request.form['hostel-name']
		comRoom = request.form['room-number']
		comDesc = request.form['complaint-description']
		#comAttach = request.files['complaint-attachments']

		data = {
			"username" : session.get('user'),
			"datetime" : str(datetime.now()),
			"title" : comTitle,
			"type" : comType,
			"status" : "open",
			"hostel" : comHostel,
			"room" : comRoom,
			"desc" : comDesc
			# "attach" : comAttach
		}

		try:
			message = cdb.save(data)

			# return jsonify({"message" : str(message)})

			doc = cdb.get('complaints')
			doc['all_complaint_ids'].append(message[0])
			cdb.save(doc)

			doc = cdb.get(session.get('user'))

			return render_template('students/studentDashboardProfile.html', doc=doc)
		except Exception as e:
			return jsonify({"error" : str(e)})

	return render_template('students/studentDashboardNewComplaint.html')

# hostel staff dashboard routes

@app.route('/goToStaffProfile')
def openStaffProfilePage():
	if session.get('user'):
		doc = cdb.get(session.get('user'))
		return render_template('staff/staffDashboardProfile.html', doc=doc)
	else:
		return render_template('login.html')

@app.route('/goToStaffOpenComplaint')
def openstaffOpenComplaintsPage():
	result = cdb.view('myComplaints/prev-complaints')
	result1 = [row for row in result.rows if row.value['type'] == session.get('role') and row.value['status'] == 'open']
	result2 = [row for row in result.rows if row.value['type'] == session.get('role') and row.value['status'] == 'inprogress']
	#return jsonify({"result" : str(result), "user" : str(session.get('user')), "role" : str(session.get('role'))})
	return render_template('staff/staffDashboardOpenComplaints.html', doc1=result1, doc2=result2)

@app.route('/showDetails/<string:row_id>')
def showDetails(row_id):
	doc = cdb.get(row_id)
	#return jsonify({"doc" : str(doc)})
	return render_template('staff/showDetailComplaint.html', doc=doc)

@app.route('/goToStaffResolvedComplaints')
def operstaffResolvedComplaintsPage():
	result = cdb.view('myComplaints/prev-complaints')
	result = [row for row in result.rows if row.value['type'] == session.get('role') and row.value['status'] == 'resolved']
	return render_template('staff/staffDashboardResolvedComplaints.html', doc=result)

@app.route('/updateStatus/<string:comp_id>', methods=['POST', 'GET'])
def updateStatus(comp_id):
	if request.method == 'POST':
		try:
			doc = cdb[comp_id]

			doc['status'] = request.form['complaint-status']
			doc['staff'] = session.get('user')

			cdb[comp_id] = doc
			if session.get('user') == 'admin':
				return openAllActiveComplaintsPage()
			else:
				return openstaffOpenComplaintsPage()
			#return jsonify({'success': True, 'message': 'Document updated successfully'})
		except couchdb.http.ResourceNotFound:
			return jsonify({'success': False, 'message': 'Document not found'})

# admin dashboards routes

@app.route('/goToAdminProfile')
def openAdminProfilePage():
	if session.get('user'):
		doc = cdb.get(session.get('user'))
		return render_template('admin/adminDashboardProfile.html', doc=doc)
	else:
		return render_template('login.html')

@app.route('/goToAllActiveComplaint')
def openAllActiveComplaintsPage():
	# result = cdb.view('myComplaints/prev-complaints')
	# result = [row for row in result.rows if not row.value['status'] == 'resolved']
	# return render_template('admin/adminDashboardAllActiveComplaints.html', doc=result)
	result = cdb.view('myComplaints/prev-complaints')
	result1 = [row for row in result.rows if row.value['status'] == 'open']
	result2 = [row for row in result.rows if row.value['status'] == 'inprogress']
	#return jsonify({"result" : str(result), "user" : str(session.get('user')), "role" : str(session.get('role'))})
	return render_template('admin/adminDashboardAllActiveComplaints.html', doc1=result1, doc2=result2)

@app.route('/goToAllResolvedComplaint')
def openAllResolvedComplaintsPage():
	result = cdb.view('myComplaints/prev-complaints')
	result = [row for row in result.rows if row.value['status'] == 'resolved']
	return render_template('admin/adminDashboardAllResolvedComplaints.html', doc=result)

# common route for all the users

@app.route('/logout')
def logoutUser():
	if session.get('user')[0] == 'h':
		session.pop('role', None)
	session.pop('user', None)
	return redirect('/')


if __name__ == '__main__':
	app.run(debug=True, port=5001)









