import logging
import re
import asyncio
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.markdown import hlink, link
import time

API_TOKEN = ''
id_chat_request = 0

#storage = MemoryStorage()
storage = MongoStorage('exchange_mongo')

currencies = ['💎 BTC (Bitcoin)']

payments = {
    '1️⃣ Банковский перевод': ['Альфабанк', 'Тинькофф', 'Сбербанк'],
    '2️⃣ Электронные кошельки': ['Яндекс.Деньги', 'QIWI кошелёк'],
    '3️⃣ Наличные в банкомате': ['Cash-in Альфабанк', 'Cash-in Тинькофф']
}

wallet = ['Альфабанк', 'Тинькофф', 'Сбербанк', 'Электронные кошельки', 'Яндекс.Деньги', 'QIWI кошелёк',
          'Наличными в банкомате', 'Cash-in Альфабанк', 'Cash-in Тинькофф']

inline_back_keyboard = types.InlineKeyboardButton(text='◀️ Назад', callback_data='Back')

logging.basicConfig(level=logging.INFO)
support_link = hlink('[BEN] Крипто-Поддержка',
                     'https://t.me/benefitsar_cryptosupport')
support_link_1 = hlink('[BEN] Поддержка', 'https://t.me/benefitsar_support')
support_link_2 = hlink('Джони', 'https://t.me/J0ni88')

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


async def check_time(message: types.Message, state: FSMContext):
    await state.update_data(time=int(time.time()))
    await asyncio.sleep(3600)
    if time.time() - (await state.get_data())['time'] > 3600:
        await bot.send_message(
            text=f'🕐 Время ожидания истелко\n'
                 f'Нажмите ' + '<b>/start</b>' + ' для запуска бота',
            chat_id=message.chat.id,
            parse_mode="HTML")
        await soft_state_finish(state)


@dp.message_handler(lambda message: message.chat.id != message.from_user.id)
async def chats_handler(message: types.Message):
    if message.chat.id == id_chat_request:
        if 'reply_to_message' in message:
            user_id = int(re.findall(r"id: (\d+)",
                                 message.reply_to_message.text)[0])
            await bot.send_message(
                chat_id=user_id,
                text=f"<b>Заявка №{(await storage.get_data(chat=user_id, user=user_id))['order_id']}:</b> \n"
                     f"Нажмите «Подтвердить» после совершения платежа "
                     f"по реквизитам и сохраните чек об оплате "
                     f"до успешного зачисления средств.\n\n"
                     f"<b>{message.text}</b>",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [types.InlineKeyboardButton(
                            text='Подтвердить',
                            callback_data='Подтвердить'
                        )]
                    ]
                ),
                parse_mode="HTML"
            )
            await message.reply(
                text='Реквизиты отправлены',
                reply=True
            )


@dp.callback_query_handler(lambda query: query.data == 'Подтвердить')
async def accept_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup())
    await callback.message.reply(
        text='Ожидайте, пожалуйста, проверки платежа менеджером',
        reply=False
    )
    await bot.send_message(
        chat_id=id_chat_request,
        text=f"Пользователь {callback.message.chat.id} подтвердил"
             f" свою заявку. Нажмите Да, если платёж прошёл или Нет, "
             f"если не прошёл",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text='Да',
                    callback_data='Да'
                ),
                    types.InlineKeyboardButton(
                        text='Нет',
                        callback_data='Нет'
                    )
                ]
            ]
        )
    )


@dp.callback_query_handler(lambda callback: callback.data == 'Да' and
                                            callback.message.chat.id !=
                                            callback.message.from_user.id)
async def accept_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='Заявка закрыта',
        reply_markup=types.InlineKeyboardMarkup()
    )
    user_id = int(re.findall(r"Пользователь (\d+)", callback.message.text)[0])
    await bot.send_message(
        chat_id=user_id,
        text='✅Менеджер успешно провёл сделку, ожидайте поступления '
             'средств.\n\n❗️Зачисление может происходить до 30 минут.'
    )
    referrer = (await storage.get_data(chat=user_id, user=user_id))['referrer']
    score = int(
        (await storage.get_data(chat=user_id, user=user_id))['pribil'] * 0.1)
    if referrer:
        await bot.send_message(chat_id=referrer,
                               text="На ваш бонусный счет зачислено: " + str(
                                   score) + " баллов.")
        score_current = (await storage.get_data(chat=referrer, user=referrer))[
            'score']
        print("score= " + str(score))
        print("score_current= " + str(score_current))
        print('sum= ' + str(score + score_current))
        await storage.update_data(chat_id=referrer, user=referrer,
                                  score=score_current + score)
    print("storage: ")
    print(await storage.get_data(chat=user_id, user=user_id))
    # await main_menu(message=callback.message, state=state)


