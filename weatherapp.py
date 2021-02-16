from typing import get_args
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from mainwindow import Ui_MainWindow

from datetime import date, datetime
import json
import os
import sys
import requests
from urllib.parse import urlencode

OPENWEATHERMAP_API_KEY = 'c29dc565403b8e0337174e7fc0920dc9'



def from_ts_to_time_of_day(ts):
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%I%p").lstrip("0")


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict, dict)


class WeatherWorker(QRunnable):
    signals = WorkerSignals()
    is_interrupted = False

    def __init__(self, location):
        super(WeatherWorker, self).__init__()

        self.location = location

    @pyqtSlot()
    def run(self):
        try:
            params = dict(
                q=self.location,
                appid=OPENWEATHERMAP_API_KEY
            )

            url = "http://api.openweathermap.org/data/2.5/weather?%s&units=metric" % urlencode(params)
            r = requests.get(url)
            weather = json.loads(r.text)

            if weather["cod"] != 200:
                raise Exception(weather["message"])

            url = "http://api.openweathermap.org/data/2.5/forecast?%s&units=metric" % urlencode(params)
            r = requests.get(url)
            forecast = json.loads(r.text)

            self.signals.result.emit(weather, forecast)

            # Uncomment the lines below to save out .json files for the weather and forecast:

            # with open("weather.json", "w") as filehandle:
            #     json.dump(weather, filehandle)

            # with open("forecast.json", "w") as filehandle:
            #     json.dump(forecast, filehandle)

        except Exception as e:
            self.signals.error.emit(str(e))

        self.signals.finished.emit()



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        
        self.setupUi(self)
        self.pushButton.pressed.connect(self.update_weather)
        self.threadpool = QThreadPool()
        self.show()

        self.update_weather()


    def alert(self, message):
        alert = QMessageBox.warning(self, "Warning", message)


    def update_weather(self):
        worker = WeatherWorker(self.lineEdit.text())
        worker.signals.result.connect(self.weather_result)
        worker.signals.error.connect(self.alert)
        self.threadpool.start(worker)
    
    
    def weather_result(self, weather, forecasts):
        self.weatherLabel.setText("%s (%s)" % (
            weather["weather"][0]["main"],
            weather["weather"][0]["description"],
        ))

        self.currentTempLabel.setText(f'{weather["main"]["temp"]} °C')
        
        for n, forecast in enumerate(forecasts["list"][:5], 1):
            getattr(self, "forecastTime%d" % n).setText(from_ts_to_time_of_day(forecast["dt"]))
            self.set_weather_icon(getattr(self, "forecastIcon%d" % n), forecast["weather"])
            getattr(self, "forecastTemp%d" % n).setText("%.1f °C" % forecast["main"]["temp"])
        
        self.set_weather_icon(self.weatherIcon, weather["weather"])

    def set_weather_icon(self, label, weather):
        label.setPixmap(
            QPixmap(os.path.join("images", "%s.png" % weather[0]["icon"])
            )
        )


if __name__ == '__main__':

    app = QApplication([])
    window = MainWindow()
    app.exec_()