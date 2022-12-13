import sys
import os

from PyQt6.QtCore import QDir, Qt, QUrl, QSizeF, QEvent, QObject
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
    QLabel,
    QComboBox
)

from PyQt6.QtGui import QIcon, QAction, QKeyEvent, QMouseEvent

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
        self.setContentsMargins(0, 0, 0, 0)
        self.setMaximumHeight(70)

        self.positionSlider = QSlider(Qt.Orientation.Horizontal)
        self.positionSlider.setRange(0, 0)

        self.volumeSlider = QSlider(Qt.Orientation.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setMaximumWidth(100)

        self.playbackSpeedComboBox = QComboBox()
        self.playbackSpeedComboBox.addItem('0.25x', 0.25)
        self.playbackSpeedComboBox.addItem('0.5x', 0.5)
        self.playbackSpeedComboBox.addItem('1x', 1)
        self.playbackSpeedComboBox.addItem('1.5x', 1.5)
        self.playbackSpeedComboBox.addItem('2x', 2)
        self.playbackSpeedComboBox.setCurrentIndex(2)

        self.controlLayout = QHBoxLayout()
        self.controlLayout.setContentsMargins(10, 10, 10, 10)
        self.controlLayout.addWidget(self.playButton)
        self.controlLayout.addWidget(self.positionSlider)
        self.controlLayout.addWidget(QLabel('Скорость воспроизведения: '))
        self.controlLayout.addWidget(self.playbackSpeedComboBox)
        self.controlLayout.addWidget(QLabel('Громкость: '))
        self.controlLayout.addWidget(self.volumeSlider)

        self.setLayout(self.controlLayout)


class VideoWindow(QMainWindow):
    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("Видеоплеер Лёхи")
        self.isControlPanelHidden = False
        self.isFullScreen = False
        self.rewindStep = 10_000
        self.volumeStep = 10
        self.controlPanelTriggerRange = 75

        centralWidget = QWidget()

        self.setCentralWidget(centralWidget)
        self.controlPanel = ControlPanel()
        self.controlPanel.playButton.clicked.connect(self.triggerPlay)
        self.controlPanel.positionSlider.sliderReleased.connect(
            self._updateVideoPosition)

        self._setupMediaPlayer()
        self.triggerControlPanel()

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
            self.playFromFile(fileName)

    def playFromFile(self, fileName: str):
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

        triggerFullscreenText = '&Exit FullScreen' if self.isFullScreen \
            else '&Enter FullScreen'

        fullscreenAction = QAction(triggerFullscreenText, self)
        fullscreenAction.triggered.connect(self.triggerFullScreen)

        contextMenu.addAction(openAction)
        contextMenu.addAction(exitAction)
        contextMenu.addAction(fullscreenAction)

        contextMenu.exec(self.mapToGlobal(event.pos()))

    def resizeEvent(self, _) -> None:
        self._resizeVideoItem()

    def setVolume(self, volume: int):
        self.audioOutput.setVolume(volume / 100)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.nativeVirtualKey()

        match key:
            # pause/play space | k
            case 32 | 75:
                self.triggerPlay()
            # rewind backward j
            case 74:
                self.mediaPlayer.setPosition(
                    max(self.mediaPlayer.position() - self.rewindStep, 0))
            # rewind forward l
            case 76:
                self.mediaPlayer.setPosition(
                    min(self.mediaPlayer.position() + self.rewindStep, self.mediaPlayer.duration()))
            # reduce playback speed ','
            case 188:
                currentIndex = self.controlPanel.playbackSpeedComboBox.currentIndex()
                self.controlPanel.playbackSpeedComboBox.setCurrentIndex(
                    max(currentIndex - 1, 0))
            # increase playback speed '.'
            case 190:
                currentIndex = self.controlPanel.playbackSpeedComboBox.currentIndex()
                self.controlPanel.playbackSpeedComboBox.setCurrentIndex(
                    min(currentIndex + 1, self.controlPanel.playbackSpeedComboBox.count() - 1))
            # trigger fullscreen f
            case 70:
                self.triggerFullScreen()
            # decrease volume u
            case 85:
                volume = self.controlPanel.volumeSlider.value()
                self.controlPanel.volumeSlider.setValue(
                    max(volume - self.volumeStep, 0))
            # decrease volume i
            case 73:
                volume = self.controlPanel.volumeSlider.value()
                self.controlPanel.volumeSlider.setValue(
                    min(volume + self.volumeStep, 100))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        position = event.scenePosition()
        positionY = self.size().height() - position.y()

        if positionY > self.controlPanel.size().height() + self.controlPanelTriggerRange \
                and not self.isControlPanelHidden:
            self.triggerControlPanel()
        elif positionY <= self.controlPanel.size().height() + self.controlPanelTriggerRange \
                and self.isControlPanelHidden:
            self.triggerControlPanel()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QMouseEvent):
            if obj is self.windowHandle():
                self.mouseMoveEvent(event)
        return False

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

    def _playbackSpeedChanged(self, index):
        self.mediaPlayer.setPlaybackRate(
            self.controlPanel.playbackSpeedComboBox.itemData(index))

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
        self.audioOutput.setVolume(1)

        self.controlPanel.volumeSlider.setValue(
            int(self.audioOutput.volume() * 100))
        self.controlPanel.volumeSlider.valueChanged.connect(self.setVolume)

        self.controlPanel.playbackSpeedComboBox.currentIndexChanged.connect(
            self._playbackSpeedChanged)

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
    FILE_PATH = sys.argv[1]
    if os.path.exists(FILE_PATH) and os.path.isfile(FILE_PATH):
        player.playFromFile(FILE_PATH)
        player.triggerPlay()
    app.installEventFilter(player)
    sys.exit(app.exec())