@dp.callback_query_handler(lambda callback: callback.data == 'Нет' and
                                            callback.message.chat.id !=
                                            callback.message.from_user.id)
async def accept_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup()
    )
    user_id = int(re.findall(r"Пользователь (\d+)", callback.message.text)[0])
    await bot.send_message(
        chat_id=user_id,
        text=f'<b>Заявка №{(await storage.get_data(chat=user_id, user=user_id))["order_id"]}:</b> \n'
             f'🤷‍♂️ Возникли какие-то проблемы с платежом.\n\n'
             f'<b>Свяжитесь с поддержкой:</b>\n'+support_link_2,
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text='Подтвердить',
                    callback_data='Подтвердить'
                ),
                    types.InlineKeyboardButton(
                        text='Отменить',
                        callback_data='Отменить'
                    )]
            ]
        ),
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    # await check_time(callback.message, state)


@dp.callback_query_handler(lambda callback: callback.data == 'Отменить')
async def cancel_request(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text='Заявка отменена',
        reply_markup=InlineKeyboardMarkup()
    )
    await main_menu(message=callback.message, state=state)
    await check_time(callback.message, state)


async def soft_state_finish(state: FSMContext):
    const_fields = ['referrer', 'referrals', 'score', 'time', 'order_id','pribil']
    current_data = await state.get_data()
    clean_data = {key: current_data[key] for key in const_fields if key in current_data}  # govnocode
    await state.set_data(clean_data)
    await state.set_state(None)


@dp.message_handler(commands=['Start', 'Help'], state="*")
async def main_menu(
        message: [types.Message, types.CallbackQuery], state: FSMContext,
        message_text='❗ Добро пожаловать ❗ \n\n'
                     'Сервис обмена криптовалюты при поддержке канала @ob_nal\n\n'
                     'Выберите в меню бота, что необходимо сделать, '
                     'купить или продать. \n\n' +
                     hlink('Канал «Обнальщик»', 'https://t.me/ob_nal')):
    print("state in main_menu: ")
    print(await state.get_data())
    if 'referrer' not in (await state.get_data()):  # first /start for user
        await state.update_data(referrals=[])
        await state.update_data(score=0)
        referrer = re.findall(r"/start (\d+)", message.text)
        referrer = int(referrer[0]) if referrer else None
        await state.update_data(referrer=referrer)
        logging.info(f"New user: {message.from_user}, referral of {referrer}")
        if referrer:
            referrer_referrals = (await storage.get_data(
                chat=referrer, user=referrer))['referrals']
            referrer_referrals.append(message.from_user.id)
            await storage.update_data(chat=referrer, user=referrer,
                                      referrals=referrer_referrals)
            try:
                await bot.send_message(
                    chat_id=referrer,
                    text='По вашей реферальной ссылке присоединился '
                         'новый пользователь'
                )
            except:
                pass
    await soft_state_finish(state)
    await bot.send_message(
        chat_id=message.chat.id,
        text=message_text,
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton('💰 Купить')],
                [KeyboardButton('💸 Продать')],
                [KeyboardButton('👤 Профиль')],
                [KeyboardButton('📩 Поддержка')]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        ),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await check_time(message, state)


#,'1️⃣ Банковский перевод','2️⃣ Электронные кошельки','3️⃣ Наличные в банкомате',
# 'Альфабанк', 'Тинькофф', 'Сбербанк','Яндекс.Деньги', 'QIWI кошелёк','Cash-in Альфабанк', 'Cash-in Тинькофф','💎 BTC (Bitcoin)',
#'Да','Нет'
@dp.message_handler(text=['💰 Купить', '💸 Продать','📩 Поддержка','👤 Профиль'],
                    state='*')
