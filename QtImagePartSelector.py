import os.path

try:
    from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QT_VERSION_STR, QPoint, QRect, QSize
    from PyQt5.QtGui import QImage, QPixmap, QPainterPath
    from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFileDialog, QRubberBand
except ImportError:
    raise ImportError("ImportError: Requires PyQt5")


class QtImagePartSelector(QGraphicsView):
    """
    Partly based on https://github.com/marcel-goldschen-ohm/PyQtImageViewer
    by Marcel Goldschen-Ohm, MIT license
    """

    rectSet = pyqtSignal(QRect)

    def __init__(self):
        QGraphicsView.__init__(self)

        # Image is displayed as a QPixmap in a QGraphicsScene attached to this QGraphicsView.
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Store a local handle to the scene's current image pixmap.
        self._pixmapHandle = None

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # rubber band for area selection
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBandScenePos = None # so it can be restored after resizing
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.changeRubberBand = False

        # previous mouse position during mouse drag action
        self.dragPrevMousePos = None

        self.setCursor(Qt.CrossCursor)

    def hasImage(self):
        """ Returns whether or not the scene contains an image pixmap.
        """
        return self._pixmapHandle is not None

    def clearImage(self):
        """ Removes the current image pixmap from the scene if it exists.
        """
        if self.hasImage():
            self.scene.removeItem(self._pixmapHandle)
            self._pixmapHandle = None

    def pixmap(self):
        """ Returns the scene's current image pixmap as a QPixmap, or else None if no image exists.
        :rtype: QPixmap | None
        """
        if self.hasImage():
            return self._pixmapHandle.pixmap()
        return None

    def image(self):
        """ Returns the scene's current image pixmap as a QImage, or else None if no image exists.
        :rtype: QImage | None
        """
        if self.hasImage():
            return self._pixmapHandle.pixmap().toImage()
        return None

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        self.updateRubberBandDisplay()


    def showEvent(self, event):
        self.old_center = self.mapToScene(self.rect().center())

    def setImage(self, image):
        """ Set the scene's current image pixmap to the input QImage or QPixmap.
        Raises a RuntimeError if the input image has type other than QImage or QPixmap.
        :type image: QImage | QPixmap
        """
        if type(image) is QPixmap:
            pixmap = image
        elif type(image) is QImage:
            pixmap = QPixmap.fromImage(image)
        else:
            raise RuntimeError("ImageViewer.setImage: Argument must be a QImage or QPixmap.")
        if self.hasImage():
            self._pixmapHandle.setPixmap(pixmap)
        else:
            self._pixmapHandle = self.scene.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))  # Set scene size to image size.



    def loadImageFromFile(self, fileName=""):
        """ Load an image from file.
        Without any arguments, loadImageFromFile() will popup a file dialog to choose the image file.
        With a fileName argument, loadImageFromFile(fileName) will attempt to load the specified image file directly.
        """
        if len(fileName) == 0:
            fileName, dummy = QFileDialog.getOpenFileName(self, "Open image file.")
        if len(fileName) and os.path.isfile(fileName):
            image = QImage(fileName)
            self.setImage(image)

    def mousePressEvent(self, event):
        """ Start creation of rubber band
        """
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBandScenePos = self.mapToScene(self.rubberBand.geometry())

            self.rubberBand.show()
            self.changeRubberBand = True
        elif event.button() == Qt.MidButton:
            self.setCursor(Qt.ClosedHandCursor)
            self.dragPrevMousePos = event.pos()

        QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if self.changeRubberBand:
            # update rubber
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
            self.rubberBandScenePos = self.mapToScene(self.rubberBand.geometry())
        if event.buttons() & Qt.MidButton:
            # drag image
            offset = self.dragPrevMousePos - event.pos()
            self.dragPrevMousePos = event.pos()

            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + offset.y())
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + offset.x())
            self.updateRubberBandDisplay()

        QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Emit rubber band size
            self.changeRubberBand = False
            self.rectSet.emit(self.rubberBandScenePos.boundingRect().toAlignedRect())
        elif event.button() == Qt.MiddleButton:
            self.setCursor(Qt.CrossCursor)

        QGraphicsView.mouseReleaseEvent(self, event)

    def updateRubberBandDisplay(self):
        if self.rubberBandScenePos is not None:
            self.rubberBand.setGeometry(self.mapFromScene(self.rubberBandScenePos).boundingRect())

    def wheelEvent(self, event):
        # Zoom Factor
        zoomInFactor = 1.1
        zoomOutFactor = 1 / zoomInFactor

        # Set Anchors
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)

        # Save the scene pos
        oldPos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.scale(zoomFactor, zoomFactor)

        # Get the new position
        newPos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())

        self.updateRubberBandDisplay()