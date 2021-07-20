import logging
import os
# from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton



print(os.getenv)
API_TOKEN = '1814604938:AAFiMoa3as2ZkKlD90hwnzg0r5V_MZp-xGk'
logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True,one_time_keyboard=True)
    markup.add("Купить")
    markup.add("Продать")
    markup.add("Профиль")
    markup.add("Поддержка")
    await message.reply("Привет, я Бен! Могу помочь с обменом криптовалюты.",
                        reply_markup=markup)




#Кнопка поддержки
@dp.message_handler(lambda message: message.text.lower() == 'поддержка')
async def support(message: types.Message, state: FSMContext):

    await message.answer("Задать вопрос или сообщить о проблеме — "
                         "[BEN] Поддержка",
                         reply_markup=types.ReplyKeyboardRemove())
    await state.set_state('support')

#либо саппорт либо саппорт2 будет вход
@dp.message_handler(state='support')
async def echo(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True,one_time_keyboard=True)
    markup.add("Купить")
    markup.add("Продать")
    markup.add("Профиль")
    markup.add("Поддержка")
    await message.answer("Сообщение направлено в поддержку",
                         reply_markup=markup)
    await state.set_state('main_menu')
    await state.finish() #работает больше с состояниями



#Наша БД для вывода справки
user_data={}

# Кнопка Купить
#Реагируем на выбор:
from aiogram.dispatcher.filters import Text
@dp.message_handler(Text(equals="Купить"), state="*")
async def buy(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="BTC", callback_data="btc"))
    await message.answer("Выберите валюту, которую хотите купить", reply_markup=kb)
    user_data[0]='BTC'



#теперь отработаем нажатие BTC
@dp.callback_query_handler(text="btc")
async def enter_btc(call: types.CallbackQuery, state: FSMContext):

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Банковский перевод", callback_data="bp"))
    kb.add(types.InlineKeyboardButton(text="Электронные кошельки", callback_data="ek"))
    kb.add(types.InlineKeyboardButton(text="Наличными в банкомате", callback_data="nvb"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="back1"))
    await call.message.edit_text("Выберите способ оплаты", reply_markup=kb)


#Нажатие назад2 (дублируем код)
@dp.callback_query_handler(text="back1")
async def enter_back1(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="BTC", callback_data="btc"))
    await call.message.answer("Выберите валюту, которую хотите купить", reply_markup=kb)
    user_data[0] = 'BTC'