async def check_main_menu(message: [types.Message, types.CallbackQuery], state: FSMContext):
    if 'referrer' not in await state.get_data() or 'referrals' not in await state.get_data():
        await main_menu(message,state)
    else:
        if message.text=='💰 Купить' or message.text=='💸 Продать':
            await select_currency(message,state)
        if message.text=='📩 Поддержка':
            await support(message,state)
        if message.text == '👤 Профиль':
            await profile(message, state)





#  Назад если мы нажали назад из купить продать
@dp.callback_query_handler(text='◀️ Назад', state=['💰 Купить', '💸 Продать'])
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action=None)
    await callback.message.delete()
    await main_menu(callback.message, state)
    await check_time(callback.message, state)


# код если нажали купить продать
@dp.message_handler(Text(equals=['💰 Купить', '💸 Продать']), state='*')
async def select_currency(message: types.Message, state: FSMContext):
    await state.update_data(action=message.text)
    text = ''
    if message.text == '💰 Купить':
        text = 'купить'
    if message.text == '💸 Продать':
        text = 'продать'
    await message.answer(
        text=f'Выберите валюту, которую хотите {text}',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=elem, callback_data=elem)]
                for elem in currencies + ['◀️ Назад']
            ]
        )
    )
    await state.set_state(message.text)
    await check_time(message, state)


#  Назад если выбрали валюту (BTC)
@dp.callback_query_handler(text='◀️ Назад', state=currencies)
async def back_to_select_currency(
        callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(currency=None)
    text = ''
    if (await state.get_data())['action'] == '💰 Купить':
        text = 'купить'
    if (await state.get_data())['action'] == '💸 Продать':
        text = 'продать'
    await callback.message.edit_text(
        text=f"Выберите валюту, которую хотите "
             f"{text}",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=elem, callback_data=elem)]
                for elem in currencies + ['◀️ Назад']
            ]
        )
    )
    await state.set_state((await state.get_data())['action'])
    await check_time(callback.message, state)


# Код если выбрали валюту (BTC)
@dp.callback_query_handler(text=currencies, state=['💰 Купить', '💸 Продать'])
async def select_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(currency=callback.data)
    response = requests.get('https://www.blockchain.com/ticker')
    value_buy = round(response.json()['RUB']['buy'] * 1.05, 2)
    value_sold = round(response.json()['RUB']['sell'] * 0.95, 2)

    pribil = value_buy - response.json()['RUB']['buy']
    await state.update_data(pribil=pribil)

    try:
        await storage.update_data(chat=(await state.get_data())['referrer'],
                                  user=(await state.get_data())['referrer'],
                                  pribil=pribil)
    except:
        pass

    await state.update_data(value_buy=value_buy)
    await state.update_data(value_sold=value_sold)
    real_payments = list(payments.keys())
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        real_payments.remove('3️⃣ Наличные в банкомате')
    await callback.message.edit_text(
        text='Выберите способ оплаты',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text=payment, callback_data=payment)]
                for payment in real_payments + ['◀️ Назад']
            ]
        )
    )
    await state.set_state(callback.data)
    await check_time(callback.message, state)


#  Назад если выбрали способ оплаты
@dp.callback_query_handler(text='◀️ Назад', state=list(payments.keys()))
async def back_to_select_payment(callback: types.CallbackQuery,
                                 state: FSMContext):
    await state.update_data(payment=None)
    real_payments = list(payments.keys())
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        real_payments.remove('3️⃣ Наличные в банкомате')
    await callback.message.edit_text(
        text='Выберите способ оплаты',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text=payment, callback_data=payment)]
                for payment in real_payments + ['◀️ Назад']
            ]
        )
    )
    await state.set_state((await state.get_data())['currency'])
    await check_time(callback.message, state)


# Код если выбрали способ оплаты
@dp.callback_query_handler(text=payments, state=currencies)
async def select_payment_variant(
        callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(payment=callback.data)
    real_payments = list(payments[callback.data])
    await callback.message.edit_reply_markup(
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text=payment, callback_data=payment)]
                for payment in real_payments + ['◀️ Назад']
            ]
        )
    )
    await state.set_state(callback.data)
    await check_time(callback.message, state)


