from flask import Flask, render_template, url_for, request, redirect, jsonify, send_file
# from flask_sqlalchemy import SQLAlchemy
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

def rescale(zs, vmin = 0, vmax = 1):
    _zs = np.array(zs)
    zmin = np.min(_zs)
    zmax = np.max(_zs)
    res = ( (_zs - zmin) * (vmax - vmin) ) / (zmax - zmin) + vmin
    return res

def make_arguments(inputs):
	res = []
	for k, v in inputs.items():
		res.append('--' + k + '=' + str(v))
	return res

def make_plot(df):

	thermal = bool(df.thermal.unique())
	if thermal:
	    scale = 1
	    vmin = 2E-5
	    vmax = 1
	else:
	    scale = 10
	    vmin = 2E-3
	    vmax = 1
	L = int(df.N.unique())
	c = str(int(L/2))
	xs = np.arange(1,L+1)
	cols = [str(x) for x in xs]
	Icols = ['I'+str(x) for x in xs]

	ts = np.array(df.t.unique())
	RZs = np.array(df[cols])**2
	AZs = np.sqrt(np.array(df[cols])**2 + np.array(df[Icols])**2)
	if thermal:
	    scale = 1
	    zs = rescale(abs(RZs),vmin = 2E-5, vmax = 1)
	else:
	    scale = 10
	    zs = rescale(AZs,vmin = 2E-3, vmax = 1)
	autoR = np.array(df[c])
	autoI = np.array(df['I'+c])
	autoA = np.sqrt(autoR**2 + autoI**2)


	fig = Figure()
	ax = fig.subplots()
	levs = np.logspace(np.log10(scale*np.min(zs)), np.log10(np.max(zs)), 60)
	cax = ax.contourf(xs, ts, zs, levs, norm=colors.LogNorm(), extend='both')

	ticks = [levs[0],levs[-1]]
	labels = ['1E-5','1']
	cbar = fig.colorbar(cax, ticks=ticks)
	cbar.ax.set_yticklabels(labels)
	ax.set_xlabel('$x$',fontsize=14)
	ax.set_ylabel('$t$',fontsize=14)
	fig.tight_layout()
	buf = BytesIO()

	fig.savefig(buf, format="png")
	data_corr = base64.b64encode(buf.getbuffer()).decode("ascii")

	fig = Figure()
	ax = fig.subplots()
	# ax.plot(ts,abs(autoR),color='k',label='real')
	# ax.plot(ts,abs(autoI),color='b',label='imag')
	ax.plot(ts,abs(autoA),color='r')
	ax.set_xscale('log')
	ax.set_yscale('log')
	ax.set_ylabel('testing',fontsize=14)
	ax.set_xlabel('$t$',fontsize=14)
	fig.tight_layout()
	ax.set_ylabel('$|G(x=0,t)|$',fontsize=14)

	# ax2 = ax.twinx()
	# ax2.set_ylabel(r'$G(x=0,t)$',fontsize=14)
	# ax.legend()
	buf = BytesIO()
	fig.savefig(buf, format="png")
	fig.savefig('trash.png')
	data_auto = base64.b64encode(buf.getbuffer()).decode("ascii")

	# return f"<img src='data:image/png;base64,{data_corr}'/>\n<img src='data:image/png;base64,{data_auto}'/>"
	return f"data:image/png;base64,{data_corr}", f"data:image/png;base64,{data_auto}"


def run_code(inputs):
	# Include a save and load system here to save some time. 
	# DB is the proper way to do this, but for the sake of time 
	# we ignore this and just use the value of the form.
	inputs['write'] = "false"
	inputs['resDir'] = "code/"
	inputs['Silent'] = "true"
	inputs['SiteSet'] = "SpinHalf"
	inputs['Model'] = "XXZ"
	inputs['nSweeps'] = 5
	inputs['beta'] = 0
	inputs['Evolver'] = "Trotter"
	inputs['swap'] = "true"
	# if(inputs['Evolver'] == "TEBD"):
	# 	inputs['Evolver'] = "Trotter"
	# sweeps_maxdim = [int(1.0/float(inputs['nSweeps'])*n*inputs['MaxDim']) for n in range(1, inputs['nSweeps']+1)]
	# inputs['sweeps_maxdim'] = str(sweeps_maxdim).strip("[").strip("]").replace(" ","")
	if "Ground" in inputs['state']:
		inputs['thermal'] = "false"
	result = subprocess.run(["code/main"]+make_arguments(inputs),capture_output=True)
	s = str(result.stdout)
	_file_name = s.split()[-1]
	file_name = _file_name.replace("\\n'","")
	print(file_name)
	return pd.read_csv(file_name)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

# # Database
# db = SQLAlchemy(app)
# class Todo(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     content = db.Column(db.String(200), nullable=False)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)

#     def __repr__(self):
#         return '<Task %r>' % self.id


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
