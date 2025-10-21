🥐 Макар Макарыч | Каталог + Картинки + Умные ответы (LLM, опционально)

Папки и файлы:
- bot.py — основной код бота (polling)
- messages.json — тексты обучения
- price.json — прайс/каталог (редактируйте цены, описания, имена файлов картинок)
- media/ — сюда положите картинки (имена должны совпадать с полем "image" в price.json)
- README_v2.txt — эта инструкция

Шаг 1. Папка и файлы
1) Создайте папку проекта (например, Desktop/makar_bot) и поместите туда bot.py, messages.json, price.json.
2) Создайте подпапку media и положите туда фотографии:
   croissant.jpg, croissant_choco.jpg, sinarol.jpg, baba.jpg, brioche.jpg, bread_white.jpg, bread_multigrain.jpg
   (имена можно менять, но тогда правьте их в price.json)

Шаг 2. Зависимости
pip install python-telegram-bot==21.6
(Опционально, для LLM-ответов)
pip install openai

Шаг 3. Токены/ключи
Вариант А (в коде, быстро для теста): откройте bot.py и вставьте TELEGRAM_TOKEN в строку token = "..."
Вариант B (безопасно через переменные окружения):
Windows:
  set TELEGRAM_TOKEN=ВАШ_ТОКЕН
  set OPENAI_API_KEY=ВАШ_OPENAI_КЛЮЧ    (необязательно)
macOS/Linux:
  export TELEGRAM_TOKEN=ВАШ_ТОКЕН
  export OPENAI_API_KEY=ВАШ_OPENAI_API_KEY  (необязательно)

Шаг 4. Запуск
python bot.py

Шаг 5. Команды
/start — приветствие и меню
/price — показать прайс по категориям (inline-кнопки)
/catalog — то же, другой вход
/photo — пример отправки фото (заготовка)
/ask ВОПРОС — умный ответ. Если OPENAI_API_KEY НЕ задан — ответит по правилам (заготовки). Если задан — спросит LLM.

Шаг 6. Изменение прайса
Редактируйте price.json: добавляйте категории и товары, меняйте цены/описания/имена файлов картинок. 
Картинки кладите в media/. Перезапустите бота после правок.
