import logging
import os
# from dotenv import load_dotenv
from typing import List

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, \
    KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

print(os.getenv)
inline_back_keyboard = types.InlineKeyboardButton(text='Назад',
                                                  callback_data='Back')

currencies = ['BTC']

payments = {
    'Банковский перевод': ['Альфабанк', 'Тинькофф', 'Сбербанк'],
    'Электронные кошельки': ['Яндекс.Деньги', 'QIWI кошелёк'],
    'Наличными в банкомате': ['Cash-in Альфабанк', 'Cash-in Тинькофф']
}

API_TOKEN = ''
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
best = 'Купить'

#Главное меню
@dp.message_handler(commands=['Start', 'Help'], state="*")
async def main_menu(
        message: [types.Message, types.CallbackQuery], state: FSMContext):
    await state.finish()
    await bot.send_message(
        chat_id=message.chat.id,
        text="Привет, я Бен! Могу помочь с обменом криптовалюты.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton('Купить')],
                [KeyboardButton('Продать')],
                [KeyboardButton('Профиль')],
                [KeyboardButton('Поддержка')]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

#Назад если мы нажали назад из купить продать
@dp.callback_query_handler(text='Назад', state=['Купить', 'Продать'])
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(action=None)
    await callback.message.delete()
    await main_menu(callback.message, state)

#код если нажали купить продать
@dp.message_handler(Text(equals=['Купить', 'Продать']))
async def select_currency(message: types.Message, state: FSMContext):
    await state.update_data(action=message.text)
    await message.answer(
        text=f'Выберите валюту, которую хотите {message.text.lower()}',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=elem, callback_data=elem)]
                for elem in currencies + ['Назад']
            ]
        )
    )
    await state.set_state(message.text)

#Назад если выбрали валюту (BTC)
@dp.callback_query_handler(text='Назад', state=currencies)
async def back_to_select_currency(
        callback: types.CallbackQuery, state:FSMContext):
    await state.update_data(currency=None)
    await callback.message.edit_text(
        text=f"Выберите валюту, которую хотите "
             f"{(await state.get_data())['action'].lower()}",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text=elem, callback_data=elem)]
                for elem in currencies + ['Назад']
            ]
        )
    )
    await state.set_state((await state.get_data())['action'])

#Код если выбрали валюту (BTC)
@dp.callback_query_handler(text=currencies, state=['Купить', 'Продать'])
async def select_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(currency=callback.data)
    real_payments = list(payments.keys())
    if ((await state.get_data())['action']).__eq__('Продать'):
        real_payments.remove('Наличными в банкомате')
    await callback.message.edit_text(
        text='Выберите способ оплаты',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text=payment, callback_data=payment)]
                for payment in real_payments + ['Назад']
            ]
        )
    )
    await state.set_state(callback.data)

#Назад если ыбрали способ оплаты
@dp.callback_query_handler(text='Назад', state=list(payments.keys()))
async def back_to_select_payment(callback: types.CallbackQuery, state:FSMContext):

    await state.update_data(payment=None)
    real_payments = list(payments.keys())
    if ((await state.get_data())['action']).__eq__('Продать'):
        real_payments.remove('Наличными в банкомате')
    await callback.message.edit_text(
        text='Выберите способ оплаты',
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text=payment, callback_data=payment)]
                for payment in real_payments + ['Назад']
            ]
        )
    )
    await state.set_state((await state.get_data())['currency'])


#КОд если выбрали способ оплаты
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
                for payment in real_payments + ['Назад']
            ]
        )
    )
    await state.set_state(callback.data)


wallet=['Альфабанк', 'Тинькофф', 'Сбербанк',
    'Электронные кошельки','Яндекс.Деньги', 'QIWI кошелёк',
    'Наличными в банкомате','Cash-in Альфабанк', 'Cash-in Тинькофф']

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