# проверка на не float
def is_not_float(value):
    try:
        float(value)
        return False
    except:
        return True


def is_float(value):
    try:
        float(value)
        return True
    except:
        return False


#  Назад если были в wallet
@dp.callback_query_handler(text='◀️ Назад', state='num_sum')
async def back_to_select_wallet(callback: types.CallbackQuery,
                                state: FSMContext):
    await state.update_data(wallet=None)
    real_payments = list(payments[(await state.get_data())['payment']])
    await callback.message.edit_text(
        text='Выберите способ оплаты',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text=payment, callback_data=payment)]
                for payment in real_payments + ['◀️ Назад']
            ]
        )
    )
    await state.set_state((await state.get_data())['payment'])
    await check_time(callback.message, state)


# КОд если выбрали одну из wallet
@dp.callback_query_handler(text=wallet, state=list(payments.keys()))
async def select_payment_variant(
        callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(wallet=callback.data)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="◀️ Назад"))
    # Код для продать
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        if ((await state.get_data())['wallet']).__eq__('Яндекс.Деньги') or (
                (await state.get_data())['wallet']).__eq__('QIWI кошелёк'):
            await callback.message.edit_text(
                text='Укажите номер телефона,привязанный к электронному кошельку',
                reply_markup=kb
            )
        else:
            await callback.message.edit_text(
                text='Укажите номер банковской карты (без пробелов) для получения денег',
                reply_markup=kb)
    # Код для купить
    if ((await state.get_data())['action']).__eq__('💰 Купить'):
        await callback.message.edit_text(
            text='Укажите точную сумму в рублях, на которую хотите приобрести BTC.'
                 ' Или укажите точную сумму BTC (Bitcoin), при этом добавьте "BTC" в конце.' + '\n' +
                 'Актуальный курс: ' + str(
                (await state.get_data())['value_buy']) + ' руб',
            reply_markup=kb)
    await state.update_data(last_msg=callback.message.message_id)
    await state.set_state('num_sum')
    await check_time(callback.message, state)


#  Назад если были в парсере номера карты и суммы ()
@dp.callback_query_handler(text='◀️ Назад', state='parser')
async def back_to_select_wallet(callback: types.CallbackQuery,
                                state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="◀️ Назад"))
    await state.update_data(num_card_for_sold=None)
    await state.update_data(sum_for_buy=None)
    # Код для продать
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        if ((await state.get_data())['wallet']).__eq__('Яндекс.Деньги') or (
                (await state.get_data())['wallet']).__eq__('QIWI кошелёк'):
            await callback.message.edit_text(
                text='Укажите номер телефона,привязанный к электронному кошельку',
                reply_markup=kb)
        else:
            await callback.message.edit_text(
                text='Укажите номер банковской карты (без пробелов) для получения денег',
                reply_markup=kb)
    # Код для купить
    if ((await state.get_data())['action']).__eq__('💰 Купить'):
        await callback.message.edit_text(
            text='Укажите точную сумму в рублях, на которую хотите приобрести BTC.'
                 ' Или укажите точную сумму BTC (Bitcoin), при этом добавьте "BTC" в конце.' + '\n' +
                 'Актуальный курс: ' + str(
                (await state.get_data())['value_buy']) + ' руб',
            reply_markup=kb)
    await state.set_state('num_sum')
    await check_time(callback.message, state)


