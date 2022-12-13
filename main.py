import sys
import os

from PyQt6.QtCore import QDir, Qt, QUrl, QSizeF
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QMainWindow,
    QMenu,
    QGraphicsScene,
    QGraphicsView,
)

from PyQt6.QtGui import QIcon, QAction

STYLES_PATH = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'styles')


def getStyles(fileName: str):
    with open(os.path.join(STYLES_PATH, fileName), 'r', encoding='utf-8') as style:
        return '\n'.join(style.readlines())


class ControlPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.playButton = QPushButton()
        self.playButton.setText('Play')
        self.playButton.setEnabled(False)

        self.positionSlider = QSlider(Qt.Orientation.Horizontal)
        self.positionSlider.setRange(0, 0)

        self.setContentsMargins(0, 0, 0, 0)
        self.setMaximumHeight(70)

        self.controlLayout = QHBoxLayout()
        self.controlLayout.setContentsMargins(10, 10, 10, 10)
        self.controlLayout.addWidget(self.playButton)
        self.controlLayout.addWidget(self.positionSlider)

        self.setLayout(self.controlLayout)


class VideoWindow(QMainWindow):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("Видеоплеер Лёхи")
        self.isControlPanelHidden = False
        self.isFullScreen = False

        self._setupMediaPlayer()

        centralWidget = QWidget()

        self.setCentralWidget(centralWidget)
        self.controlPanel = ControlPanel()
        self.controlPanel.playButton.clicked.connect(self.triggerPlay)
        self.controlPanel.positionSlider.sliderReleased.connect(
            self._updateVideoPosition)

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.graphicsView)
        self.layout.addWidget(self.controlPanel)

        centralWidget.setLayout(self.layout)
        self.setStyleSheet(getStyles('main.qss'))
        self._resizeVideoItem()

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(
            self, "Open Movie", QDir.homePath())
        if fileName != '':
            self.mediaPlayer.setSource(QUrl.fromLocalFile(fileName))
            self.setWindowTitle(fileName)
            self.controlPanel.playButton.setEnabled(True)

    def triggerControlPanel(self):
        self.controlPanel.setVisible(self.isControlPanelHidden)
        self.isControlPanelHidden = not self.isControlPanelHidden
        self._resizeVideoItem()

    def triggerFullScreen(self):
        if self.isFullScreen:
            self.setWindowState(Qt.WindowState.WindowNoState)
            self.isFullScreen = False
        else:
            self.setWindowState(Qt.WindowState.WindowFullScreen)
            self.isFullScreen = True

        self.show()
        self._resizeVideoItem()

    def triggerPlay(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def contextMenuEvent(self, event) -> None:
        contextMenu = QMenu()

        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open video')
        openAction.triggered.connect(self.openFile)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Quit application')
        exitAction.triggered.connect(self._exit)

        triggerControlPanelText = '&Show Control Panel' if self.isControlPanelHidden \
            else '&Hide Control Panel'

        triggerControlPanelAction = QAction(triggerControlPanelText, self)
        triggerControlPanelAction.triggered.connect(self.triggerControlPanel)

        triggerFullscreenText = '&Exit FullScreen' if self.isFullScreen \
            else '&Enter FullScreen'

        fullscreenAction = QAction(triggerFullscreenText, self)
        fullscreenAction.triggered.connect(self.triggerFullScreen)

        contextMenu.addAction(openAction)
        contextMenu.addAction(exitAction)
        contextMenu.addAction(triggerControlPanelAction)
        contextMenu.addAction(fullscreenAction)

        contextMenu.exec(self.mapToGlobal(event.pos()))

    def resizeEvent(self, _) -> None:
        self._resizeVideoItem()

    def _updateVideoPosition(self):
        self.mediaPlayer.setPosition(self.controlPanel.positionSlider.value())

    def _exit(self):
        sys.exit(1)

    def _playbackStateChanged(self, _):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.controlPanel.playButton.setText('Pause')
        else:
            self.controlPanel.playButton.setText('Play')

    def _positionChanged(self, position):
        self.controlPanel.positionSlider.setValue(position)

    def _durationChanged(self, duration):
        self.controlPanel.positionSlider.setRange(0, duration)

    def _resizeVideoItem(self):
        height = self.size().height() - self.controlPanel.height() * \
            (0 if self.isControlPanelHidden else 1)
        size = QSizeF(self.size().width(), height)

        self.videoItem.setSize(size)
        self.scene.setSceneRect(0, 0, size.width(), size.height())

    def _setupMediaPlayer(self):
        self.mediaPlayer = QMediaPlayer()
        self.setMinimumHeight(300)

        self.scene = QGraphicsScene(self)
        self.graphicsView = QGraphicsView(self.scene)
        self.graphicsView.setStyleSheet(
            'background-color: black; border: none;')

        self.videoItem = QGraphicsVideoItem()
        self.scene.addItem(self.videoItem)
        self.audioOutput = QAudioOutput()
        self.audioOutput.setVolume(50)

        self.mediaPlayer.setAudioOutput(self.audioOutput)
        self.mediaPlayer.setVideoOutput(self.videoItem)
        self.mediaPlayer.playbackStateChanged.connect(
            self._playbackStateChanged)
        self.mediaPlayer.positionChanged.connect(self._positionChanged)
        self.mediaPlayer.durationChanged.connect(self._durationChanged)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoWindow()
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec())
