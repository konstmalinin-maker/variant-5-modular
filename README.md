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


## Дополнения практики №7

`STORAGE=sqlite|json` выбирает адаптер, `DATA_PATH` задаёт путь к файлу. Например:
```bash
STORAGE=json DATA_PATH=university.json python main.py add-student "Анна"
python main.py export STUDENT_UUID plan.csv
STORAGE=sqlite python -m pytest -q --cov --cov-report=json --junitxml=junit.xml --cov-fail-under=80
STORAGE=json python -m pytest -q --cov --cov-report=json --junitxml=junit.xml --cov-fail-under=80
python scripts/check_layers.py
radon cc . -a -s
python scripts/collect_metrics.py . metrics.json
```
PowerShell: `$env:STORAGE="json"; $env:DATA_PATH="university.json"` перед запуском. Оба адаптера используют разные файлы; автоматического переноса уже созданных записей нет. Переключение — эксперимент замены механизма хранения, а не миграция данных.

CSV содержит course_id, title, credits, grade; незаполненная оценка — пустая ячейка. Формат UTF-8 BOM, экранирование через csv.writer.

CI запускает Ruff, pytest-cov ≥80%, radon, проверку архитектуры; матрица SQLite/JSON. Измеренные метрики и coverage/JUnit/HTML сохраняются артефактами. В PR бот публикует отдельную сводку для каждого backend.

Данные экспериментов и методика: docs/experiments.json и docs/metrics-method.md. Время поиска — реальный запуск rg; время изменений — автоматизированная запись файлов, без времени обдумывания и проверки. Это не измерение скорости человека.

Архитектура и C4: [docs/architecture.md](docs/architecture.md). Контейнер DI находится в src/infrastructure/di/container.py, точка сборки — src/infrastructure/bootstrap.py.

## Отчёт

[Практическая работа №7: вариант 5, все задания A–G](PR7_Отчёт_Малинин.md). Основной PDF — 8 страниц; скриншоты и сырые измерения приложены к Modular-репозиторию.