# Парсер номера карты и суммы
@dp.message_handler(state='num_sum')
async def numFics(message: types.Message, state: FSMContext):
    try:
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=(await state.get_data())['last_msg'],
            reply_markup=InlineKeyboardMarkup()
        )
    except:
        pass
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="◀️ Назад"))
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        if ((await state.get_data())['wallet']).__eq__('Яндекс.Деньги') or ((
                await state.get_data())['wallet']).__eq__('QIWI кошелёк'):
            result = re.findall(r"^\s*\+?[78]9\d{9}\s*$", message.text)
            if not result:
                await message.answer(
                    text='Неверный формат ввода телефона',
                    reply_markup=kb)
                await check_time(message, state)
                return
        else:
            if is_not_float(str(message.text)):
                await message.answer(
                    text="Номер карты неккоректен (Номер может содержать только цифры)",
                    reply_markup=kb)
                await check_time(message, state)
                return
            if is_float(str(message.text)) and len(
                    str(message.text)) != 16:  # если это флот
                await message.answer(
                    text="Пожалуйста, введите корректный номер карты (Неверное количество символов)",
                    reply_markup=kb)
                await check_time(message, state)
                return
        our_num = message.text
        await message.answer(
            text='Укажите точную сумму в рублях, на которую хотите продать BTC.'
                 ' Или укажите точную сумму BTC (Bitcoin), при этом добавьте "BTC" в конце.' + '\n' +
                 'Актуальный курс: ' + str(
                (await state.get_data())['value_sold']) + ' руб',
            reply_markup=kb)

        await state.update_data(num_card_for_sold=str(our_num))
    if ((await state.get_data())['action']).__eq__('💰 Купить'):
        string = message.text.lower()
        flag_btc = False
        if string.endswith('btc'):
            flag_btc = True
            string = string.replace('btc', '')

        if is_not_float(string):
            await message.answer(
                text=f"<b>Пожалуйста, введите число.</b>" + '\n' +
                     f"Пример 1: 0.00324 BTC\n"
                     f"Пример 2: 7500",
                reply_markup=kb,
                parse_mode='HTML')
            await check_time(message, state)
            return
        our_sum = float(string)
        print(our_sum)
        if flag_btc and (our_sum > 0.5 or our_sum < 0.00003):
            await message.answer(
                text="Пожалуйста, введите сумму в Bitcoin в диапазоне от 0.00003 до 0.5 BTC",
                reply_markup=kb)
            await check_time(message, state)
            return
        if (not flag_btc) and (our_sum > 1500000 or our_sum < 100):
            await message.answer(
                text="Пожалуйста, введите сумму в рублях в диапазоне от 100 до 1500000",
                reply_markup=kb)
            await check_time(message, state)
            return
        await state.update_data(sum_for_buy=float(our_sum))
        await message.answer(
            text="Укажите номер электронного кошелька для зачисления BTC (Bitcoin)",
            reply_markup=kb)
    await state.set_state('parser')  # устанвливаем статус
    await check_time(message, state)


# функция парсера
@dp.message_handler(state='parser')
async def enter(message: types.Message, state: FSMContext):
    await spravka(message, state)
    await check_time(message, state)


async def spravka_sold_to_operator(message: types.Message, state: FSMContext):
    user = 'username' in message.chat
    lastn = 'last_name' in message.chat
    num = (await state.get_data())['sum_for_sold']
    await bot.send_message(text=f"Заявка №{(await state.get_data())['order_id']}: " + message.chat.first_name + ' ' + (
        message.chat.last_name if lastn else '') +
                                (
                                    '\n' + 'username: @' + message.chat.username if user else '') + '\n'
                                + 'id: ' + str(message.chat.id) + '\n'
                                                                  'Продажа ' +
                                (await state.get_data())['currency'] + '\n'
                                + 'Сумма: ' + (str(format(
        round(float(num) / (await state.get_data())['value_sold'], 5),
        '.5f')) if (float(num) >= 100 and float(num) <= 1500000) else str(
        format(round(num, 5), '.5f'))) + ' BTC' + '\n'
                                + 'Деньги получить на ' +
                                (await state.get_data())['wallet'] + '\n'
                                + 'По реквизитам: ' + (await state.get_data())[
                                    'num_card_for_sold'] + '\n'
                                + 'По актуальному курсу: '
                                  f"{(await state.get_data())['value_sold']} "
                                  "рублей\n"
                                + 'К общей выплате: ' +
                                (
                                    f"{round((await state.get_data())['value_buy'] * num, 2)} рублей\n" if (
                                            float(num) > 0.00003 and float(
                                        num) <= 0.5) else str(
                                        num) + f" рублей\n"),
                           chat_id=id_chat_request)