#нажатие Банковский перевод
@dp.callback_query_handler(text="bp")
async def enter_bp(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Альфабанк", callback_data="Alfa"))
    kb.add(types.InlineKeyboardButton(text="Тинькофф", callback_data="Tinkoff"))
    kb.add(types.InlineKeyboardButton(text="Сбербанк", callback_data="Sber"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="btc"))
    await call.message.edit_text("Выберите банк", reply_markup=kb)

#нажатие Электронные кошельки
@dp.callback_query_handler(text="ek")
async def enter_ek(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Яндекс.Деньги", callback_data="YaMon"))
    kb.add(types.InlineKeyboardButton(text="QIWI.Кошелёк", callback_data="QIWI"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="btc"))
    await call.message.edit_text("Выберите электронный кошелёк", reply_markup=kb)

#нажатие Наличными в банкомате
@dp.callback_query_handler(text="nvb")
async def enter_nvb(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Cash-in Альфабанк", callback_data="cashAlpha"))
    kb.add(types.InlineKeyboardButton(text="Cash-in Тинькофф", callback_data="cashTin"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="btc"))
    await call.message.edit_text("Выберите банк", reply_markup=kb)


#проверка на не float
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


#------------------------------------------------------------------------------------#
#Выход на сумму BTC
@dp.callback_query_handler(text=["Alfa","Tinkoff","Sber","YaMon","QIWI","cashAlpha","cashTin"])
async def enter_sum_btc(call: types.CallbackQuery,state: FSMContext ):
    await call.message.edit_text("Укажите точную сумму BTC, которую хотите получить на свой кошелёк. Пример 0.006489")
    await state.set_state('sum_BTC')
#-------------------------------------------------------------------------------------#


#Парсер суммы
@dp.message_handler(state='sum_BTC')
async def sumFics(message: types.Message, state: FSMContext):

    if is_not_float(str(message.text)):
        await message.answer("Пожалуйста, введите число. Пример: 0.0000324")
        return
    our_sum=float(message.text)
    if is_float(str(message.text)) and (our_sum > 10 or our_sum < 0.0000000001): #если это флот
        await message.answer("Пожалуйста, введите сумму в диапазоне от 0.0000000001 до 10 BTC")
        return

    await message.answer("Укажите номер электронного кошелька для зачисления BTC")
    await state.set_state('parser') #устанвливаем статус
    user_data[1] = str(our_sum) #Сохраняем в БД сумму



#Выход на номер кошелька
@dp.message_handler(state='parser')
async def enter_num_btc(message: types.Message, state: FSMContext):
     await numberFics_buy(message,state) #Вызываю функцию парсера


#Парсер кошелька BTC
async def numberFics_buy(message: types.Message, state: FSMContext):
    if len(str(message.text)) != 34:
        await message.answer(f'Пожалуйста, корректно введите номер кошелька. Он должен состоять из 34 символов,\n'
                             f'которые включают в себя латинские буквы(заглавные и строчные) и цифры')
        return

    kosh=message.text
    await message.answer("Кошелек указан корректно!")
    user_data[2] = str(kosh)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
    kb.add(types.InlineKeyboardButton(text="Нет", callback_data="NO"))

    await message.answer('Вы хотите купить: '+ user_data[0] + '\n'
                         + 'Сумма: ' + user_data[1] + '\n'
                         + user_data[0] + ' получить на номер ' + user_data[2] + '\n'
                         + 'По актуальному курсу (+10%)\n'
                         + 'Общая стоимость: 200руб.\n'
                         + 'Подвтерждаете условия сделки?',reply_markup=kb)
    await state.finish()


# нажатие Да
@dp.callback_query_handler(text="Yes")
async def enter_Yes(call: types.CallbackQuery,state: FSMContext):
    await call.message.answer("Заявка создана, дождитесь сообщения от оператора или свяжитесь самостоятельно, "
                                 "что бы ускорить процесс. Доступные операторы: [BEN] Криптосервис")
    await call.answer()




# нажатие Нет
@dp.callback_query_handler(text="NO")
async def enter_NO(call: types.CallbackQuery,state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data="mainmenu"))
    kb.add(types.InlineKeyboardButton(text="Назад к заявке", callback_data="btc"))
    await call.message.edit_text("Возможно Вас заинтересуют другие услуги.", reply_markup=kb)
    await call.answer()



#======================================================================ПРОДАЖА===================================================================================================

#БД для продажи
user_data_sold={}



#Реагируем на выбор продать:
from aiogram.dispatcher.filters import Text
@dp.message_handler(Text(equals="Продать"))
async def sold(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="BTC", callback_data="btc1"))
    await message.answer("Выберите валюту, которую хотите продать", reply_markup=kb)
    user_data_sold[0]='BTC'


#теперь отработаем нажатие BTC
@dp.callback_query_handler(text="btc1")
async def enter_btc1(call: types.CallbackQuery, state: FSMContext):

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Банковский перевод", callback_data="bp1"))
    kb.add(types.InlineKeyboardButton(text="Электронные кошельки", callback_data="ek1"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="back2"))
    await call.message.edit_text("Выберите способ оплаты", reply_markup=kb)

#Нажатие назад2 (дублирование кода)
@dp.callback_query_handler(text="back2")
async def enter_back2(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="BTC", callback_data="btc"))
    await call.message.answer("Выберите валюту, которую хотите купить", reply_markup=kb)
    user_data_sold[0] = 'BTC'


