import sys, os # math, ast
import numpy as np


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QApplication, QPushButton, QDesktopWidget, 
QGroupBox, QLineEdit, QHBoxLayout, QVBoxLayout, QFrame, QFormLayout,
QDoubleSpinBox, QLabel, QComboBox
)
from PyQt5.QtCore import QDir, Qt

from lmfit.models import GaussianModel
from arpes.io import example_data


# user defined package
from reader import read_file
from utils import normalize, shirley_baseline


def getDoubleSpinBox():
	box = QDoubleSpinBox()
	box.setMinimum(float("-inf"))
	box.setMaximum(float("inf"))
	box.setDecimals(3)
	box.setSingleStep(0.05)
	box.setValue(10.00)
	return box
	
def sigma2fwhm(sigma):
	fwhm = 2.3548*sigma
	return fwhm

def fwhm2sigma(fwhm):
	if isinstance(fwhm, float):
		sigma = 1.0/2.3548 * fwhm
		return sigma 

def calculate_height(area, sigma):
	if isinstance(area, float) and isinstance(sigma, float):
	    return 0.3989 * area / max(1e-12,sigma)

class FitWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setUi()

	def setUi(self):
		# set the title
		self.setWindowTitle("Gaussion Fitting")
		# setting  the geometry of window
		self.setGeometry(600, 300, 1200, 700)
		self.center()

		# main Layout
		self.main_layout = QHBoxLayout()
		self.setLayout(self.main_layout)
		
		self.create_left_layout()
		self.create_right_layout()

		v_line = QFrame()
		v_line.setFrameShape(QFrame.VLine)
		v_line.setLineWidth(2)
		v_line.setFrameShadow(QFrame.Sunken)

		self.main_layout.addLayout(self.left_layout)
		self.main_layout.addWidget(v_line)
		self.main_layout.addLayout(self.right_layout)


	def create_left_layout(self):
		# setup Matplotlib Figure: Canvas 
		self.figure, (self.a_top, self.a_bot) = plt.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [4,1], 'hspace': 0.05})
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)

		# left layout is the graph
		self.left_layout = QVBoxLayout()
		self.left_layout.addWidget(self.toolbar)
		self.left_layout.addWidget(self.canvas)

	def create_right_layout(self):

		self.right_layout = QVBoxLayout()

		# list of dropdown function selection default Core Level fitting
		self.func_list = ["Core level", "Fermi edge"]

		# create comboBox swithes the different functions
		self.comb_func = QComboBox(self)
		self.comb_func.addItems(self.func_list)
		self.comb_func.currentIndexChanged.connect(self.choose_func)
		self.comb_func.setCurrentIndex(0)
		

		# add open button
		self.b_open = QPushButton('Open', self)
		self.b_open.setFocus()
		self.b_open.clicked.connect(self.open_file)

		# Current directory
		self.dir = QDir.currentPath()

		# add path filename line edit
		self.l_path_file = QLineEdit()
		self.l_path_file.setAlignment(Qt.AlignLeft)
		self.l_path_file.setText(self.dir)

		# open file group
		open_file_layout = QHBoxLayout()
		open_file_layout.addWidget(self.b_open)
		open_file_layout.addWidget(self.l_path_file)


		# user input parameters for Gaussian fit
		self.gauss_para_group = QGroupBox()
		self.gauss_para_group.setTitle("Core Level")

		form_layout = QFormLayout()
		lb_ctr = QLabel("Center")
		self.dsb_center = getDoubleSpinBox()
		form_layout.addRow(lb_ctr, self.dsb_center)

		lb_area = QLabel("Area")
		self.dsb_area = getDoubleSpinBox()
		# connect mathmatic constraint variable height, area, sigma
		self.dsb_area.valueChanged.connect(self.update_height)
		form_layout.addRow(lb_area, self.dsb_area)

		lb_fwhm = QLabel("FWHM")
		self.dsb_fwhm = getDoubleSpinBox()
		# connect mathmatic constraint variable fwhm and sigma
		self.dsb_fwhm.valueChanged.connect(self.update_sigma)
		form_layout.addRow(lb_fwhm, self.dsb_fwhm)	

		lb_sigma = QLabel("Sigma")
		self.dsb_sigma = getDoubleSpinBox()
		# print(type(self.dsb_fwhm.value()))
		self.dsb_sigma.setValue(fwhm2sigma(self.dsb_fwhm.value()))
		# connect mathmatic constraint variable height, area, sigma
		self.dsb_sigma.valueChanged.connect(self.update_height)
		self.dsb_sigma.setReadOnly(True)
		form_layout.addRow(lb_sigma, self.dsb_sigma)		

		lb_height = QLabel("Height")
		self.dsb_height = getDoubleSpinBox()
		self.dsb_height.setValue(calculate_height(self.dsb_area.value(), self.dsb_sigma.value()))
		self.dsb_height.setReadOnly(True)
		form_layout.addRow(lb_height, self.dsb_height)	
			
		lb_chi_sqr = QLabel("Reduced Chi-Sqr")
		self.dsb_chi_sqr = getDoubleSpinBox()
		self.dsb_chi_sqr.setReadOnly(True)		
		form_layout.addRow(lb_chi_sqr, self.dsb_chi_sqr)	

		self.gauss_para_group.setLayout(form_layout)

		self.fermi_para_group = QGroupBox()
		self.fermi_para_group.setTitle("Fermi Edge")

		form_layout = QFormLayout()
		lb_temp = QLabel("Temperature (K)")
		self.dsb_temp = getDoubleSpinBox()
		form_layout.addRow(lb_temp, self.dsb_temp)

		lb_fermi_ctr = QLabel("Fermi Center(eV)")
		self.dsb_fermi_ctr = getDoubleSpinBox()
		form_layout.addRow(lb_fermi_ctr, self.dsb_fermi_ctr)

		lb_delta_e = QLabel("BL \u0394E (eV)")
		self.dsb_delta_e = getDoubleSpinBox()
		form_layout.addRow(lb_delta_e, self.dsb_delta_e)

		lb_sptrm = QLabel("Spectrum \u0394E (eV)")
		self.dsb_sptrm = getDoubleSpinBox()
		form_layout.addRow(lb_sptrm, self.dsb_sptrm)	

		self.fermi_para_group.setLayout(form_layout)
		self.fermi_para_group.setDisabled(True)		

		# excutable buttions group
		# add evalate buttion
		self.b_eval  = QPushButton('&Evaluate', self)
		self.b_eval.clicked.connect(self.eval)

		# add preview buttion
		self.b_preview  = QPushButton('&Preview', self)
		self.b_preview.clicked.connect(self.preview)

		# add Fit buttion
		self.b_fit  = QPushButton('&Fit', self)
		self.b_fit.clicked.connect(self.fit)

		v_layout = QHBoxLayout()
		v_layout.addWidget(self.b_eval)
		v_layout.addWidget(self.b_preview)
		v_layout.addWidget(self.b_fit)

		self.right_layout.addWidget(self.comb_func)
		self.right_layout.addLayout(open_file_layout)
		self.right_layout.addWidget(self.gauss_para_group)
		self.right_layout.addWidget(self.fermi_para_group)
		self.right_layout.addLayout(v_layout)

	def choose_func(self):
		# print(f"here {self.comb_func.currentIndex()}")
		if self.comb_func.currentIndex() == 0:
			self.gauss_para_group.setEnabled(True)
			self.fermi_para_group.setDisabled(True)
		elif self.comb_func.currentIndex() == 1:
			self.gauss_para_group.setDisabled(True)
			self.fermi_para_group.setEnabled(True)

	def update_sigma(self):
		self.dsb_sigma.setValue(fwhm2sigma(self.dsb_fwhm.value()))
	
	def update_height(self):
		self.dsb_height.setValue(calculate_height(self.dsb_area.value(), self.dsb_sigma.value()))

	def open_file(self):
		pathfile_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self.dir)
		if pathfile_name != "":
			# print(pathfile_name)
			self.filepath = pathfile_name
			self.dir = os.path.dirname(pathfile_name)
			self.l_path_file.setText(pathfile_name)
			self.read()
	
	def read(self):
		# read file and plot int he figure
		data = read_file(self.filepath)
		# print(data.spectrum.keys())
		# conside only one region in file
		self.x0 = data.spectrum["Region 1"][:,0]
		self.y0 = data.spectrum["Region 1"][:,1]

		# plot the import data in figure
		self.plot()
	
	def plot(self):
		self.clear_plot()
		self.a_top.plot(self.x0, self.y0, "-o", color="b", label="exp")
		self.update_plot()

	def clear_plot(self):
		# clear the current plot
		self.a_top.cla()
		self.a_bot.cla()

	def update_plot(self):
		# decorate the plots
		self.a_bot.set_xlabel("Binding energy (eV)", fontsize=12)
		plt.xlim(self.x0[0], self.x0[-1])
		if self.x0[0] < self.x0[-1]:
			self.a_bot.invert_xaxis()
		self.a_top.set_ylabel('Intensity (arb. unit)', fontsize=12)
		self.a_top.grid(True)
		self.a_top.legend(loc=0)
		self.a_bot.legend(loc=0)
		self.canvas.draw()

	def eval(self):

		pass

	def preview(self):
		# preview the Gaussion peak with init parameters 
		# print("preview is clicked!")
		if self.has_data():
			self.setup_model()
			self.eval_result = self.model.eval(self.pars, x=self.x0)	
			self.plot_preview_result()

	def plot_preview_result(self):
		self.clear_plot()
		self.a_top.plot(self.x0, self.y0, "o", color= "b", label="exp")
		self.a_top.plot(self.x0, self.eval_result,'r-', label="fit" )
		self.a_bot.plot(self.x0, self.eval_result-self.y0, 'g.', label='residual')
		self.update_plot()

	def fit(self):
		# fit the gauss peak funcition
		# print(self.has_data())
		# print("fit is clicked!")
		if self.has_data(): 
			self.setup_model()
			self.gauss_fit()
			self.update_result_para()
			self.plot_result()

	def update_result_para(self):
		self.dsb_center.setValue(self.results.params["center"].value)
		self.dsb_area.setValue(self.results.params["amplitude"].value)
		self.dsb_fwhm.setValue(sigma2fwhm(self.results.params["sigma"].value))
		self.dsb_chi_sqr.setValue(self.results.redchi)

	def plot_result(self):
		self.clear_plot()
		self.a_top.plot(self.x0, self.y0, "o", color= "b", label="exp")
		self.a_top.plot(self.x0, self.results.best_fit,'r-', label="fit" )
		self.a_top.fill_between(self.x0, self.results.best_fit, color="r", alpha=0.5)
		self.a_bot.plot(self.x0, self.results.residual, 'g.', label='residual')
		

		self.a_top.annotate("", xy=(0.5, 0.5), xycoords=self.a_top.transAxes)
		self.update_plot()
	
	def setup_model(self):
		self.model = GaussianModel()
		self.pars = self.model.make_params()
		self.pars['center'].set(self.dsb_center.value())
		self.pars['sigma'].set(self.dsb_sigma.value())
		self.pars['amplitude'].set(self.dsb_area.value())

	def gauss_fit(self, method = "leastsq"):
		if hasattr(self,"model"):
			self.results = self.model.fit(self.y0, self.pars, x=self.x0, method=method, nan_policy="omit")

			
	def has_data(self):
		# check if the data is existed 
		if hasattr(self, "x0") and hasattr(self, "y0"):
			return True
		else:
			return False		

	def center(self):
		"""
		Move the window to the center of the screen.
		"""
		size = self.geometry()
		screen = QDesktopWidget().availableGeometry()
		self.move(
			(screen.width() - size.width()) // 2, 
			(screen.height() - size.height()) // 2 
			)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	w = FitWidget()
	w.show()
	sys.exit(app.exec_())