async def spravka_buy_to_operator(message: types.Message, state: FSMContext):
    user = 'username' in message.chat
    lastn = 'last_name' in message.chat
    num = (await state.get_data())['sum_for_buy']
    await bot.send_message(text=f"Заявка №{(await state.get_data())['order_id']}: " + message.chat.first_name + ' ' + (
        message.chat.last_name if lastn else '') + (
                                    '\n' + 'username: @' + message.chat.username if user else '') + '\n'
                                + 'id: ' + str(message.chat.id) + '\n'
                                                                  'Покупка: ' +
                                (await state.get_data())['currency'] + '\n'
                                + 'Сумма: ' + (str(format(
        round(float(num) / (await state.get_data())['value_sold'], 5),
        '.5f')) if (float(num) >= 100 and float(num) <= 1500000) else str(
        format(round(num, 5), '.5f'))) + ' BTC' + '\n'
                                + (await state.get_data())['currency']
                                + ' получить на номер ' +
                                (await state.get_data())['num_wallet'] + '\n'+
                                'Прислать реквизиты на: '+(await state.get_data())['wallet']+'\n'
                                + 'По актуальному курсу: '
                                  f"{(await state.get_data())['value_buy']} "
                                  "рублей\n"
                                + 'Общая стоимость: ' +
                                (
                                    f"{round((await state.get_data())['value_buy'] * num, 2)} рублей\n" if (
                                            float(num) > 0.00003 and float(
                                        num) <= 0.5) else str(
                                        num) + f" рублей\n")
                           , chat_id=id_chat_request)


async def spravka_sold(message: types.Message, state: FSMContext,
                       to_operator=False):
    kb = types.InlineKeyboardMarkup()
    if to_operator is False:
        kb.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
        kb.add(types.InlineKeyboardButton(text="Нет", callback_data="NO"))
        num = (await state.get_data())['sum_for_sold']
    await bot.send_message(
        text=message.from_user.first_name + ', Вы хотите продать ' +
             (await state.get_data())['currency'] + '\n'
             + 'Сумма: ' + (str(format(
            float(num) / (await state.get_data())['value_sold'], '.5f')) if (
                float(num) >= 100 and float(num) <= 1500000) else str(
            format(round(num, 5), '.5f'))) + ' BTC' + '\n'
             + 'Деньги получить на ' + (await state.get_data())[
                 'wallet'] + '\n'
             + 'По реквизитам: ' + (await state.get_data())[
                 'num_card_for_sold'] + '\n'
             + 'По актуальному курсу: '
               f"{(await state.get_data())['value_sold']} "
               "рублей\n"
             + 'К общей выплате: ' +
             (
                 f"{round((await state.get_data())['value_sold'] * num, 2)} рублей\n" if (
                         float(num) > 0.00003 and float(num) <= 0.5) else str(
                     num) + f" рублей\n")
             + 'Подтверждаете заявку и условия сделки?',
        reply_markup=kb,
        chat_id=message.chat.id if not to_operator else id_chat_request)


async def spravka_buy(message: types.Message, state: FSMContext,
                      to_operator=False):
    kb = types.InlineKeyboardMarkup()
    if to_operator is False:
        kb.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
        kb.add(types.InlineKeyboardButton(text="Нет", callback_data="NO"))
    num = (await state.get_data())['sum_for_buy']
    await bot.send_message(
        text=message.from_user.first_name + ', Вы хотите купить: ' +
             (await state.get_data())['currency'] + '\n'
             + 'Сумма: ' + (str(format(
            round(float(num) / (await state.get_data())['value_sold'], 5),
            '.5f')) if (float(num) >= 100 and float(num) <= 1500000) else str(
            format(round(num, 5), '.5f'))) + ' BTC' + '\n'
             + (await state.get_data())['currency'] + ' получить на номер ' +
             (await state.get_data())[
                 'num_wallet']
             + '\n'
             + 'По актуальному курсу: '
               f"{(await state.get_data())['value_buy']} "
               f"рублей\n"
             + 'Общая стоимость: ' +
             (
                 f"{round((await state.get_data())['value_buy'] * num, 2)} рублей\n" if (
                         float(num) > 0.00003 and float(
                     num) <= 0.5) else str(num) + f" рублей\n")
             + 'Подтверждаете условия сделки?', reply_markup=kb,
        chat_id=message.chat.id if not to_operator else id_chat_request)


