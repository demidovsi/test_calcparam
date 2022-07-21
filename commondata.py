import PyQt5
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QMessageBox, QApplication)
import json
import winsound
import time


settings: QtCore.QSettings  # запоминаемые параметры программы
tform_handle = None
time_out = 0.5  # time_out для send_evt
texts = []  # тексты на разных языках
app_lang = 'ru'
with_sound = False
width_form = 1000
height_form = 600
icon_font = None

evt_change_language = -1001  # сменен язык


class StatusOperation(QtCore.QEvent):
    idType = QtCore.QEvent.registerEventType()

    def __init__(self, data):
        QtCore.QEvent.__init__(self, StatusOperation.idType)
        self.data = data

    def get_data(self):
        return self.data


def get_value_dic(user_dict, code, default):
    """
    выборка значения из словаря по ключу и ли значение по умолчанию, если ключ в словаре отсутствует
        :param user_dict: словарь
    :param code: ключ
    :param default: значение по умолчанию
    :return: значение ключа словаря или значение по умолчанию (если ключа нет)
    """
    if code in user_dict:
        return user_dict[code]
    else:
        return default


def get_text(value=None, key=None, id_text=None, first_upper=False, first_low=False, delete_lf=False):
    """
    Получение значения текста для текущего диалекта
        :param value: текст эталонный
        :param key:
        :param id_text:
        :param first_upper: первый символ должен быть на верхнем регистре
        :param first_low: первый символ должен быть на нижнем регистре
        :param delete_lf: заменять перевод строки на пробел
        :return: текст, приведенный к диалекту или эталонный текст, если в словаре трансляция эталона отсутствует
    """
    global texts
    result = value
    if key is None:
        result = get_value_dic(texts, value, value)
    elif id is not None and key in texts:
        for unit in texts[key]:
            if 'id' in unit and unit['id'] == id_text and 'text' in unit:
                result = unit['text']
                break
    if first_low:
        result = result[0].lower() + result[1:len(result)]

    if first_upper:
        result = result[0].upper() + result[1:len(result)]
    if delete_lf:
        result = result.replace('\n', ' ')
    return result


def load_texts(language_id):
    """
    Чтение текстов диалекта
    :return:
    """
    global texts
    try:
        f = open('languages//texts_' + language_id + '.json', 'rt', encoding='utf-8')  # только чтение и текстовый файл
        with f:
            texts = f.read()
            texts = json.loads(texts.replace('\n', ' '))
    except Exception as err:
        txt = f'Other error occurred: {err}'
        make_question(None, txt, 'Ошибка чтения файла', onlyok=True)


def make_question(self, txt, informative_text=None, detailed_text=None, onlyok=False):
    message_box = QMessageBox(self)
    message_box.setText(txt)
    message_box.setIcon(4)
    if informative_text:
        message_box.setWindowTitle(informative_text)
    if detailed_text:
        message_box.setDetailedText(detailed_text)
    if onlyok:
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.setDefaultButton(QMessageBox.Ok)
    else:
        message_box.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        message_box.setDefaultButton(QMessageBox.No)
    result = message_box.exec()
    return result == QMessageBox.Yes


def beep(frequency=500, duration=500):
    if with_sound:
        winsound.Beep(frequency, duration)


def show_message(self, txt, informative_text=None, detailed_text=None, onlyok=False, back_color=None):
    message_box = QMessageBox(self)
    if back_color is not None:
        message_box.setStyleSheet('background-color: ' + back_color + ';')
    message_box.setText(str(txt))
    if onlyok:
        message_box.setIcon(QMessageBox.Information)
    else:
        message_box.setIcon(QMessageBox.Question)
    if informative_text:
        message_box.setWindowTitle(informative_text)
    if detailed_text:
        message_box.setDetailedText(detailed_text)
    if onlyok:
        message_box.setStandardButtons(QMessageBox.Ok)
        message_box.setDefaultButton(QMessageBox.Ok)
    else:
        message_box.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        message_box.setDefaultButton(QMessageBox.No)
    result = message_box.exec()
    return result == QMessageBox.Yes


def get_index_row_in_table(model, value, col, value_child=''):  # model это  QStandardItemModel
    result = model.index(0, 0)
    try:
        for i in range(0, model.rowCount()):
            ind = model.index(i, col)
            if model.data(ind) == value:
                result = ind
                if value_child != '':
                    ind = model.index(i, 0)
                    item = model.itemFromIndex(ind)  # 0-го уровня заданной колонки (или 0-й колонки)
                    if item.hasChildren():  # найден 0-ой уровень и есть дети
                        for j in range(0, item.rowCount()):
                            ind = item.child(j).index()
                            if model.data(ind.sibling(ind.row(), col)) == value_child:
                                result = ind
                                break
                break
    except:
        pass
    return result


def set_width_columns(table, mas_fixed_width=[], increment=20, last_column=False):
    """
    Задание ширины колонок
        :param table: таблица
        :param mas_fixed_width: индексы колонок, для которых ширина не устанавливается по размеру
        :param increment: добавка к ширине колонки по размеру
        :param last_column: признак наличия невидимой последней колонки
        :return:
    """
    for j in range(table.model().columnCount()):
        if not (j in mas_fixed_width):  # колонка не фиксированной ширины
            table.resizeColumnToContents(j)
            w = table.header().sectionSize(j)
            table.setColumnWidth(j, w + increment)
    if last_column:
        table.setColumnWidth(table.model().columnCount() - 1, 0)
    table.header().setStretchLastSection(False)


def set_align(table, a_row, mas_fixed=[], align=QtCore.Qt.AlignRight):
    """
    установка выравнивания текста в колонках строки таблицы
        :param table: таблица
    :param a_row: строка таблицы
    :param mas_fixed: массив индексов колонок, у которых выравниевание не меняется (остается left)
    :param align: тип выравнивания QtCore.Qt.AlignRight (по умолчанию) или QtCore.Qt.AlignCenter
    :return:
    """
    if type(table) == PyQt5.QtWidgets.QTreeView:
        model = table.model()
    else:
        model = table
    if a_row is not None:
        for j in range(model.columnCount()):
            if not (j in mas_fixed):  # колонка не меняет ориентации
                ind = model.index(a_row, j)
                model.setData(ind, align, QtCore.Qt.TextAlignmentRole)


def row_only_read(row, mas_change=None, mas_read_only=None):
    """
    Установка ячеек с запретом на ввод
        :param row: - массив ячеек строки
    :param mas_change: массив номеров колонок, для которых возможна коррекция данных
    :param mas_read_only: массив номеров колонок, для которых не возможна коррекция данных
    :return:
    """
    for jj in range(0, len(row)):
        ind = row.__getitem__(jj)
        if mas_change is not None and not (jj in mas_change):  # j-ая колонка не корректируется
            ind.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        if mas_read_only is not None and jj in mas_read_only:  # j-ая колонка не корректируется
            ind.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)


def send_evt(number, form_parent, time_out_sleep=0):
    if form_parent is not None:
        evt = StatusOperation(number)
        QtCore.QCoreApplication.postEvent(form_parent, evt)
        if time_out_sleep > 0:
            time.sleep(time_out_sleep)
