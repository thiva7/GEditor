import os
import uuid
from includes import tables
import speech_recognition as sr
from PyQt5 import QtCore, QtPrintSupport
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import *
from PyQt5.QtWidgets import *
from UI import editorHelp


FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14, 18, 24, 36, 48, 64, 72, 96, 144, 288]
IMAGE_EXTENSIONS = ['.jpg', '.png', '.bmp']
HTML_EXTENSIONS = ['.htm', '.html' , '.txt']
VERSION = "1.5"

class VLine(QFrame):
    # a simple Vertical line
    def __init__(self):
        super(VLine, self).__init__()
        self.setFrameShape(self.VLine | self.Sunken)

class DialogFind(editorHelp.FindDialog):
    def __init__(self, parent=None):
        super(DialogFind, self).__init__()
        self.setupUi(self)


class VoiceWorker(QtCore.QObject):
    try:
        textChanged = QtCore.pyqtSignal(str)
        say = QtCore.pyqtSignal(str)
        GotIt = QtCore.pyqtSignal(str)
        micStatus = QtCore.pyqtSignal(str)
        @QtCore.pyqtSlot()
        def task(self):
            try:
                r = sr.Recognizer()
                m = sr.Microphone()
                self.micStatus.emit("True")
            except Exception as e:
                self.micStatus.emit(False)
            msg = "Πες κάτι..."
            self.say.emit(msg)
            with m as source:
                audio = r.listen(source)
                try:
                    value = r.recognize_google(audio, language='en')
                    newMsg = "Σε άκουσα! Αναλύω..."
                    self.GotIt.emit(newMsg)
                    self.textChanged.emit(value)
                except sr.UnknownValueError:
                    newMsg = "Κατι πήγε λαθος"
                    self.GotIt.emit(newMsg)
    except Exception as e:
        pass
        print(e)

def hexuuid():
    return uuid.uuid4().hex


def splitext(p):
    return os.path.splitext(p)[1].lower()


class TextEdit(QTextEdit):

    def canInsertFromMimeData(self, source):
        if source.hasImage():
            return True
        else:
            return super(TextEdit, self).canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        cursor = self.textCursor()
        document = self.document()

        if source.hasUrls():
            for u in source.urls():
                file_ext = splitext(str(u.toLocalFile()))
                if u.isLocalFile() and file_ext in IMAGE_EXTENSIONS:
                    image = QImage(u.toLocalFile())
                    document.addResource(QTextDocument.ImageResource, u, image)
                    cursor.insertImage(u.toLocalFile())
                else:
                    # If we hit a non-image or non-local URL break the loop and fall out
                    # to the super call & let Qt handle it
                    break
            else:
                # If all were valid images, finish here.
                return


        elif source.hasImage():
            image = source.imageData()
            uuid = hexuuid()
            document.addResource(QTextDocument.ImageResource, uuid, image)
            cursor.insertImage(uuid)
            return

        super(TextEdit, self).insertFromMimeData(source)