# Парсер
async def spravka(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="◀️ Назад", callback_data="◀️ Назад"))

    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        string = message.text.lower()
        flag_btc = False
        if string.endswith('btc'):
            flag_btc = True
            string = string.replace('btc', '')

        if is_not_float(string):
            await message.answer(
                text=f"<b>Пожалуйста, введите число.</b>" + '\n' +
                     f"Пример 1: 0.00324 BTC\n"
                     f"Пример 2: 7500",
                reply_markup=kb,
                parse_mode='HTML')
            await check_time(message, state)
            return
        our_sum = float(string)
        print(our_sum)
        if flag_btc and (our_sum > 0.5 or our_sum < 0.00003):
            await message.answer(
                text="Пожалуйста, введите сумму в Bitcoin в диапазоне от 0.00003 до 0.5 BTC",
                reply_markup=kb)
            await check_time(message, state)
            return
        if (not flag_btc) and (our_sum > 1500000 or our_sum < 100):
            await message.answer(
                text="Пожалуйста, введите сумму в рублях в диапазоне от 100 до 1500000",
                reply_markup=kb)
            await check_time(message, state)
            return
        await state.update_data(sum_for_sold=float(our_sum))
        await message.answer("Сумма указана верно!")
        await spravka_sold(message, state)
    if ((await state.get_data())['action']).__eq__('💰 Купить'):
        right_btc = re.findall(r"^[13][a-zA-Z0-9]{25,34}$", message.text)
        if right_btc:
            await state.update_data(num_wallet=str(message.text))
            # await message.answer("Кошелек указан корректно!")
            await spravka_buy(message, state)
        else:
            await message.answer(
                text=f'Пожалуйста, корректно введите номер кошелька. '
                     f'Он должен состоять из 26-35 символов,\n'
                     f'которые включают в себя цифры, латинские '
                     f'заглавные и строчные буквы',
                reply_markup=kb)
            await check_time(message, state)
            return

    await state.set_state('apply_request')


async def transfer_order(state: FSMContext):
    bot_id = (await bot.get_me())['id']
    bot_data = await storage.get_data(chat=bot_id, user=bot_id)
    if 'orders' not in bot_data:
        bot_data['orders'] = []
    bot_data['orders'].append(await state.get_data())
    await storage.update_data(chat=bot_id, user=bot_id, **bot_data)
    print("HI")
    print(await storage.get_data(chat=bot_id, user=bot_id))


async def add_order_id(state: FSMContext):
    bot_id = (await bot.get_me())['id']
    bot_data = await storage.get_data(chat=bot_id, user=bot_id)
    if 'orders' not in bot_data:
        bot_data['orders'] = []
    current_order_id = len(bot_data['orders']) + 100
    await state.update_data(order_id=current_order_id)


# нажатие Да
@dp.callback_query_handler(text="Yes", state="apply_request")
async def enter_Yes(callback: types.CallbackQuery, state: FSMContext):
    await add_order_id(state)
    await callback.message.edit_reply_markup(types.InlineKeyboardMarkup())
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        await spravka_sold_to_operator(callback.message, state)
    if ((await state.get_data())['action']).__eq__('💰 Купить'):
        await spravka_buy_to_operator(callback.message, state)
    text = f'Заявка создана, дождитесь сообщения от оператора.'
           #f'или свяжитесь самостоятельно, что бы ускорить процесс.\n\n' \
           #f'Доступные операторы: ' + support_link_2
    await transfer_order(state)
    await soft_state_finish(state)
    await callback.answer()
    print(f"XXX: {await state.get_data()}")
    await main_menu(callback.message, state, text)
    await check_time(callback.message, state)


# нажатие Нет
@dp.callback_query_handler(text="NO", state="apply_request")
async def enter_NO(callback: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Вернуться в главное меню",
                                      callback_data='back_main_menu'))
    kb.add(types.InlineKeyboardButton(text="◀️ Назад к заявке",
                                      callback_data='back_one_step'))
    await callback.message.edit_text(
        "Возможно Вас заинтересуют другие услуги.", reply_markup=kb)
    await check_time(callback.message, state)


