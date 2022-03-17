import sys
from PyQt5.QtWidgets import QApplication
from FitWidget import FitWidget
from matplotlib import style
style.use('ggplot')

if __name__ == '__main__':
	app = QApplication(sys.argv)
	w = FitWidget()
	w.show()
	sys.exit(app.exec_())