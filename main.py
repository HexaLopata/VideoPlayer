import sys
import os
import enum
import random
from typing import List

from PyQt6.QtCore import QDir, Qt, QUrl, QSizeF, QSize, QEvent, QObject, QPointF, pyqtSignal
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
    QComboBox,
    QGraphicsPolygonItem,
    QListWidget,
    QListWidgetItem,
    QSizePolicy
)

from PyQt6.QtGui import QIcon, QAction, QKeyEvent, QMouseEvent, QPolygonF, QColor, QPainter

STYLES_PATH = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'styles')

ICONS_PATH = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'icons')


def getStyle(fileName: str):
    with open(os.path.join(STYLES_PATH, fileName), 'r', encoding='utf-8') as style:
        return '\n'.join(style.readlines())


def getIcon(fileName: str):
    return QIcon(os.path.join(ICONS_PATH, fileName))


class DeleteButton(QPushButton):
    ...

class MinimizeButton(QPushButton):
    ...

class VideoItem(QWidget):
    deleted=pyqtSignal(int, name='deleted')
    doubleClicked=pyqtSignal(QWidget)


    def __init__(self, item: QListWidgetItem, fileName='', parent=None) -> None:
        super().__init__(parent)
        self.item=item
        self.isPlaying=False
        self.filePath=fileName
        self.fileName=os.path.split(fileName)[1]
        self.layout=QHBoxLayout()
        self.fileNameLabel=QLabel(self.fileName)
        self.videoIconLabel = QLabel('')
        self.videoIconLabel.setMaximumSize(20, 30)
        self.videoIconLabel.setPixmap(VIDEO_ICON.pixmap(QSize(20, 20)))
        self.layout.addWidget(self.videoIconLabel)
        self.layout.addWidget(self.fileNameLabel)
        self.deleteButton=DeleteButton('×')
        self.deleteButton.clicked.connect(self.delete)
        self.deleteButton.setMaximumWidth(50)
        self.layout.addWidget(self.deleteButton)
        self.setLayout(self.layout)


    def delete(self, _):
        list=self.item.listWidget()
        count=list.count()
        items=[list.item(i) for i in range(count)]

        for i, item in enumerate(items):
            if item is self.item:
                list.takeItem(i)
                self.deleted.emit(i)
                break

    def setIsPlaying(self, value):
        if value:
            self.fileNameLabel.setText('Playing...')
        else:
            self.fileNameLabel.setText(self.fileName)
        self.isPlaying=value

    def mouseDoubleClickEvent(self, _) -> None:
        self.doubleClicked.emit(self)

class PlaylistState(enum.IntEnum):
    Shuffle=0
    RepeatOne=1
    Repeat=2