#нажатие Банковский перевод
@dp.callback_query_handler(text="bp1")
async def enter_bp1(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Альфабанк", callback_data="Alfa1"))
    kb.add(types.InlineKeyboardButton(text="Тинькофф", callback_data="Tinkoff1"))
    kb.add(types.InlineKeyboardButton(text="Сбербанк", callback_data="Sber1"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="btc1"))
    user_data_sold[2] = 'по банковскому переводу'
    await call.message.edit_text("Выберите банк", reply_markup=kb)

#нажатие Электронные кошельки
@dp.callback_query_handler(text="ek1")
async def enter_ek1(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Яндекс.Деньги", callback_data="YaMon1"))
    kb.add(types.InlineKeyboardButton(text="QIWI.Кошелёк", callback_data="QIWI1"))
    kb.add(types.InlineKeyboardButton(text="Назад", callback_data="btc1"))
    user_data_sold[2] = 'на электронный кошелек'
    await call.message.edit_text("Выберите электронный кошелёк", reply_markup=kb)


#--------------------------------------------------------------------------------------------#
#Выход на номер карты
@dp.callback_query_handler(text=["Alfa1","Tinkoff1","Sber1","YaMon1","QIWI1"])
async def enter_num_btc(call: types.CallbackQuery,state: FSMContext):
    await call.message.edit_text("Укажите номер банковской карты для получения денег")
    await state.set_state("num_card")
#---------------------------------------------------------------------------------------------#



#Парсер номера карты
@dp.message_handler(state='num_card')
async def numFics(message: types.Message, state: FSMContext):

    if is_not_float(str(message.text)):
        await message.answer("Номер карты неккоректен (Номер может содержать только цифры)")
        return
    our_num=int(message.text)
    if is_float(str(message.text)) and len(str(message.text))!= 16: #если это флот
        await message.answer("Пожалуйста, введите корректный номер карты (Неверное количество символов)")
        return
    await message.answer("Укажите точную сумму продажи криптовалюты. Пример 0.006489")
    await state.set_state('parser_num_card')
    user_data_sold[3] = str(our_num)


#Ввод суммы
@dp.message_handler(state='parser_num_card')
async def enter_num_btc_sold(message: types.Message, state: FSMContext):
     await num_card_Fics(message,state) #Вызываю функцию парсера


#Парсер суммы
async def num_card_Fics(message: types.Message, state: FSMContext):

    if is_not_float(str(message.text)):
        await message.answer("Пожалуйста, введите число. Пример: 0.0000324")
        return
    our_sum=float(message.text)
    if is_float(str(message.text)) and (our_sum > 10 or our_sum < 0.0000000001): #если это флот
        await message.answer("Пожалуйста, введите сумму в диапазоне от 0.0000000001 до 10 BTC")
        return
    user_data_sold[1] = str(our_sum)
    await message.answer("Сумма указана верно!")

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Да", callback_data="Yes1"))
    kb.add(types.InlineKeyboardButton(text="Нет", callback_data="NO1"))
    await message.answer('Вы хотите продать ' + user_data_sold[0] + '\n'
                         + 'Сумма: ' + user_data_sold[1]+ '\n'
                         + 'Деньги получить ' + user_data_sold[2] + '\n'
                         + 'По реквизитам: '+ user_data_sold[3] + '\n'
                         + 'По актуальному курсу: (-10%)\n'
                         + 'К общей выплате: 200руб\n'
                         + 'Подвтерждаете заявку и условия сделки?', reply_markup=kb)
    await state.finish()


# нажатие Да
@dp.callback_query_handler(text="Yes1")
async def enter_Yes1(call: types.CallbackQuery,state: FSMContext):
    me=await  bot.get_me()
    await call.message.edit_text(f'Заявка создана, дождитесь сообщения от оператора или свяжитесь самостоятельно, '
                                 f'что бы ускорить процесс. Доступные операторы: {me.username} [BEN] Криптосервис')
    await call.answer()

# нажатие Нет
@dp.callback_query_handler(text="NO1")
async def enter_NO1(call: types.CallbackQuery,state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data="main_menu")) # , callback_data="btc1"))
    kb.add(types.InlineKeyboardButton(text="Назад к заявке", callback_data="btc1"))
    await call.message.edit_text("Возможно Вас заинтересуют другие услуги.", reply_markup=kb)
    await call.answer()



#===============================================================ПРОФИЛЬ===========================================================================




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


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
