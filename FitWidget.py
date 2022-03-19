import sys, os 
import numpy as np


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QApplication, QPushButton, QDesktopWidget, 
QGroupBox, QLineEdit, QHBoxLayout, QVBoxLayout, QFrame, QFormLayout,
QDoubleSpinBox, QLabel, QComboBox, QTextEdit
)
from PyQt5.QtCore import QDir, Qt

from lmfit import CompositeModel, Model
from lmfit.models import GaussianModel
from lmfit.lineshapes import gaussian

# user defined package
from reader import read_file
from utils import (fwhm2sigma, sigma2fwhm, calculate_height, instr_delta_e, 
fermi_dirac, convolve, timestamp, normalize, shirley_baseline)


def getDoubleSpinBox():
	box = QDoubleSpinBox()
	box.setMinimum(float("-inf"))
	box.setMaximum(float("inf"))
	box.setDecimals(3)
	box.setSingleStep(0.05)
	box.setValue(10.00)
	return box
	
class FitWidget(QWidget):
	def __init__(self):
		super().__init__()
		self.setUi()

	def setUi(self):
		# set the title
		self.setWindowTitle("Gaussion Fitting")
		# setting  the geometry of window
		self.setGeometry(600, 300, 1600, 900)
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
		self.figure, (self.a_top, self.a_bot) = plt.subplots(2, 1, sharex=True, 
		gridspec_kw={'height_ratios': [4,1], 'hspace': 0.05})
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
		lb_ctr = QLabel("Center (eV)")
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
		self.dsb_temp.setMinimum(0.0)
		self.dsb_temp.setValue(300)
		form_layout.addRow(lb_temp, self.dsb_temp)

		lb_fermi_ctr = QLabel("Center(meV)")
		self.dsb_fermi_ctr = getDoubleSpinBox()
		self.dsb_fermi_ctr.setValue(0.0)
		form_layout.addRow(lb_fermi_ctr, self.dsb_fermi_ctr)

		lb_fermi_amp = QLabel("Amplitude")
		self.dsb_fermi_amp = getDoubleSpinBox()
		self.dsb_fermi_amp.setValue(10)
		form_layout.addRow(lb_fermi_amp, self.dsb_fermi_amp)

		lb_beaml_e = QLabel("BL \u0394E (meV)")
		self.dsb_beaml_e = getDoubleSpinBox()
		form_layout.addRow(lb_beaml_e, self.dsb_beaml_e)
		self.dsb_beaml_e.valueChanged.connect(self.update_meters_e)

		lb_conv_e = QLabel("Convolve \u0394E (meV)")
		self.dsb_conv_e = getDoubleSpinBox()
		form_layout.addRow(lb_conv_e, self.dsb_conv_e)
		self.dsb_conv_e.valueChanged.connect(self.update_meters_e)
		
		lb_instr = QLabel("Instrument \u0394E (meV)")
		self.dsb_instr = getDoubleSpinBox()
		form_layout.addRow(lb_instr, self.dsb_instr)
		

		self.fermi_para_group.setLayout(form_layout)
		self.fermi_para_group.setDisabled(True)		

		# excutable buttions group
		# add guessate buttion
		self.b_guess  = QPushButton('&Guess', self)
		self.b_guess.clicked.connect(self.guess)

		# add preview buttion
		self.b_preview  = QPushButton('&Preview', self)
		self.b_preview.clicked.connect(self.preview)

		# add Fit buttion
		self.b_fit  = QPushButton('&Fit', self)
		self.b_fit.clicked.connect(self.fit)

		v_layout = QHBoxLayout()
		v_layout.addWidget(self.b_guess)
		v_layout.addWidget(self.b_preview)
		v_layout.addWidget(self.b_fit)

		self.text_edit = QTextEdit()
		self.text_edit.setStyleSheet("font-size: 11pt; font: Arial")
		self.text_edit.setPlaceholderText("Results Report")

		self.right_layout.addWidget(self.comb_func)
		self.right_layout.addLayout(open_file_layout)
		self.right_layout.addWidget(self.gauss_para_group)
		self.right_layout.addWidget(self.fermi_para_group)
		self.right_layout.addLayout(v_layout)
		self.right_layout.addWidget(self.text_edit)

	def choose_func(self):
		# print(f"here {self.comb_func.currentIndex()}")
		if self.comb_func.currentIndex() == 0:
			self.gauss_para_group.setEnabled(True)
			self.fermi_para_group.setDisabled(True)
			self.b_guess.setVisible(True)
		elif self.comb_func.currentIndex() == 1:
			self.gauss_para_group.setDisabled(True)
			self.fermi_para_group.setEnabled(True)
			self.b_guess.setVisible(False)

	def update_sigma(self):
		self.dsb_sigma.setValue(fwhm2sigma(self.dsb_fwhm.value()))
	
	def update_height(self):
		self.dsb_height.setValue(calculate_height(self.dsb_area.value(), self.dsb_sigma.value()))

	def update_meters_e(self):
		self.dsb_instr.setValue(instr_delta_e(self.dsb_beaml_e.value(), self.dsb_conv_e.value()))

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

	def guess(self):
		if self.has_data():
			if self.comb_func.currentIndex() == 0:
				self.setup_gauss_model()
				self.gauss_pars = self.gauss_model.guess(self.y0, x=self.x0)
				self.dsb_center.setValue(self.gauss_pars["center"])
				self.dsb_area.setValue(self.gauss_pars["amplitude"])
				self.dsb_fwhm.setValue(sigma2fwhm(self.gauss_pars["sigma"]))
			elif self.comb_func.currentIndex() == 1:
				self.setup_fermi_model()
				try:
					self.fermi_pars= self.fermi_model.guess(self.y0, x=self.x0)
				except NotImplementedError:
					print(f"The guee method is not implemented for model {type(self.setup_gauss_model())}")

	def preview(self):
		# preview the Gaussion peak with init parameters 
		# print("preview is clicked!")
		if self.has_data():
			if self.comb_func.currentIndex() == 0:
				self.setup_gauss_model()
				self.eval_gauss_result = self.gauss_model.eval(self.gauss_pars, x=self.x0)	
				self.plot_preview_result()
			elif self.comb_func.currentIndex() == 1:
				self.setup_fermi_model()
				self.eval_fermi_result = self.fermi_model.eval(self.fermi_pars, x=self.x0)					
				self.plot_preview_result()


	def plot_preview_result(self):
		self.clear_plot()
		if self.comb_func.currentIndex() == 0:
			self.a_top.plot(self.x0, self.y0, "o", color= "b", label="exp")
			self.a_top.plot(self.x0, self.eval_gauss_result,'r-', label="fit" )
			self.a_bot.plot(self.x0, self.eval_gauss_result-self.y0, 'g.', label='residual')
		elif self.comb_func.currentIndex() == 1:
			self.a_top.plot(self.x0, self.y0, "o", color= "b", label="exp")
			self.a_top.plot(self.x0, self.eval_fermi_result,'r-', label="fit" )
			self.a_bot.plot(self.x0, self.eval_fermi_result-self.y0, 'g.', label='residual')
		self.update_plot()

	def fit(self):
		# fit the gauss peak funcition
		# print(self.has_data())
		# print("fit is clicked!")
		if self.has_data(): 
			if self.comb_func.currentIndex() == 0:
				self.setup_gauss_model()
				self.gauss_fit()
				self.update_result_para()
				self.plot_result()
			elif self.comb_func.currentIndex() == 1:
				self.setup_fermi_model()
				self.fermi_fit()
				self.update_result_para()
				self.plot_result()

	def setup_fermi_model(self):
		self.fermi_model = CompositeModel(Model(fermi_dirac), Model(gaussian), convolve)
		self.fermi_pars = self.fermi_model.make_params()
		self.fermi_pars['amplitude'].set(self.dsb_fermi_amp.value())
		self.fermi_pars['center'].set(self.dsb_fermi_ctr.value()/1000)
		self.fermi_pars['sigma'].set(self.fermi_sigma if hasattr(self, "fermi_sigma") else 0.2)
		self.fermi_pars['tempr'].set(value=self.dsb_temp.value(), vary=False)
		# Mathmatic constraint 
		self.fermi_pars["Ef"].set(expr="center")
		self.fermi_pars.add("Height", expr="0.3989*amplitude/max(1e-12,sigma)")
		self.fermi_pars.add("FWHM", expr="2.3548*sigma")
		self.fermi_pars.add("Beamline_dE", self.dsb_beaml_e.value()/1000, vary=False)
		self.fermi_pars.add("Conv_dE",expr="FWHM")
		self.fermi_pars.add("Instrument_dE",expr="sqrt(Conv_dE**2-Beamline_dE**2)")

		
	def update_result_para(self):
		if self.comb_func.currentIndex() == 0:		
			self.dsb_center.setValue(self.gauss_results.params["center"].value)
			self.dsb_area.setValue(self.gauss_results.params["amplitude"].value)
			self.dsb_fwhm.setValue(sigma2fwhm(self.gauss_results.params["sigma"].value))
			self.dsb_chi_sqr.setValue(self.gauss_results.redchi)
		elif self.comb_func.currentIndex() == 1:
			self.dsb_fermi_amp.setValue(self.fermi_results.params["amplitude"].value)
			self.dsb_fermi_ctr.setValue(self.fermi_results.params["center"].value * 1000)
			self.dsb_conv_e.setValue(sigma2fwhm(self.fermi_results.params["sigma"].value) * 1000)
			self.fermi_heigh = calculate_height(self.fermi_results.params["amplitude"].value,
			self.fermi_results.params["sigma"].value )
			self.fermi_sigma = self.fermi_results.params["sigma"].value
			# print(self.fermi_heigh)


	def plot_result(self):
		self.clear_plot()
		if self.comb_func.currentIndex() == 0:		
			self.a_top.plot(self.x0, self.y0, "o", color= "b", label="exp")
			self.a_top.plot(self.x0, self.gauss_results.best_fit,'r-', label="fit" )
			self.a_top.fill_between(self.x0, self.gauss_results.best_fit, color="r", alpha=0.5)
			self.a_bot.plot(self.x0, self.gauss_results.residual, 'g.', label='residual')
			self.text_edit.append(timestamp())
			self.text_edit.append(self.gauss_results.fit_report())			
			# self.a_top.annotate("", xy=(0.5, 0.5), xycoords=self.a_top.transAxes)
		elif self.comb_func.currentIndex() == 1:
			self.comps = self.fermi_results.eval_components(x=self.x0)
			self.a_top.plot(self.x0, self.y0, "o", color= "b", label="exp")
			self.a_top.plot(self.x0, self.fermi_results.best_fit,'r-', label="fit" )
			self.a_top.plot(self.x0, self.comps['fermi_dirac'], 'k--', label='Fermi-Dirac component')
			self.a_top.plot(self.x0, self.comps['gaussian'], 'k-.', label='Gaussian component')
			self.a_bot.plot(self.x0, self.fermi_results.residual, 'g.', label='residual')
			self.text_edit.append(timestamp())
			self.text_edit.append(self.fermi_results.fit_report())
		self.update_plot()
	
	def setup_gauss_model(self):
		self.gauss_model = GaussianModel()
		self.gauss_pars = self.gauss_model.make_params()
		self.gauss_pars['center'].set(self.dsb_center.value())
		self.gauss_pars['sigma'].set(self.dsb_sigma.value())
		self.gauss_pars['amplitude'].set(self.dsb_area.value())

	def fermi_fit(self):
		if hasattr(self,"fermi_model"):
			self.fermi_results = self.fermi_model.fit(self.y0, self.fermi_pars, x=self.x0, nan_policy="omit")

	def gauss_fit(self, method = "leastsq"):
		if hasattr(self,"gauss_model"):
			self.gauss_results = self.gauss_model.fit(self.y0, self.gauss_pars, x=self.x0, method=method, nan_policy="omit")

			
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