class PlayList(QWidget):
    _controlPanelHeight=40
    _isHidden=True
    _currentPlaylistIndex=0
    _prevIndex=0
    playRequested=pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.minimizeButton=MinimizeButton('')
        self.minimizeButton.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.minimizeButton.clicked.connect(self.triggerHide)
        self.playListContent=QWidget()
        self.playListContentLayout=QVBoxLayout()
        self.state=PlaylistState.Repeat

        self.controlPanel=QWidget()
        self.controlPanelLayout=QHBoxLayout()
        self.controlPanel.setMaximumHeight(self._controlPanelHeight)
        self.addButton=QPushButton(getIcon('plus.ico'), '')
        self.addButton.setIconSize(QSize(15, 15))
        self.addButton.clicked.connect(self.openNewFile)
        self.controlPanelLayout.addWidget(self.addButton)

        self.shuffleButton=QPushButton(getIcon('shuffle.ico'), '')
        self.shuffleButton.setIconSize(QSize(20, 20))
        self.repeatOneButton=QPushButton(getIcon('repeat-one.ico'), '')
        self.repeatOneButton.setIconSize(QSize(20, 20))
        self.repeatButton=QPushButton(getIcon('repeat.ico'), '')
        self.repeatButton.setIconSize(QSize(20, 20))
        self.repeatButton.setProperty('selected', True)

        self.shuffleButton.clicked.connect(self.shuffleClicked)
        self.repeatButton.clicked.connect(self.repeatClicked)
        self.repeatOneButton.clicked.connect(self.repeatOneClicked)

        self.controlPanelLayout.addWidget(self.shuffleButton)
        self.controlPanelLayout.addWidget(self.repeatOneButton)
        self.controlPanelLayout.addWidget(self.repeatButton)

        self.controlPanel.setLayout(self.controlPanelLayout)

        self.playListContentLayout.addWidget(self.controlPanel)
        self.videoList=QListWidget()

        self.playListContentLayout.addWidget(self.videoList)
        
        self.playListContent.setLayout(self.playListContentLayout)

        self.layout=QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.minimizeButton)
        self.layout.addWidget(self.playListContent)
        self.setStyleSheet(getStyle('playlist.qss'))
        self.setLayout(self.layout)
        self._isHidden=not self._isHidden
        self.triggerHide()


    def triggerHide(self):
        if self._isHidden:
            self.playListContent.setVisible(True)
            self.minimizeButton.setText('>')
        else:
            self.playListContent.setVisible(False)
            self.minimizeButton.setText('<')

        self._isHidden=not self._isHidden

    def shuffleClicked(self):
        self.repeatButton.setProperty('selected', False)
        self.repeatOneButton.setProperty('selected', False)
        self.shuffleButton.setProperty('selected', True)
        self.updateButtonStyle()
        self.state=PlaylistState.Shuffle

    def repeatClicked(self):
        self.repeatOneButton.setProperty('selected', False)
        self.shuffleButton.setProperty('selected', False)
        self.repeatButton.setProperty('selected', True)
        self.updateButtonStyle()
        self.state=PlaylistState.Repeat


    def repeatOneClicked(self):
        self.repeatButton.setProperty('selected', False)
        self.shuffleButton.setProperty('selected', False)
        self.repeatOneButton.setProperty('selected', True)
        self.updateButtonStyle()
        self.state=PlaylistState.RepeatOne

    def updateButtonStyle(self):
        self.shuffleButton.style().polish(self.shuffleButton)
        self.repeatOneButton.style().polish(self.repeatOneButton)
        self.repeatButton.style().polish(self.repeatButton)


    def openNewFile(self):
        fileName, _=QFileDialog.getOpenFileName(
            self, "Open File", QDir.homePath())
        if fileName != '':
            item=QListWidgetItem()
            self.videoList.addItem(item)
            videoItem=VideoItem(item, fileName)
            videoItem.deleted.connect(self._adjustIndex)
            videoItem.doubleClicked.connect(self.playVideoItem)
            self.videoList.setItemWidget(item, videoItem)

    def playVideoItem(self, item: VideoItem):
        count=self.videoList.count()
        videoItems=[self.videoList.itemWidget(
            self.videoList.item(i)) for i in range(count)]

        for i, videoItem in enumerate(videoItems):
            if videoItem is item:
                self.unSelectOldWidget()
                self._prevIndex=self._currentPlaylistIndex=i
                item.setIsPlaying(True)
                self.playRequested.emit(self.videoList.itemWidget(
                    self.videoList.item(i)).filePath)


    def next(self):
        count=self.videoList.count()
        if count == 0:
            return None

        videoWidgets=[self.videoList.itemWidget(
            self.videoList.item(i)) for i in range(count)]
        videoWidgets: List[VideoItem]
        videos=list(map(lambda w: w.filePath, videoWidgets))

        self.unSelectOldWidget()

        if self.state == PlaylistState.Shuffle:
            index=random.randint(0, count - 1)
            self.videoList.itemWidget(
                self.videoList.item(index)).setIsPlaying(True)
            self._currentPlaylistIndex=index
            self._prevIndex=index
            return videos[index]
        if self.state == PlaylistState.RepeatOne:
            index=self._currentPlaylistIndex % count
            self._prevIndex=index
            self.videoList.itemWidget(
                self.videoList.item(index)).setIsPlaying(True)
            return videos[index]
        if self.state == PlaylistState.Repeat:
            self._prevIndex=self._currentPlaylistIndex % count
            index=self._prevIndex
            self.videoList.itemWidget(
                self.videoList.item(index)).setIsPlaying(True)
            video=videos[self._currentPlaylistIndex]
            self._currentPlaylistIndex += 1
            self._currentPlaylistIndex %= count

            return video

    def unSelectOldWidget(self):
        count=self.videoList.count()
        currentVideoItem=self.videoList.itemWidget(
            self.videoList.item(self._prevIndex % count))
        currentVideoItem.setIsPlaying(False)

    def count(self):
        return self.videoList.count()

    def _adjustIndex(self, index):
        if index > self._currentPlaylistIndex:
            return

        self._currentPlaylistIndex=max(0, self._currentPlaylistIndex - 1)



class ControlPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.playButton=QPushButton()
        self.playButton.setIcon(getIcon('play.ico'))
        self.playButton.setIconSize(QSize(30, 30))
        self.setContentsMargins(0, 0, 0, 0)
        self.setMaximumHeight(70)

        self.positionSlider=QSlider(Qt.Orientation.Horizontal)
        self.positionSlider.setRange(0, 0)

        self.volumeSlider=QSlider(Qt.Orientation.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setMaximumWidth(100)

        self.playbackSpeedComboBox=QComboBox()
        self.playbackSpeedComboBox.addItem('0.25x', 0.25)
        self.playbackSpeedComboBox.addItem('0.5x', 0.5)
        self.playbackSpeedComboBox.addItem('1x', 1)
        self.playbackSpeedComboBox.addItem('1.5x', 1.5)
        self.playbackSpeedComboBox.addItem('2x', 2)
        self.playbackSpeedComboBox.setCurrentIndex(2)

        self.controlLayout=QHBoxLayout()
        self.controlLayout.setContentsMargins(10, 10, 10, 10)
        self.controlLayout.addWidget(self.playButton)
        self.controlLayout.addWidget(self.positionSlider)
        self.playbackSpeedLabel = QLabel('')
        self.playbackSpeedLabel.setPixmap(getIcon('speed.ico').pixmap(QSize(20, 20)))
        self.controlLayout.addWidget(self.playbackSpeedLabel)
        self.controlLayout.addWidget(self.playbackSpeedComboBox)
        self.volumeLabel = QLabel('')
        self.volumeLabel.setPixmap(getIcon('speaker.ico').pixmap(QSize(20, 20)))
        self.controlLayout.addWidget(self.volumeLabel)
        self.controlLayout.addWidget(self.volumeSlider)

        self.setLayout(self.controlLayout)


class VideoWindow(QMainWindow):
    _rewindStep=10_000
    _volumeStep=10
    _controlPanelTriggerRange=10
    _playIconWidth=100
    _playIconHeight=100
    _playIconColor=QColor(255, 255, 255, 150)
    _isControlPanelHidden=False
    _playlistWidth=400
    _videoEnded=True

    def __init__(self, parent=None):
        super(VideoWindow, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("Видеоплеер Лёхи")
        self.isFullScreen=False
        self.miniPlayIcon = getIcon('play.ico')
        self.pauseIcon = getIcon('pause.ico')

        centralWidget=QWidget()

        self.controlPanel=ControlPanel()
        self.controlPanel.playButton.clicked.connect(self.triggerPlay)
        self.controlPanel.positionSlider.sliderReleased.connect(
            self._updateVideoPosition)
        self.setCentralWidget(centralWidget)

        self._setupMediaPlayer()
        self._setupPlayIcon()

        self.playListWidget=PlayList(self)
        self.playListWidget.setMinimumWidth(self._playlistWidth)
        self.playListWidget.playRequested.connect(self.playFromFile)
        self.triggerControlPanel()

        self.layout=QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.graphicsView)
        self.layout.addWidget(self.controlPanel)

        centralWidget.setLayout(self.layout)
        self.setStyleSheet(getStyle('main.qss'))
        self._resizeVideoItem()

    def openFile(self):
        fileName, _=QFileDialog.getOpenFileName(
            self, "Open Movie", QDir.homePath())
        if fileName != '':
            self.playFromFile(fileName)

    def playFromFile(self, fileName: str):
        self.mediaPlayer.setSource(QUrl.fromLocalFile(fileName))
        self.setWindowTitle(fileName)
        self.play()

    def triggerControlPanel(self):
        self.controlPanel.setVisible(self._isControlPanelHidden)
        self._isControlPanelHidden=not self._isControlPanelHidden
        self._resizeVideoItem()
        self.playListWidget.move(
            self.size().width() - self.playListWidget.width(), 0)
        self.playListWidget.setMinimumSize(
            self.playListWidget.width(), int(self.scene.height()))
        self.playListWidget.setMaximumSize(
            self.playListWidget.width(), int(self.scene.height()))

    def triggerFullScreen(self):
        if self.isFullScreen:
            self.setWindowState(Qt.WindowState.WindowNoState)
            self.isFullScreen=False
        else:
            self.setWindowState(Qt.WindowState.WindowFullScreen)
            self.isFullScreen=True

        self.show()
        self._resizeVideoItem()

    def triggerPlay(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def play(self):
        if self.mediaPlayer.source().fileName() == '' and self.playListWidget.count() > 0:
            self._playNextFromPlaylist()

        if self.mediaPlayer.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.play()

    def pause(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()

    def contextMenuEvent(self, event) -> None:
        contextMenu=QMenu()

        openAction=QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('O')
        openAction.setStatusTip('Open video')
        openAction.triggered.connect(self.openFile)

        exitAction=QAction('&Exit', self)
        exitAction.setStatusTip('Quit application')
        exitAction.triggered.connect(self._exit)

        triggerFullscreenText='&Exit FullScreen' if self.isFullScreen else '&Enter FullScreen'

        fullscreenAction=QAction(triggerFullscreenText, self)
        fullscreenAction.setShortcut('F')
        fullscreenAction.triggered.connect(self.triggerFullScreen)

        contextMenu.addAction(openAction)
        contextMenu.addAction(fullscreenAction)
        contextMenu.addAction(exitAction)

        contextMenu.exec(self.mapToGlobal(event.pos()))

    def resizeEvent(self, _) -> None:
        self._resizeVideoItem()
        self.playListWidget.move(
            self.size().width() - self.playListWidget.width(), 0)
        self.playListWidget.setMinimumSize(
            self.playListWidget.width(), int(self.scene.height()))
        self.playListWidget.setMaximumSize(
            self.playListWidget.width(), int(self.scene.height()))

    def setVolume(self, volume: int):
        self.audioOutput.setVolume(volume / 100)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key=event.keyCombination().key()

        match key:
            # pause/play
            case Qt.Key.Key_Space | Qt.Key.Key_K:
                self.triggerPlay()
            # rewind backward
            case Qt.Key.Key_J:
                self.mediaPlayer.setPosition(
                    max(self.mediaPlayer.position() - self._rewindStep, 0))
            # rewind forward
            case Qt.Key.Key_L:
                self.mediaPlayer.setPosition(
                    min(self.mediaPlayer.position() + self._rewindStep, self.mediaPlayer.duration()))
            # reduce playback speed
            case Qt.Key.Key_Comma:
                currentIndex=self.controlPanel.playbackSpeedComboBox.currentIndex()
                self.controlPanel.playbackSpeedComboBox.setCurrentIndex(
                    max(currentIndex - 1, 0))
            # increase playback speed
            case Qt.Key.Key_Period:
                currentIndex=self.controlPanel.playbackSpeedComboBox.currentIndex()
                self.controlPanel.playbackSpeedComboBox.setCurrentIndex(
                    min(currentIndex + 1, self.controlPanel.playbackSpeedComboBox.count() - 1))
            # trigger fullscreen
            case Qt.Key.Key_F:
                self.triggerFullScreen()
            # decrease volume
            case Qt.Key.Key_U:
                volume=self.controlPanel.volumeSlider.value()
                self.controlPanel.volumeSlider.setValue(
                    max(volume - self._volumeStep, 0))
            # decrease volume
            case Qt.Key.Key_I:
                volume=self.controlPanel.volumeSlider.value()
                self.controlPanel.volumeSlider.setValue(
                    min(volume + self._volumeStep, 100))
            # open file
            case Qt.Key.Key_O:
                self.openFile()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        position=event.scenePosition()
        positionY=self.size().height() - position.y()

        if positionY > self.controlPanel.size().height() + self._controlPanelTriggerRange \
                and not self._isControlPanelHidden:
            self.triggerControlPanel()
        elif positionY <= self.controlPanel.size().height() + self._controlPanelTriggerRange \
                and self._isControlPanelHidden:
            self.triggerControlPanel()

    def mousePressEvent(self, _: QMouseEvent) -> None:
        self.triggerPlay()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if isinstance(event, QMouseEvent):
            if obj is self.windowHandle():
                self.mouseMoveEvent(event)
        return False

    def _setupPlayIcon(self):
        self.playIcon=QGraphicsPolygonItem()
        self.playIcon.setPen(Qt.GlobalColor.transparent)
        self.playIcon.setBrush(self._playIconColor)
        self.scene.addItem(self.playIcon)

    def _updateVideoPosition(self):
        self.mediaPlayer.setPosition(self.controlPanel.positionSlider.value())

    def _exit(self):
        sys.exit(1)

    def _playbackStateChanged(self, _):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.playIcon.setVisible(False)
            self.controlPanel.playButton.setIcon(self.pauseIcon)
        else:
            self.playIcon.setVisible(True)
            self.controlPanel.playButton.setIcon(self.miniPlayIcon)

        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.StoppedState and self._videoEnded:
            self._videoEnded=False
            self._playNextFromPlaylist()

    def _positionChanged(self, position):
        if position == self.mediaPlayer.duration() and position != 0:
            self._videoEnded=True
        self.controlPanel.positionSlider.setValue(position)

    def _playNextFromPlaylist(self):
        next=self.playListWidget.next()
        if next is not None:
            self.playFromFile(next)


    def _durationChanged(self, duration):
        self.controlPanel.positionSlider.setRange(0, duration)

    def _playbackSpeedChanged(self, index):
        self.mediaPlayer.setPlaybackRate(
            self.controlPanel.playbackSpeedComboBox.itemData(index))

    def _resizeVideoItem(self):
        height=self.size().height() - self.controlPanel.height() * \
            (0 if self._isControlPanelHidden else 1)
        size=QSizeF(self.size().width(), height)

        center=QPointF(size.width() // 2, size.height() // 2)

        self.playIcon.setPolygon(
            QPolygonF(
                [QPointF(center.x() - self._playIconWidth / 2, center.y() - self._playIconHeight / 2),
                 QPointF(center.x() + self._playIconWidth / 2, center.y()),
                 QPointF(center.x() - self._playIconWidth / 2, center.y() + self._playIconHeight / 2)]
            ))

        self.videoItem.setSize(size)
        self.scene.setSceneRect(0, 0, size.width(), size.height())

    def _stopIfNeed(self):
        if self.mediaPlayer.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.triggerPlay()

    def _setupMediaPlayer(self):
        self.mediaPlayer=QMediaPlayer()
        self.setMinimumHeight(300)

        self.scene=QGraphicsScene(self)
        self.graphicsView=QGraphicsView(self.scene)
        self.graphicsView.setStyleSheet(
            'background-color: black; border: none;')
        self.graphicsView.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphicsView.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.videoItem=QGraphicsVideoItem()
        self.scene.addItem(self.videoItem)
        self.audioOutput=QAudioOutput()
        self.audioOutput.setVolume(1)
        self.controlPanel.positionSlider.sliderPressed.connect(
            self._stopIfNeed)

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
    app=QApplication(sys.argv)
    player=VideoWindow()
    player.resize(640, 480)
    player.show()
    if len(sys.argv) > 1:
        FILE_PATH=sys.argv[1]
        if os.path.exists(FILE_PATH) and os.path.isfile(FILE_PATH):
            player.playFromFile(FILE_PATH)
    app.installEventFilter(player)
    VIDEO_ICON = getIcon('video.ico')

    sys.exit(app.exec())