class myEditor(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.editor = TextEdit()
        # Setup the QTextEdit editor configuration
        self.editor.setAutoFormatting(QTextEdit.AutoAll)
        self.editor.selectionChanged.connect(self.update_format)
        # Initialize default font size.
        font = QFont('Times', 12)
        self.editor.setFont(font)
        # We need to repeat the size to init the current format.
        self.editor.setFontPointSize(12)

        self.worker = VoiceWorker()
        self.thread = QtCore.QThread()
        self.thread.start()
        self.worker.moveToThread(self.thread)
        # self.pushButton.clicked.connect(self.worker.task)
        self.worker.textChanged.connect(self.VoiceToText)
        self.worker.say.connect(self.VoiceToTextMsg)
        self.worker.GotIt.connect(self.VoiceToTextGotIt)
        self.worker.micStatus.connect(self.MicStatus)

        self.FindDialog = DialogFind()




        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = None

        layout.addWidget(self.editor)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Uncomment to disable native menubar on Mac
        # self.menuBar().setNativeMenuBar(False)

        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(25, 25))
        self.addToolBar(file_toolbar)
        file_menu = self.menuBar().addMenu("&File")

        new_file_action = QAction(QIcon(os.path.join('images/editor', 'new-document.png')), "New", self,
                                   shortcut=QKeySequence.New)
        new_file_action.setStatusTip("New")
        new_file_action.triggered.connect(self.newFile)
        file_menu.addAction(new_file_action)
        file_toolbar.addAction(new_file_action)



        open_file_action = QAction(QIcon(os.path.join('images/editor', 'folder.png')), "Open...", self , shortcut=QKeySequence.Open)
        open_file_action.setStatusTip("Open")
        open_file_action.triggered.connect(self.file_open)
        file_menu.addAction(open_file_action)
        file_toolbar.addAction(open_file_action)

        save_file_action = QAction(QIcon(os.path.join('images/editor', 'save.png')), "Save", self , shortcut=QKeySequence.Save)
        save_file_action.setStatusTip("Save ")
        # save_file_action.shortcut(shortcut=QKeySequence.Save)
        save_file_action.triggered.connect(self.file_save)
        file_menu.addAction(save_file_action)
        file_toolbar.addAction(save_file_action)

        saveas_file_action = QAction(QIcon(os.path.join('images/editor', 'saveas.png')), "Save as...", self, shortcut=QKeySequence.SaveAs)
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)
        file_menu.addAction(saveas_file_action)
        file_toolbar.addAction(saveas_file_action)

        print_action = QAction(QIcon(os.path.join('images/editor', 'printer.png')), "Print...", self, shortcut=QKeySequence.Print)
        print_action.setStatusTip("Print")
        print_action.triggered.connect(self.file_print)
        file_menu.addAction(print_action)
        file_toolbar.addAction(print_action)

        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(25, 25))
        self.addToolBar(edit_toolbar)
        edit_menu = self.menuBar().addMenu("&Edit")

        undo_action = QAction(QIcon(os.path.join('images/editor', 'undo.png')), "Undo", self)
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self.editor.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction(QIcon(os.path.join('images/editor', 'redo.png')), "Repeat", self)
        redo_action.setStatusTip("Repeat last action")
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        cut_action = QAction(QIcon(os.path.join('images/editor', 'cut.png')), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)
        edit_menu.addAction(cut_action)

        copy_action = QAction(QIcon(os.path.join('images/editor', 'copy.png')), "Copy", self)
        copy_action.setStatusTip("Cupy selected text")
        cut_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)
        edit_menu.addAction(copy_action)

        paste_action = QAction(QIcon(os.path.join('images/editor', 'paste.png')), "Paste", self)
        paste_action.setStatusTip("Paste ")
        cut_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)
        edit_menu.addAction(paste_action)



        mic_action = QAction(QIcon(os.path.join('images/editor', 'mic.png')), "Speech to Text", self)
        mic_action.setStatusTip("Speech to Text")

        edit_toolbar.addAction(mic_action)
        edit_menu.addAction(mic_action)


        addImage_action = QAction(QIcon(os.path.join('images/editor', 'image.png')), "Add Image", self)
        addImage_action.setStatusTip("Add Image")

        edit_toolbar.addAction(addImage_action)
        edit_menu.addAction(addImage_action)

        ExportPDF_action = QAction(QIcon(os.path.join('images/editor', 'pdf.png')), "Export as PDF", self)
        ExportPDF_action.setStatusTip("Export PDF")

        edit_toolbar.addAction(ExportPDF_action)
        edit_menu.addAction(ExportPDF_action)

        Table_action = QAction(QIcon(os.path.join('images/editor', 'table.png')), "Add Table...", self)
        Table_action.setStatusTip("Add Table")

        edit_toolbar.addAction(Table_action)
        edit_menu.addAction(Table_action)

        pix = QPixmap(20, 20)
        pix.fill(Qt.black)
        BBG_action = QAction(QIcon(pix), "Background Color", self)
        BBG_action.setStatusTip("Background Color")

        edit_toolbar.addAction(BBG_action)
        edit_menu.addAction(BBG_action)

        TextColor_action = QAction(QIcon(os.path.join('images/editor', 'color-text.png')), "Background Color", self)
        TextColor_action.setStatusTip("Background Color")

        edit_toolbar.addAction(TextColor_action)
        edit_menu.addAction(TextColor_action)

        select_action = QAction(QIcon(os.path.join('images/editor', 'select-all.png')), "Select All", self)
        select_action.setStatusTip("Select All")
        cut_action.setShortcut(QKeySequence.SelectAll)
        select_action.triggered.connect(self.editor.selectAll)
        edit_menu.addAction(select_action)

        edit_menu.addSeparator()

        wrap_action = QAction(QIcon(os.path.join('images', 'arrow-continue.png')), "Wrap text to window", self)
        wrap_action.setStatusTip("Toggle wrap text to window")
        wrap_action.setCheckable(True)
        wrap_action.setChecked(True)
        wrap_action.triggered.connect(self.edit_toggle_wrap)
        edit_menu.addAction(wrap_action)

        findAndReplace = QAction(QIcon(os.path.join('images', '1arrow-continue.png')), "Find / Replace", self, shortcut=Qt.CTRL + Qt.Key_F)
        findAndReplace.setStatusTip("Find / Replace")
        findAndReplace.setCheckable(True)
        findAndReplace.setChecked(True)
        findAndReplace.triggered.connect(self.OpenFindDialog)
        edit_menu.addAction(findAndReplace)

        format_toolbar = QToolBar("Format")
        format_toolbar.setIconSize(QSize(25, 25))
        self.addToolBar(format_toolbar)
        format_menu = self.menuBar().addMenu("&Format")

        # We need references to these actions/settings to update as selection changes, so attach to self.
        self.fonts = QFontComboBox()
        self.fonts.currentFontChanged.connect(self.editor.setCurrentFont)
        format_toolbar.addWidget(self.fonts)

        self.fontsize = QComboBox()
        self.fontsize.addItems([str(s) for s in FONT_SIZES])

        # Connect to the signal producing the text of the current selection. Convert the string to float
        # and set as the pointsize. We could also use the index + retrieve from FONT_SIZES.
        self.fontsize.currentIndexChanged[str].connect(lambda s: self.editor.setFontPointSize(float(s)))
        format_toolbar.addWidget(self.fontsize)

        self.comboStyle = QComboBox()
        format_toolbar.addWidget(self.comboStyle)
        self.comboStyle.addItem("Standard")
        self.comboStyle.addItem("Bullet List (Disc)")
        self.comboStyle.addItem("Bullet List (Circle)")
        self.comboStyle.addItem("Bullet List (Square)")
        self.comboStyle.addItem("Ordered List (Decimal)")
        self.comboStyle.addItem("Ordered List (Alpha lower)")
        self.comboStyle.addItem("Ordered List (Alpha upper)")
        self.comboStyle.addItem("Ordered List (Roman lower)")
        self.comboStyle.addItem("Ordered List (Roman upper)")
        self.comboStyle.activated.connect(self.textStyle)

        self.bold_action = QAction(QIcon(os.path.join('images/editor', 'bold.png')), "Bold", self, shortcut=Qt.CTRL + Qt.Key_B)
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(lambda x: self.editor.setFontWeight(QFont.Bold if x else QFont.Normal))
        format_toolbar.addAction(self.bold_action)
        format_menu.addAction(self.bold_action)

        self.italic_action = QAction(QIcon(os.path.join('images/editor', 'italic.png')), "Italic", self, shortcut=Qt.CTRL + Qt.Key_I)
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.editor.setFontItalic)
        format_toolbar.addAction(self.italic_action)
        format_menu.addAction(self.italic_action)

        self.underline_action = QAction(QIcon(os.path.join('images/editor', 'underline-text.png')), "Underline", self, shortcut=Qt.CTRL + Qt.Key_U)
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.editor.setFontUnderline)
        format_toolbar.addAction(self.underline_action)
        format_menu.addAction(self.underline_action)

        format_menu.addSeparator()

        self.alignl_action = QAction(QIcon(os.path.join('images/editor', 'left-align.png')), "Align left", self)
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignLeft))
        format_toolbar.addAction(self.alignl_action)
        format_menu.addAction(self.alignl_action)

        self.alignc_action = QAction(QIcon(os.path.join('images/editor', 'center-align.png')), "Align center", self)
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        self.alignc_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignCenter))
        format_toolbar.addAction(self.alignc_action)
        format_menu.addAction(self.alignc_action)

        self.alignr_action = QAction(QIcon(os.path.join('images/editor', 'right-align.png')), "Align right", self)
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignRight))
        format_toolbar.addAction(self.alignr_action)
        format_menu.addAction(self.alignr_action)

        self.alignj_action = QAction(QIcon(os.path.join('images', 'edit-alignment-justify.png')), "Justify", self)
        self.alignj_action.setStatusTip("Justify text")
        self.alignj_action.setCheckable(True)
        self.alignj_action.triggered.connect(lambda: self.editor.setAlignment(Qt.AlignJustify))
        format_toolbar.addAction(self.alignj_action)
        format_menu.addAction(self.alignj_action)




        format_group = QActionGroup(self)
        format_group.setExclusive(True)
        format_group.addAction(self.alignl_action)
        format_group.addAction(self.alignc_action)
        format_group.addAction(self.alignr_action)
        format_group.addAction(self.alignj_action)
        self.settings = QSettings('GEditor', 'App1')

        format_menu.addSeparator()



        # A list of all format-related widgets/actions, so we can disable/enable signals when updating.
        self._format_actions = [
            self.fonts,
            self.fontsize,
            self.bold_action,
            self.italic_action,
            self.underline_action,
            # We don't need to disable signals for alignment, as they are paragraph-wide.
        ]

        # Initialize.

        self.update_format()
        self.update_title()


        mic_action.triggered.connect(self.worker.task)
        addImage_action.triggered.connect(self.insertImage)
        ExportPDF_action.triggered.connect(self.exportPDF)
        BBG_action.triggered.connect(self.changeBGColor)
        TextColor_action.triggered.connect(self.textColor)
        Table_action.triggered.connect(tables.Table(self).show)
        # self.show()

        windowScreenGeometry = self.settings.value("windowScreenGeometryJEditor")
        windowScreenState = self.settings.value("windowScreenStateJEditor")

        if windowScreenGeometry:
            self.restoreGeometry(windowScreenGeometry)
        else:
            self.resize(1745, 1040)
        if windowScreenState:
            self.restoreState(windowScreenState)

        self.filename = ""
        self.cursor = QTextCursor()
        self.mainText = " "
        self.col = QLabel("Col 1 ")
        self.line = QLabel("Ln 1 ")
        self.versionLbl = QLabel("V" + VERSION)

        self.statusBar().addPermanentWidget(self.col)
        self.statusBar().addPermanentWidget(VLine())
        self.statusBar().addPermanentWidget(self.line)
        self.statusBar().addPermanentWidget(VLine())
        self.statusBar().addPermanentWidget(self.versionLbl)

        self.editor.cursorPositionChanged.connect(self.LineCounter)
        self.editor.cursorPositionChanged.connect(self.handleSelectionChanged)

    def handleSelectionChanged(self):
        cursor = self.editor.textCursor()
        txt = cursor.selectedText()
        self.FindDialog.lineEditFind.setText(txt)
        self.FindDialog.lineEdit_1.setText(txt)

    def LineCounter(self):
        line = self.editor.textCursor().blockNumber() + 1
        pos = self.editor.textCursor().columnNumber() + 1
        self.col.setText("Col " + str(pos))
        self.line.setText("Ln " + str(line))

    def findText(self):
        word = self.FindDialog.lineEditFind.text()
        if self.editor.find(word):
            return
        else:
            self.editor.moveCursor(QTextCursor.Start)
            if self.editor.find(word):
                return

    def replaceAll(self):
        oldtext = self.FindDialog.lineEdit_1.text()
        newtext = self.FindDialog.lineEdit_2.text()
        if not oldtext == "":
            h = self.editor.toHtml().replace(oldtext, newtext)
            self.editor.setText(h)
            self.setModified(True)
            self.statusBar().showMessage("all replaced")
        else:
            self.statusBar().showMessage("nothing to replace")

    def replaceOne(self):
        oldtext = self.FindDialog.lineEdit_1.text()
        newtext = self.FindDialog.lineEdit_2.text()
        if not oldtext == "":
            h = self.editor.toHtml().replace(oldtext, newtext, 1)
            self.editor.setText(h)
            self.setModified(True)
            self.statusBar().showMessage("one replaced")
        else:
            self.statusBar().showMessage("nothing to replace")



    def OpenFindDialog(self):
        self.FindDialog.btn_find.clicked.connect(self.findText)
        self.FindDialog.btn_replace.clicked.connect(self.replaceOne)
        self.FindDialog.btn_all.clicked.connect(self.replaceAll)
        self.FindDialog.show()

    def removeRow(self):
        cursor = self.text.textCursor()
        table = cursor.currentTable()
        cell = table.cellAt(cursor)
        table.removeRows(cell.row(), 1)

    def removeCol(self):
        cursor = self.text.textCursor()
        table = cursor.currentTable()
        cell = table.cellAt(cursor)
        table.removeColumns(cell.column(), 1)

    def insertRow(self):
        cursor = self.text.textCursor()
        table = cursor.currentTable()
        cell = table.cellAt(cursor)
        table.insertRows(cell.row(), 1)

    def insertCol(self):
        cursor = self.text.textCursor()
        table = cursor.currentTable()
        cell = table.cellAt(cursor)
        table.insertColumns(cell.column(), 1)

    def context(self, pos):
        cursor = self.text.textCursor()
        table = cursor.currentTable()

        if table:
            menu = QMenu(self)
            appendRowAction = QAction("", self)
            appendRowAction.triggered.connect(lambda: table.appendRows(1))
            appendColAction = QAction("", self)
            appendColAction.triggered.connect(lambda: table.appendColumns(1))
            removeRowAction = QAction("", self)
            removeRowAction.triggered.connect(self.removeRow)
            removeColAction = QAction("", self)
            removeColAction.triggered.connect(self.removeCol)
            insertRowAction = QAction("", self)
            insertRowAction.triggered.connect(self.insertRow)
            insertColAction = QAction("", self)
            insertColAction.triggered.connect(self.insertCol)

            mergeAction = QAction("", self)
            mergeAction.triggered.connect(lambda: table.mergeCells(cursor))
            if not cursor.hasSelection():
                mergeAction.setEnabled(False)

            splitAction = QAction("demo", self)
            cell = table.cellAt(cursor)
            if cell.rowSpan() > 1 or cell.columnSpan() > 1:
                splitAction.triggered.connect(lambda: table.splitCell(cell.row(), cell.column(), 1, 1))
            else:
                splitAction.setEnabled(False)

            menu.addAction(appendRowAction)
            menu.addAction(appendColAction)
            menu.addSeparator()
            menu.addAction(removeRowAction)
            menu.addAction(removeColAction)
            menu.addSeparator()
            menu.addAction(insertRowAction)
            menu.addAction(insertColAction)
            menu.addSeparator()
            menu.addAction(mergeAction)
            menu.addAction(splitAction)
            menu.addSeparator()

            pos = self.mapToGlobal(pos)
            menu.move(pos)
            menu.show()

        else:
            event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint())
            self.text.contextMenuEvent(event)

    def maybeSave(self):
        if not self.isModified():
            return True

        if self.filename.startswith(':/'):
            return True

        ret = QMessageBox.question(self, "Message",
                                   "<h4><p>The Doc have been modified .</p>\n" \
                                   "<p>Would you like to save changes?</p></h4>",
                                   QMessageBox.Yes | QMessageBox.Discard | QMessageBox.Cancel)
        if ret == QMessageBox.Yes:
            if self.filename == "":
                self.file_saveas()
                return False
            else:
                self.file_save()
                return True

        if ret == QMessageBox.Cancel:
            return False

        return True

    def isModified(self):
        return self.editor.document().isModified()

    def setModified(self, modified):
        self.editor.document().setModified(modified)

    def newFile(self):
        if self.maybeSave():
            self.editor.clear()
            self.editor.setPlainText(self.mainText)
            self.filename = ""

            self.editor.moveCursor(self.cursor.End)
            self.editor.textCursor().deletePreviousChar()
            self.setWindowTitle("New[*]")
            self.setModified(False)
        else:
            self.editor.clear()
            self.editor.setPlainText(self.mainText)
            self.filename = ""

            self.editor.moveCursor(self.cursor.End)
            self.editor.textCursor().deletePreviousChar()
            self.setWindowTitle("New[*]")
            self.setModified(False)


    def textStyle(self, styleIndex):
        cursor = self.editor.textCursor()
        if styleIndex:
            styleDict = {
                1: QTextListFormat.ListDisc,
                2: QTextListFormat.ListCircle,
                3: QTextListFormat.ListSquare,
                4: QTextListFormat.ListDecimal,
                5: QTextListFormat.ListLowerAlpha,
                6: QTextListFormat.ListUpperAlpha,
                7: QTextListFormat.ListLowerRoman,
                8: QTextListFormat.ListUpperRoman,
            }

            style = styleDict.get(styleIndex, QTextListFormat.ListDisc)
            cursor.beginEditBlock()
            blockFmt = cursor.blockFormat()
            listFmt = QTextListFormat()

            if cursor.currentList():
                listFmt = cursor.currentList().format()
            else:
                listFmt.setIndent(1)
                blockFmt.setIndent(0)
                cursor.setBlockFormat(blockFmt)

            listFmt.setStyle(style)
            cursor.createList(listFmt)
            cursor.endEditBlock()
        else:
            bfmt = QTextBlockFormat()
            bfmt.setObjectIndex(-1)
            cursor.mergeBlockFormat(bfmt)


    def mergeFormatOnWordOrSelection(self, format):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.WordUnderCursor)

        cursor.mergeCharFormat(format)
        self.editor.mergeCurrentCharFormat(format)

    def textColor(self):
        col = QColorDialog.getColor(self.editor.textColor(), self)
        if not col.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(col)
        self.mergeFormatOnWordOrSelection(fmt)


    def changeBGColor(self):

        all = self.editor.document().toHtml()
        bgcolor = all.partition("<body style=")[2].partition(">")[0].partition('bgcolor="')[2].partition('"')[0]
        if not bgcolor == "":
            col = QColorDialog.getColor(QColor(bgcolor), self)
            if not col.isValid():
                return
            else:
                colorname = col.name()
                new = all.replace("bgcolor=" + '"' + bgcolor + '"', "bgcolor=" + '"' + colorname + '"')
                self.editor.document().setHtml(new)
        else:
            col = QColorDialog.getColor(QColor("#FFFFFF"), self)
            if not col.isValid():
                return
            else:
                all = self.editor.document().toHtml()
                body = all.partition("<body style=")[2].partition(">")[0]
                newbody = body + "bgcolor=" + '"' + col.name() + '"'
                new = all.replace(body, newbody)
                self.editor.document().setHtml(new)


    def strippedName(self, fullFileName):
        return QFileInfo(fullFileName).fileName()

    def exportPDF(self):
        if self.editor.toPlainText() == "":
            self.statusBar().showMessage("no text")
        else:
            newname = self.strippedName(self.filename).replace(".html", ".pdf")
            fn, _ = QFileDialog.getSaveFileName(self,
                                                "PDF files (*.pdf);;PDF files (*.pdf)",
                                                (QDir.homePath() + "/PDF/" + newname))
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(fn)
            self.editor.document().print_(printer)

    def insertImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Pictures/",
                                              "Images (*.png *.PNG *.jpg *.JPG *.bmp *.BMP *.xpm *.gif *.eps)")
        if filename:
            image = QImage(filename)
            if image.isNull():
                popup = QMessageBox(QMessageBox.Critical,
                                    "Προσοχή",
                                    "Δεν επιλεχτικε καμια εικονα",
                                    QMessageBox.Ok, self)
                popup.show()
            else:
                cursor = self.editor.textCursor()
                cursor.insertImage(image, filename)


    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def update_format(self):
        """
        Update the font format toolbar/actions when a new text selection is made. This is neccessary to keep
        toolbars/etc. in sync with the current edit state.
        :return:
        """
        # Disable signals for all format widgets, so changing values here does not trigger further formatting.
        self.block_signals(self._format_actions, True)

        self.fonts.setCurrentFont(self.editor.currentFont())
        # Nasty, but we get the font-size as a float but want it was an int
        self.fontsize.setCurrentText(str(int(self.editor.fontPointSize())))

        self.italic_action.setChecked(self.editor.fontItalic())
        self.underline_action.setChecked(self.editor.fontUnderline())
        self.bold_action.setChecked(self.editor.fontWeight() == QFont.Bold)

        self.alignl_action.setChecked(self.editor.alignment() == Qt.AlignLeft)
        self.alignc_action.setChecked(self.editor.alignment() == Qt.AlignCenter)
        self.alignr_action.setChecked(self.editor.alignment() == Qt.AlignRight)
        self.alignj_action.setChecked(self.editor.alignment() == Qt.AlignJustify)

        self.block_signals(self._format_actions, False)

    def closeEvent(self, e):
        # Write window size and position to config file
        self.settings.setValue("windowScreenGeometryJEditor", self.saveGeometry())
        self.settings.setValue("windowScreenStateJEditor", self.saveState())
        self.filename = ""
        self.editor.setText("")
        e.accept()

    def MicStatus(self , status):
        self.editor.setStatusTip(status)
        return status

    def VoiceToTextGotIt(self, text):
        self.editor.setStatusTip(text)

    def VoiceToTextMsg(self, text):
        self.editor.setStatusTip(text)

    def VoiceToText(self, text):
        self.update_format()
        self.editor.setPlainText(self.editor.toPlainText() + " " + text)



    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def file_open(self, path=None):
        if self.maybeSave():
            if not path:
                path, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.homePath() + "/Dokumente/",
                                                      "RichText Files (*.htm *.html *.xhtml);; Text Files (*.txt *.csv *.py);;All Files (*.*)")
            if path:
                inFile = QFile(path)
                self.openFileOnStart(path)

    ### open File
    def openFileOnStart(self, path=None):
        if path:
            inFile = QFile(path)
            if inFile.open(QFile.ReadWrite | QFile.Text):
                data = inFile.readAll()
                codec = QTextCodec.codecForHtml(data)
                unistr = codec.toUnicode(data)

                if Qt.mightBeRichText(unistr):
                    self.editor.setHtml(unistr)
                else:
                    self.editor.setPlainText(unistr)
                self.filename = path



    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()

        text = self.editor.toHtml() if splitext(self.path) in HTML_EXTENSIONS else self.editor.toPlainText()

        try:
            with open(self.path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "",
                                              "HTML documents (*.html);;Text documents (*.txt);;All files (*.*)")

        print(path)

        if not path:
            # If dialog is cancelled, will return ''
            return

        text = self.editor.toHtml() if splitext(path) in HTML_EXTENSIONS else self.editor.toPlainText()

        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle("%s - JEditor" % (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode(1 if self.editor.lineWrapMode() == 0 else 0)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = myEditor()
    app.setWindowIcon(QIcon("images/editor/writer.png"))
    window.show()
    sys.exit(app.exec_())