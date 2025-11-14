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
            # Заменяем плейсхолдеры на реальные данные
            html_content = html_content.replace("{{name}}", user_name)
            
            # Создаем изображение 1080x1080
            img = Image.new('RGB', (1080, 1080), color='white')
            draw = ImageDraw.Draw(img)
            
            # Определяем этап по пути файла
            stage = 1
            if 'stage2' in str(output_path):
                stage = 2
            elif 'stage3' in str(output_path):
                stage = 3
            
            # Цветовые схемы для каждого этапа
            if stage == 1:
                # Этап 1: Привлечение внимания (красно-оранжевый)
                bg_colors = ['#ff6b6b', '#ee5a24', '#ff9ff3']
                text_color = '#ffffff'
                accent_color = '#ffd700'
            elif stage == 2:
                # Этап 2: Решение (сине-фиолетовый)
                bg_colors = ['#667eea', '#764ba2', '#f093fb']
                text_color = '#ffffff'
                accent_color = '#00d2d3'
            else:  # stage 3
                # Этап 3: Срочность (красный)
                bg_colors = ['#ff0844', '#ffb199', '#ff6b6b']
                text_color = '#ffffff'
                accent_color = '#fff200'
            
            # Рисуем градиентный фон
            self._draw_advanced_gradient(draw, 1080, 1080, bg_colors)
            
            # Настройки шрифта
            try:
                # Пытаемся загрузить шрифты
                font_emoji = ImageFont.truetype("arial.ttf", 120)
                font_title = ImageFont.truetype("arial.ttf", 72)
                font_subtitle = ImageFont.truetype("arial.ttf", 56)
                font_text = ImageFont.truetype("arial.ttf", 42)
                font_small = ImageFont.truetype("arial.ttf", 32)
            except:
                # Если шрифты не найдены, используем дефолтные
                font_emoji = ImageFont.load_default()
                font_title = ImageFont.load_default()
                font_subtitle = ImageFont.load_default()
                font_text = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Рисуем персонализированный контент
            if stage == 1:
                self._draw_stage1_content(draw, user_name, stage, font_emoji, font_title, font_subtitle, font_text, font_small)
            elif stage == 2:
                self._draw_stage2_content(draw, user_name, stage, font_emoji, font_title, font_subtitle, font_text, font_small)
            else:  # stage 3
                self._draw_stage3_content(draw, user_name, stage, font_emoji, font_title, font_subtitle, font_text, font_small)
            
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
    
    def _draw_advanced_gradient(self, draw, width, height, colors):
        """Рисует улучшенный градиентный фон"""
        for y in range(height):
            # Интерполяция между цветами
            ratio = y / height
            if len(colors) == 3:
                # Трехцветный градиент
                if ratio < 0.5:
                    # Переход от первого ко второму цвету
                    local_ratio = ratio * 2
                    color1 = self._hex_to_rgb(colors[0])
                    color2 = self._hex_to_rgb(colors[1])
                else:
                    # Переход от второго к третьему цвету
                    local_ratio = (ratio - 0.5) * 2
                    color1 = self._hex_to_rgb(colors[1])
                    color2 = self._hex_to_rgb(colors[2])
                
                r = int(color1[0] + (color2[0] - color1[0]) * local_ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * local_ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * local_ratio)
            else:
                # Двухцветный градиент
                color1 = self._hex_to_rgb(colors[0])
                color2 = self._hex_to_rgb(colors[1])
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    def _hex_to_rgb(self, hex_color):
        """Конвертирует hex цвет в RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _draw_stage1_content(self, draw, user_name, stage, font_emoji, font_title, font_subtitle, font_text, font_small):
        """Рисует контент для этапа 1: Привлечение внимания"""
        # Эмодзи
        emoji = "⚡"
        
        # Рисуем эмодзи
        bbox = draw.textbbox((0, 0), emoji, font=font_emoji)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 100), emoji, font=font_emoji, fill='#ffffff')
        
        # Заголовок
        title = "ТЫ ПРОПУСТИЛ\nВАЖНОЕ!"
        
        lines = title.split('\n')
        y_offset = 250
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), line, font=font_title, fill='#ffffff')
            y_offset += 80
        
        # Имя пользователя
        name_text = f"Привет, {user_name}!"
        
        bbox = draw.textbbox((0, 0), name_text, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 450), name_text, font=font_subtitle, fill='#ffd700')
        
        # Основной текст
        main_text = [
            "Каждый день упускаются",
            "ОГРОМНЫЕ ВОЗМОЖНОСТИ",
            "из-за неавтоматизированных процессов"
        ]
        
        y_offset = 550
        for line in main_text:
            bbox = draw.textbbox((0, 0), line, font=font_text)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), line, font=font_text, fill='#ffffff')
            y_offset += 50
        
        # Финальный призыв
        final_text = "🔥 НО ЭТО МОЖНО ИСПРАВИТЬ ПРЯМО СЕЙЧАС! 🔥"
        
        bbox = draw.textbbox((0, 0), final_text, font=font_text)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 750), final_text, font=font_text, fill='#ffd700')
    
    def _draw_stage2_content(self, draw, user_name, stage, font_emoji, font_title, font_subtitle, font_text, font_small):
        """Рисует контент для этапа 2: Решение"""
        # Эмодзи
        emoji = "💡"
        
        bbox = draw.textbbox((0, 0), emoji, font=font_emoji)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 100), emoji, font=font_emoji, fill='#ffffff')
        
        # Заголовок
        title = "ЕСТЬ РЕШЕНИЕ!"
        
        bbox = draw.textbbox((0, 0), title, font=font_title)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 250), title, font=font_title, fill='#ffffff')
        
        # Имя пользователя
        name_text = f"{user_name}, мы знаем как помочь"
        
        bbox = draw.textbbox((0, 0), name_text, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 350), name_text, font=font_subtitle, fill='#00d2d3')
        
        # Преимущества
        benefits = [
            "📈 +40% ЭФФЕКТИВНОСТИ",
            "⏱️ -10 ЧАСОВ/НЕДЕЛЮ",
            "💰 ROI ЗА 30 ДНЕЙ"
        ]
        
        y_offset = 450
        for benefit in benefits:
            bbox = draw.textbbox((0, 0), benefit, font=font_text)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), benefit, font=font_text, fill='#ffeb3b')
            y_offset += 60
        
        # Описание
        description = "Наша платформа позволит экономить\n10+ ЧАСОВ В НЕДЕЛЮ\nна рутинных задачах"
        
        lines = description.split('\n')
        y_offset = 650
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), line, font=font_small, fill='#ffffff')
            y_offset += 45
        
        # Финальный призыв
        final_text = "🎯 СПЕЦИАЛЬНО ДЛЯ ПРОФЕССИОНАЛОВ 🎯"
        
        bbox = draw.textbbox((0, 0), final_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 800), final_text, font=font_small, fill='#00d2d3')
    
    def _draw_stage3_content(self, draw, user_name, stage, font_emoji, font_title, font_subtitle, font_text, font_small):
        """Рисует контент для этапа 3: Срочность"""
        # Эмодзи
        emoji = "🚨"
        
        bbox = draw.textbbox((0, 0), emoji, font=font_emoji)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 100), emoji, font=font_emoji, fill='#ffffff')
        
        # Заголовок
        title = "ПОСЛЕДНИЙ\nШАНС!"
        
        lines = title.split('\n')
        y_offset = 250
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), line, font=font_title, fill='#ffffff')
            y_offset += 85
        
        # Имя пользователя
        name_text = f"{user_name}, время почти вышло!"
        
        bbox = draw.textbbox((0, 0), name_text, font=font_subtitle)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 450), name_text, font=font_subtitle, fill='#fff200')
        
        # Срочность
        urgent_text = "⏰ ОСТАЛОСЬ ВСЕГО 24 ЧАСА! ⏰"
        
        bbox = draw.textbbox((0, 0), urgent_text, font=font_text)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 520), urgent_text, font=font_text, fill='#fff200')
        
        # Предложение
        offer_lines = [
            "🎁 СПЕЦИАЛЬНАЯ ЦЕНА: -50%",
            "ДО ПОЛУНОЧИ!"
        ]
        
        y_offset = 600
        for line in offer_lines:
            bbox = draw.textbbox((0, 0), line, font=font_text)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), line, font=font_text, fill='#ffffff')
            y_offset += 50
        
        # Количество мест
        spots_text = "🔥 СВОБОДНЫХ МЕСТ: 3 ИЗ 10 🔥"
        
        bbox = draw.textbbox((0, 0), spots_text, font=font_small)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        draw.text((x, 720), spots_text, font=font_small, fill='#fff200')
        
        # Финальный призыв
        final_text = "Не упусти шанс присоединиться к\nУСПЕШНЫМ ПРЕДПРИНИМАТЕЛЯМ!"
        
        lines = final_text.split('\n')
        y_offset = 800
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_small)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            draw.text((x, y_offset), line, font=font_small, fill='#fff200')
            y_offset += 50
    
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
        # Используем polling (рекомендуется для Railway)
        print("� Используем polling режим для получения обновлений")
        app.run_polling()

if __name__ == "__main__":
    main()