#КОд если выбрали одну из wallet
@dp.callback_query_handler(text=wallet, state=list(payments.keys()))
async def select_payment_variant(
        callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(wallet=callback.data)
    #Код для продать
    if ((await state.get_data())['action']).__eq__('Продать'):
        await callback.message.edit_text(
            "Укажите номер банковской карты для получения денег")
        await state.set_state("num_card")
    #Код для купить
    if ((await state.get_data())['action']).__eq__('Купить'):
        await callback.message.edit_text(
            "Укажите точную сумму BTC, которую хотите получить на свой кошелёк. Пример 0.006489")
        await state.set_state("parser_sum")



# Парсер номера карты для продать
@dp.message_handler(state='num_card')
async def numFics(message: types.Message, state: FSMContext):
    if is_not_float(str(message.text)):
        await message.answer(
            "Номер карты неккоректен (Номер может содержать только цифры)")
        return
    if is_float(str(message.text)) and len(
            str(message.text)) != 16:  # если это флот
        await message.answer(
            "Пожалуйста, введите корректный номер карты (Неверное количество символов)")
        return
    our_num = int(message.text)
    await message.answer(
        "Укажите точную сумму продажи криптовалюты. Пример 0.006489")
    await state.update_data(num_card_for_sold=str(our_num))
    await state.set_state('parser')



# Парсер суммы для купить
@dp.message_handler(state='parser_sum')
async def sumFics(message: types.Message, state: FSMContext):
    if is_not_float(str(message.text)):
        await message.answer("Пожалуйста, введите число. Пример: 0.0000324")
        return
    our_sum = float(message.text)
    if is_float(str(message.text)) and (
            our_sum > 10 or our_sum < 0.0000000001):  # если это флот
        await message.answer(
            "Пожалуйста, введите сумму в диапазоне от 0.0000000001 до 10 BTC")
        return

    await state.update_data(sum_for_buy=str(our_sum))
    await message.answer(
        "Укажите номер электронного кошелька для зачисления BTC")
    await state.set_state('parser')  # устанвливаем статус



# функция парсера
@dp.message_handler(state='parser')
async def enter(message: types.Message, state: FSMContext):
    #await numberFics_buy(message, state)  # Вызываю функцию парсера для покупки
    await spravka(message, state)

# Парсер
async def spravka(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
    kb.add(types.InlineKeyboardButton(text="Нет", callback_data="NO"))

    if ((await state.get_data())['action']).__eq__('Продать'):
        if is_not_float(str(message.text)):
            await message.answer("Пожалуйста, введите число. Пример: 0.0000324")
            return
        our_sum = float(message.text)
        if is_float(str(message.text)) and (
                our_sum > 10 or our_sum < 0.0000000001):  # если это флот
            await message.answer(
                "Пожалуйста, введите сумму в диапазоне от 0.0000000001 до 10 BTC")
            return
        await state.update_data(sum_for_sold=str(our_sum))
        await message.answer("Сумма указана верно!")
        await message.answer('Вы хотите продать ' +(await state.get_data())['wallet'] + '\n'
                             + 'Сумма: ' + (await state.get_data())['sum_for_sold']+ '\n'
                             + 'Деньги получить на ' +  (await state.get_data())['wallet'] + '\n'
                             + 'По реквизитам: ' + (await state.get_data())['num_card_for_sold'] + '\n'
                             + 'По актуальному курсу: (-10%)\n'
                             + 'К общей выплате: 200руб\n'
                             + 'Подвтерждаете заявку и условия сделки?',
                             reply_markup=kb)
    if ((await state.get_data())['action']).__eq__('Купить'):
        if len(str(message.text)) != 34:
            await message.answer(
                f'Пожалуйста, корректно введите номер кошелька. Он должен состоять из 34 символов,\n'
                f'которые включают в себя латинские буквы(заглавные и строчные) и цифры')
            return

        await state.update_data(num_wallet=str(message.text))
        await message.answer("Кошелек указан корректно!")
        await message.answer('Вы хотите купить: ' + (await state.get_data())['currency'] + '\n'
                             + 'Сумма: ' + (await state.get_data())['sum_for_buy'] + '\n'
                             + (await state.get_data())['currency'] + ' получить на номер ' + (await state.get_data())[
                                 'num_wallet']
                             + '\n'
                             + 'По актуальному курсу (+10%)\n'
                             + 'Общая стоимость: 200руб.\n'
                             + 'Подвтерждаете условия сделки?', reply_markup=kb)
    await state.finish()



# нажатие Да
@dp.callback_query_handler(text="Yes")
async def enter_Yes(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Заявка создана, дождитесь сообщения от оператора или свяжитесь самостоятельно, "
        "что бы ускорить процесс. Доступные операторы: [BEN] Криптосервис")
    await state.finish()
    await callback.answer()


# нажатие Нет
@dp.callback_query_handler(text="NO")
async def enter_NO(callback: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Вернуться в главное меню",callback_data='back_main_menu'))
    kb.add(types.InlineKeyboardButton(text="Назад к заявке", callback_data='back_one_step'))
    await callback.message.edit_text("Возможно Вас заинтересуют другие услуги.",reply_markup=kb)



@dp.callback_query_handler(text="back_one_step")
async def enter_NO_back_one_step(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.answer()
    await state.set_state('spravka')
    #await spravka(callback.message, state)

@dp.callback_query_handler(text="back_main_menu")
async def enter_NO_back_to_mian_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await callback.message.delete()
    await main_menu(callback.message, state)




# ===============================================================ПРОФИЛЬ===========================================================================


# Кнопка профиль
@dp.message_handler(lambda message: message.text.lower() == 'профиль')
async def support(message: types.Message, state: FSMContext):
    me = await bot.get_me()
    await message.answer(f'Уважаемый @{message.from_user.username}\n'
                         f'Бонусный баланс: 0\n'
                         f'Приглашено рефералов: 0\n'
                         f'Ваша реферальная ссылка: '
                         f'https://t.me/{me.username}?start='
                         f'{message.from_user.id}\n',
                         reply_markup=types.ReplyKeyboardRemove())
    # print()
    # await state.set_state('support')


# @dp.message_handler()
# async def echo(message: types.Message, state: FSMContext):
#     await message.answer(message.text)

# Support button
# lambda message: message.text.lower() == 'поддержка'
@dp.message_handler(Text(equals='Поддержка'))
async def support(message: types.Message, state: FSMContext):
    await message.answer("Задать вопрос или сообщить о проблеме — "
                         "[BEN] Поддержка",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.set_state('support')


@dp.message_handler(state='support')
async def echo(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        selective=True,
        one_time_keyboard=True
    )
    markup.add("Купить")
    markup.add("Продать")
    markup.add("Профиль")
    markup.add("Поддержка")
    await message.answer("Сообщение направлено в поддержку",
                         reply_markup=markup)
    await state.set_state('main_menu')
    await state.finish()  # работает больше с состояниями


@dp.callback_query_handler(state='*')
async def any_callback(callback: types.CallbackQuery, state: FSMContext):
    print('No one callback handler')
    print(f"{await state.get_state()=}")
    print(f"{callback.data=}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)