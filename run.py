import csv
import logging
import os.path
import sys
import xml
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.dom.minidom import parse


@dataclass
class Requisites:
    service_unit: str = 'СлЧаст'
    date_file_path: str = 'ОбщСвСч/ИдФайл/ДатаФайл'
    payer: str = 'ИнфЧаст/Плательщик'
    bank_book: str = 'ЛицСч'
    full_name: str = 'ФИО'
    address: str = 'Адрес'
    period: str = 'Период'
    total: str = 'Сумма'


def log_writer(er, e=BaseException):
    logging.error(er)
    raise e(er)


class Transformator:
    def __init__(self, file):
        self.file = file
        self.basename = os.path.basename(self.file)
        self.dirname = os.path.dirname(self.file)
        self.csv_file = os.path.join(self.dirname, self.basename.split('.')[0] + '.csv')
        self.enc = self._file_encoding(self.file)
        self.tree = ET.parse(self.file)
        self.root = self.tree.getroot()
        self.payers = []

    @property
    def file(self):
        return self.__file

    @file.setter
    def file(self, value):
        if self._file_existing(value):
            self.__file = value

    @staticmethod
    def _file_existing(value):
        if type(value) is str:
            if not Path(value).is_file():
                log_writer(f'Файл {value} не найден', FileNotFoundError)
            return True
        log_writer(f'Путь должен быть строкой', TypeError)

    @staticmethod
    def _file_encoding(file):
        '''Проверка кодировки файла'''
        try:
            return parse(file).encoding
        except:
            log_writer(f'В файле {file} строка с кодировкой отсутствует', xml.parsers.expat.ExpatError)

    @staticmethod
    def _is_file_xml(file):
        '''проверка формата файла'''
        if Path(file).suffix != '.xml':
            log_writer(f'Этот файл ({file}) невозможно обработать. Перемещен в папку "bad"', TypeError)
        return True

    def launch(self):
        '''Инициализируем преобразование файла'''
        if not self._is_file_xml(self.file):
            self._replace_file(self.dirname, 'bad', self.basename)

        logging.info('')
        logging.info(f'Начинаем процесс преобразования файла {self.file}')

        with open(self.csv_file, 'w', encoding=self.enc) as csv_file:
            csv.register_dialect("separ", delimiter=";")
            csvwriter = csv.writer(csv_file, dialect='separ')

            basename, date = self._main_info()
            for row in self.root.findall(Requisites.payer):
                Payer.id += 1
                payer = Payer(basename, date)

                period = self._element_has_text(row.find(Requisites.period))
                total = self._element_has_text(row.find(Requisites.total))

                if not self._period(period, payer.id) or not self._total(total, payer.id):
                    setattr(payer, 'correct', False)

                setattr(payer, 'bank_book', self._element_has_text(row.find(Requisites.bank_book)))
                setattr(payer, 'full_name', self._element_has_text(row.find(Requisites.full_name)))
                setattr(payer, 'address', self._element_has_text(row.find(Requisites.address)))
                setattr(payer, 'period', period)
                setattr(payer, 'total', f'{float(total):.2f}' if total else total)

                self._duplicates(payer, self.payers)
                self.payers.append(payer)

            # добавляем корректные данные в файл
            [csvwriter.writerow(payer.lst()) for payer in self.payers if payer]

        logging.info(f'Программа успешно отработала. Перемещаем файл {self.file} в архив')
        logging.info('')
        self._replace_file(self.dirname, 'arh', self.basename)

    @staticmethod
    def _element_has_text(el):
        if hasattr(el, 'text'):
            return el.text
        return ''

    @staticmethod
    def _check_date(date):
        date_error = f'Некорректный формат даты {date}, программа завершена, так как он общий на все строки'
        if type(date) is str:
            try:
                return datetime.strptime(date, '%m.%d.%Y').strftime('%d.%m.%Y')
            except ValueError:
                log_writer(date_error, ValueError)
        log_writer(date_error, TypeError)

    def _main_info(self):
        '''проверяем ключевые реквизиты, общие для всего файла'''
        main_info = []
        for row in self.root.findall(Requisites.service_unit):
            main_info.append(self.basename)
            date = self._element_has_text(row.find(Requisites.date_file_path))
            main_info.append(self._check_date(date))
        return main_info

    @staticmethod
    def _period(period, count=0):
        '''Проверяем значение периода'''
        period_error = f'Некорректное значение Периода ({period}) в строке номер {count}'
        try:
            if int(period) == 0 or len(period) != 6 or (int(period[:2]) not in range(1, 13)):
                logging.error(period_error)
                return False
            return period
        except:
            logging.error(period_error)
            return False

    @staticmethod
    def _total(total, count=0):
        '''Проверяем значение суммы'''
        total_error = f'Некорректное значение Суммы ({total}) в строке номер {count}'
        if total:
            try:
                if float(total) < 0 or ('.' in total and total[-3] != '.'):
                    logging.error(total_error)
                    return False
            except:
                logging.error(total_error)
                return False
            return total
        return total

    @staticmethod
    def _duplicates(payer, payers):
        '''Отсеиваем дубликаты по совпадению номера счета и периода'''
        for i in payers:
            if payer == i:
                payer.correct = i.correct = False
                logging.error(f'В строках {payer.id} и {i.id} дублируются данные по значениям лицевого счета и периода')

    @staticmethod
    def _create_directory(directory, folder, name):
        '''Создаем папку, если она не существует'''
        if not os.path.exists(os.path.join(directory, folder)):
            os.mkdir(os.path.join(directory, folder))
        return os.path.join(directory, folder, name)

    def _replace_file(self, directory, folder, name):
        '''Перемещаем файл'''
        os.replace(self.file, self._create_directory(directory, folder, name))


class Payer:
    id = 0

    def __init__(self, basename, date):
        self.id = Payer.id
        self.basename = basename
        self.date_file_path = date
        self.bank_book = None
        self.full_name = None
        self.address = None
        self.period = None
        self.total = None
        self.correct = True

    def __hash__(self):
        return hash((self.bank_book, self.period))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __bool__(self):
        return self.correct

    def lst(self):
        list = [self.basename, self.date_file_path, self.bank_book,
                self.full_name, self.address, self.period, self.total]
        return [i for i in list if i]


class Logger(Transformator):
    def __init__(self, file):
        super().__init__(file)
        self._log_configurate()

    def _log_configurate(self):
        log_dir_name = self._create_directory(self.dirname, 'log', 'mylog.log')

        logging.basicConfig(
            level=logging.DEBUG,
            filename=log_dir_name,
            format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
            datefmt='%d.%m.%Y %H:%M:%S',
        )


if __name__ == '__main__':
    if len(sys.argv) == 2:
        file = sys.argv[1]
        Logger(file).launch()
    else:
        error = 'Не передан аргумент при запуске программы'
        log_writer(error, AttributeError)

