# Вариант №5: Университет — Modular

Малинин Константин Николаевич, М-25 ИО. Практическая работа №7.

## Функциональность
- enroll — запись студента на курс; повторная запись запрещена.
- list — список курсов и оценок студента, отсортированный по названию.
- grade — выставление/изменение целой оценки 2–5 только записанному студенту.
- gpa — средняя оценка с весом по кредитам; курсы без оценки пропускаются.
- drop — удаление записи на курс вместе с оценкой.
- add-student и add-course — подготовка справочников.

## Сущности и правила
Student(id UUID4, name 1–100); Course(id UUID4, title 1–100, credits 1–60); Grade(student_id, course_id, value 2–5 либо None до выставления).
GPA = sum(grade * credits)/sum(credits) по оценённым курсам, шкала 2–5; это не перевод в американскую шкалу 4.0. Если оценок нет, выводится понятная ошибка. ID должны совпадать полностью. Данные локальные; параллельные несогласованные записи не поддерживаются.

## Запуск
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py add-student "Иван"
python main.py add-course "Математика" 3
python main.py enroll STUDENT_UUID COURSE_UUID
python main.py grade STUDENT_UUID COURSE_UUID 5
python main.py list STUDENT_UUID
python main.py gpa STUDENT_UUID
python main.py drop STUDENT_UUID COURSE_UUID
python -m pytest -q --cov --cov-report=json --junitxml=junit.xml --cov-fail-under=80
```
Windows: `.venv\Scripts\Activate.ps1`. DATA_PATH задаёт файл SQLite, по умолчанию university.sqlite3. В Modular исходники разделены на domain/application/infrastructure/presentation; тесты в tests/. MIT License.
