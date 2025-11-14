import csv
import os
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class FunnelBot:
    def __init__(self):
        self.templates_dir = Path("templates")
        self.data_file = Path("users_data.csv")
        
        # Создаем CSV файл с заголовками если его нет
        if not self.data_file.exists():
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'telegram_id', 'current_stage'])
    
    def load_template(self, stage):
        """Загружает HTML шаблон для этапа"""
        files = list(self.templates_dir.glob(f"stage{stage}_*.html"))
        if not files:
            raise FileNotFoundError(f"Template for stage {stage} not found")
        
        with open(files[0], 'r', encoding='utf-8') as f:
            return f.read()
    
    def personalize_template(self, template_html, user_name):
        """Подставляет только имя пользователя в шаблон"""
        return template_html.replace("{{name}}", user_name)
    
    def html_to_png(self, html_content, output_path, user_name):
        """Конвертирует HTML в PNG с персонализацией"""
        try:
            # Создаем изображение 1080x1080
            img = Image.new('RGB', (1080, 1080), color='#667eea')
            draw = ImageDraw.Draw(img)
            
            # Определяем этап по пути файла
            stage = 1
            if 'stage2' in str(output_path):
                stage = 2
            elif 'stage3' in str(output_path):
                stage = 3
            
            # Тексты для каждого этапа с персонализацией
            if stage == 1:
                lines = [
                    "🚀 Ты пропустил важное!",
                    "",
                    f"Привет, {user_name}!",
                    "",
                    "Каждый день упускаются огромные",
                    "возможности из-за неавтоматизированных",
                    "процессов.",
                    "",
                    "Но это можно исправить прямо сейчас!"
                ]
            elif stage == 2:
                lines = [
                    "✨ Решение для тебя!",
                    "",
                    f"{user_name}, наша платформа позволит",
                    "экономить 10+ часов в неделю",
                    "на рутинных задачах",
                    "",
                    "📈 +40% эффективности",
                    "⏱️ -10 часов/неделю",
                    "💰 ROI за 30 дней"
                ]
            else:  # stage 3
                lines = [
                    "⏰ Последний день!",
                    "",
                    f"{user_name}, у тебя есть последние",
                    "24 часа, чтобы присоединиться",
                    "к числу успешных предпринимателей",
                    "",
                    "🎁 СПЕЦИАЛЬНАЯ ЦЕНА: -50% ДО ПОЛУНОЧИ",
                    "",
                    "Осталось: 24 часа",
                    "Свободных мест осталось: 3 из 10"
                ]
            
            # Рисуем градиентный фон
            self._draw_gradient_background(draw, 1080, 1080)
            
            # Настройки шрифта
            try:
                font_large = ImageFont.truetype("arial.ttf", 48)
                font_medium = ImageFont.truetype("arial.ttf", 36)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Рисуем текст
            y_offset = 150
            for i, line in enumerate(lines):
                if not line.strip():
                    y_offset += 30
                    continue
                
                if i == 0:  # Заголовок
                    font = font_large
                    fill = '#ffd700'
                elif i == 2:  # Имя пользователя
                    font = font_medium
                    fill = '#ffffff'
                else:
                    font = font_small
                    fill = '#ffffff'
                
                # Выравнивание по центру
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (1080 - text_width) // 2
                draw.text((x, y_offset), line, font=font, fill=fill)
                y_offset += 60 if i == 0 else 40
            
            # Сохраняем изображение
            output_path.parent.mkdir(exist_ok=True)
            img.save(output_path, 'PNG')
            print(f"✓ Изображение создано: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error converting HTML to PNG: {e}")
            return None
    
    def _draw_gradient_background(self, draw, width, height):
        """Рисует градиентный фон"""
        for y in range(height):
            r = int(102 + (118 - 102) * y / height)
            g = int(126 + (75 - 126) * y / height)
            b = int(234 + (162 - 234) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    def save_user(self, user_data):
        """Сохраняет данные пользователя в CSV"""
        try:
            # Проверяем, есть ли уже пользователь
            users = []
            user_exists = False
            
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        users.append(row)
                        if row['telegram_id'] == user_data['telegram_id']:
                            user_exists = True
                            # Обновляем данные
                            row['name'] = user_data['name']
                            row['current_stage'] = user_data.get('current_stage', 1)
            except:
                pass
            
            # Если пользователь новый, добавляем его
            if not user_exists:
                users.append({
                    'name': user_data['name'],
                    'telegram_id': user_data['telegram_id'],
                    'current_stage': user_data.get('current_stage', 1)
                })
            
            # Записываем обратно в CSV
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'telegram_id', 'current_stage'])
                writer.writeheader()
                writer.writerows(users)
            
            print(f"✓ Данные пользователя {user_data['name']} сохранены")
            return True
        except Exception as e:
            print(f"✗ Ошибка сохранения данных: {e}")
            return False
    
    def get_user_stage(self, telegram_id):
        """Получает текущий этап пользователя"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['telegram_id'] == str(telegram_id):
                        return int(row.get('current_stage', 1))
        except:
            pass
        return 1
    
    def update_user_stage(self, telegram_id, stage):
        """Обновляет этап пользователя"""
        try:
            users = []
            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['telegram_id'] == str(telegram_id):
                        row['current_stage'] = stage
                    users.append(row)
            
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'telegram_id', 'current_stage'])
                writer.writeheader()
                writer.writerows(users)
        except Exception as e:
            print(f"✗ Ошибка обновления этапа: {e}")

# Инициализируем бота
bot = FunnelBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    user_data = {
        'name': user.first_name or user.username or 'Уважаемый клиент',
        'telegram_id': str(user.id),
        'current_stage': 1
    }
    
    # Сохраняем пользователя
    bot.save_user(user_data)
    
    # Отправляем первый этап
    await send_stage(update, context, 1, user_data['name'])
    
    print(f"✓ Новый пользователь: {user_data['name']} (ID: {user_data['telegram_id']})")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку 'Далее'"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    user_name = user.first_name or user.username or 'Уважаемый клиент'
    
    # Получаем текущий этап
    current_stage = bot.get_user_stage(user.id)
    
    # Переходим к следующему этапу
    next_stage = current_stage + 1
    
    if next_stage <= 3:
        # Обновляем этап в CSV
        bot.update_user_stage(user.id, next_stage)
        
        # Отправляем следующий этап
        await send_stage(update, context, next_stage, user_name)
    else:
        # Воронка завершена
        await query.edit_message_caption(
            caption="✅ Воронка завершена! Спасибо за внимание.",
            reply_markup=None
        )

async def send_stage(update: Update, context: ContextTypes.DEFAULT_TYPE, stage: int, user_name: str):
    """Отправляет этап воронки"""
    try:
        # Загружаем шаблон
        template_html = bot.load_template(stage)
        
        # Персонализируем (только имя)
        personalized_html = template_html.replace('{{name}}', user_name)
        
        # Конвертируем в PNG
        safe_name = user_name.replace(' ', '_')
        png_path = Path(f"temp/stage{stage}_{safe_name}.png")
        png_path.parent.mkdir(exist_ok=True)
        bot.html_to_png(personalized_html, png_path, user_name)
        
        # Создаем кнопку "Далее" (только если это не последний этап)
        keyboard = None
        if stage < 3:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("Далее ➡️", callback_data="next_stage")
            ]])
        
        # Отправляем фото
        with open(png_path, 'rb') as photo:
            if update.callback_query:
                # Если вызвано из кнопки, редактируем сообщение
                await update.callback_query.message.reply_photo(
                    photo=photo,
                    caption=f"Этап {stage}/3",
                    reply_markup=keyboard
                )
            else:
                # Если вызвано из команды /start
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"Этап {stage}/3",
                    reply_markup=keyboard
                )
        
        print(f"✓ Отправлен этап {stage} для {user_name}")
        
    except Exception as e:
        print(f"✗ Ошибка отправки этапа {stage} для {user_name}: {e}")
        if update.callback_query:
            await update.callback_query.message.reply_text(f"Ошибка: {e}")
        else:
            await update.message.reply_text(f"Ошибка: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    print(f"Update {update} caused error {context.error}")

def main():
    """Запуск бота"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Ошибка: BOT_TOKEN не установлен в файле .env")
        print("Пожалуйста, добавьте ваш токен бота в файл .env")
        return
    
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🚀 Бот запущен! Нажмите Ctrl+C для остановки")
    
    # Проверяем, используется ли webhook
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        # Используем webhook если указан URL
        port = int(os.getenv("PORT", 8080))
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )
    else:
        # Используем polling (рекомендуется для Render)
        app.run_polling()

if __name__ == "__main__":
    main()