@dp.callback_query_handler(text="back_one_step", state="*")
async def enter_NO_back_one_step(callback: types.CallbackQuery,
                                 state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    if ((await state.get_data())['action']).__eq__('💸 Продать'):
        await spravka_sold(callback.message, state)
    if ((await state.get_data())['action']).__eq__('💰 Купить'):
        await spravka_buy(callback.message, state)
    await check_time(callback.message, state)


@dp.callback_query_handler(text="back_main_menu", state="*")
async def enter_NO_back_to_mian_menu(callback: types.CallbackQuery,
                                     state: FSMContext):
    await soft_state_finish(state)
    await callback.message.delete()
    await main_menu(callback.message, state)
    await check_time(callback.message, state)


# ===============================================================ПРОФИЛЬ===========================================================================

# Кнопка профиль
@dp.message_handler(lambda message: message.text == '👤 Профиль', state='*')
async def profile(message: types.Message, state: FSMContext):
    me = await bot.get_me()
    name = message.from_user.username if 'username' in message.from_user \
        else message.from_user.first_name
    await main_menu(message, state,
                    f'Уважаемый @{name}\n'
                    f'Бонусный баланс: {(await state.get_data())["score"]}\n'
                    f'Приглашено рефералов: '
                    f'{len((await state.get_data())["referrals"])}\n'
                    f'Ваша реферальная ссылка: '
                    f'https://t.me/{me.username}?start='
                    f'{message.from_user.id}\n')
    await check_time(message, state)

    # print()
    # await state.set_state('support')


# @dp.message_handler()
# async def echo(message: types.Message, state: FSMContext):
#     await message.answer(message.text)

# Support button
@dp.message_handler(Text(equals='📩 Поддержка'), state='*')
async def support(message: types.Message, state: FSMContext):
    chat_1 = hlink(' Написать в поддержку', 'https://t.me/benefitsar_support')
    chat_2 = hlink(' Канал «Бенефициар»', 'https://t.me/benefitsar')
    chat_3 = hlink(' Пробив информации', 'https://t.me/benefitsar_probiv_bot')
    chat_4 = hlink(' Проверка на списки 550/639',
                   'https://t.me/benefitsar_639_bot')
    chat_5 = hlink(' Аресты ФССП', 'https://t.me/benefitsar_fssp_bot')
    chat_6 = hlink(' Бум НДС от 1,3%', 'https://t.me/benefitsar_nds')
    chat_7 = hlink(' Кэш от 13%', 'https://t.me/benefitsar_cash')
    await main_menu(message, state,
                    '❗️Задать вопрос или сообщить о проблеме можно поддержке проекта.' + '\n\n'
                    + '-' + chat_1 + '\n\n'
                    + '‼️ Другие сервисы:' + '\n'
                    + '-' + chat_2 + '\n'
                    + '-' + chat_3 + '\n'
                    + '-' + chat_4 + '\n'
                    + '-' + chat_5 + '\n'
                    + '-' + chat_6 + '\n'
                    + '-' + chat_7)
    await check_time(message, state)


# Support button
# lambda message: message.text.lower() == 'поддержка'
# @dp.message_handler(Text(equals='Поддержка'))
# async def support(message: types.Message, state: FSMContext):
#     await message.answer("Задать вопрос или сообщить о проблеме — "
#                          "[BEN] Поддержка",
#                          reply_markup=types.ReplyKeyboardRemove())
#     await state.set_state('support')

# @dp.message_handler(state='support')
# async def echo(message: types.Message, state: FSMContext):
#     markup = types.ReplyKeyboardMarkup(
#         resize_keyboard=True,
#         selective=True,
#         one_time_keyboard=True
#     )
#     markup.add("Купить")
#     markup.add("Продать")
#     markup.add("Профиль")
#     markup.add("Поддержка")
#     await message.answer("Сообщение направлено в поддержку",
#                          reply_markup=markup)
#     await state.set_state('main_menu')
#     await soft_state_finish(state)  # работает больше с состояниями

@dp.callback_query_handler(state='*')
async def any_callback(callback: types.CallbackQuery, state: FSMContext):
    print('No one callback handler')
    print(f"{await state.get_state()=}")
    print(f"{callback.data=}")
    # меняем клавиатуру на пустую
    await callback.message.edit_reply_markup(InlineKeyboardMarkup())
    # await bot.send_message(chat_id=id_chat_request,reply_markup=types.ReplyKeyboardRemove(),text="*")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
