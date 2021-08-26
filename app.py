from flask import Flask, render_template, url_for, request, redirect, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import sys
import os
import subprocess
import pandas as pd
import numpy as np
from matplotlib.figure import Figure
import matplotlib.colors as colors
from io import BytesIO
import base64
# import matplotlib as mpl
# mpl.use('Agg')
# import matplotlib.pyplot as plt

# from PIL import Image
# import io

app = Flask(__name__)

def make_arguments(inputs):
	res = []
	for k, v in inputs.items():
		res.append('--' + k + '=' + str(v))
	return res

def make_plot(df):
	L = int(df.N.unique())
	c = str(int(L/2))
	xs = np.arange(1,L+1)
	cols = [str(x) for x in xs]
	Icols = ['I'+str(x) for x in xs]

	ts = np.array(df.t.unique())
	AZs = np.sqrt(np.array(df[cols])**2 + np.array(df[Icols])**2)
	autoR = np.array(df[c])
	autoI = np.array(df['I'+c])
	autoA = np.sqrt(autoR**2 + autoI**2)


	fig = Figure()
	ax = fig.subplots()
	cax = ax.contourf(xs,ts,AZs,200, cmap="inferno" ,norm = colors.SymLogNorm(linthresh = 0.5, base=10))
	ax.set_xlabel('$x$',fontsize=14)
	ax.set_ylabel('$t$',fontsize=14)
	fig.colorbar(cax)
	buf = BytesIO()
	fig.savefig(buf, format="png")
	data_corr = base64.b64encode(buf.getbuffer()).decode("ascii")

	fig = Figure()
	ax = fig.subplots()
	ax.plot(ts,autoR,color='k',label='real')
	ax.plot(ts,autoI,color='b',label='imag')
	ax.plot(ts,autoA,color='r',label='abs')
	ax.set_xlabel('$t$',fontsize=14)
	ax.set_ylabel(r'$G(x=0,t)$',fontsize=14)
	ax.legend()
	buf = BytesIO()
	fig.savefig(buf, format="png")
	data_auto = base64.b64encode(buf.getbuffer()).decode("ascii")

	# return f"<img src='data:image/png;base64,{data_corr}'/>\n<img src='data:image/png;base64,{data_auto}'/>"
	return f"data:image/png;base64,{data_corr}", f"data:image/png;base64,{data_auto}"


def run_code(inputs):
	inputs['write'] = "false"
	inputs['resDir'] = "code/"
	inputs['Silent'] = "true"
	inputs['SiteSet'] = "SpinHalf"
	inputs['nSweeps'] = 5
	# sweeps_maxdim = [int(1.0/float(inputs['nSweeps'])*n*inputs['MaxDim']) for n in range(1, inputs['nSweeps']+1)]
	# inputs['sweeps_maxdim'] = str(sweeps_maxdim).strip("[").strip("]").replace(" ","")
	if(inputs['state'] == "Ground"): 
		inputs['thermal'] = "false"
	result = subprocess.run(["code/main"]+make_arguments(inputs),capture_output=True)
	s = str(result.stdout)
	_file_name = s.split()[-1]
	file_name = _file_name.replace("\\n'","")
	return pd.read_csv(file_name)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

# Database
db = SQLAlchemy(app)
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id


# setup initial page
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/correlation', methods=['GET','POST'])
def correlation():
	if request.method == 'POST':
		inputs = dict(request.form)
		inputs['Correlation'] = "true"
		url_cor, url_auto = make_plot(run_code(inputs))
		return render_template('correlation.html', url_cor=url_cor, url_auto=url_auto)
	else:
		return render_template('correlation.html', url_cor="static/plot/correlation.png", url_auto="static/plot/auto-correlation.png")

@app.route('/correlation<int:id>', methods=['GET','POST'])
def correlation_image():
	if request.method == 'POST':
		res = dict(request.form)
		return redirect('/correlation/10')
	else:
		return render_template('correlation/10.html')

@app.route('/neutron')
def neutron():
    return render_template('neutron.html')


##########################################
############### TEMP #####################
##########################################

# @app.route('/', methods=['POST', 'GET'])
# def index():
# 	if request.method == 'POST':
# 		task_content = request.form['content']
# 		new_task = Todo(content=task_content)

# 		try:
# 			db.session.add(new_task)
# 			db.session.commit()
# 			return redirect('/')
# 		except:
# 			return 'There was an issue adding your task'

# 	else:
# 		tasks = Todo.query.order_by(Todo.date_created).all()
# 		return render_template('index.html', tasks=tasks)

# # Delete button implementation
# @app.route('/delete/<int:id>')
# def delete(id):
#     task_to_delete = Todo.query.get_or_404(id)

#     try:
#         db.session.delete(task_to_delete)
#         db.session.commit()
#         return redirect('/')
#     except:
#         return 'There was a problem deleting that task'

# Update button implementation
# @app.route('/update/<int:id>', methods=['GET', 'POST'])
# def update(id):
#     task = Todo.query.get_or_404(id)

#     if request.method == 'POST':
#         task.content = request.form['content']

#         try:
#             db.session.commit()
#             return redirect('/')
#         except:
#             return 'There was an issue updating your task'

#     else:
#         return render_template('update.html', task=task)


if __name__ == "__main__":
    app.run(debug=True)
