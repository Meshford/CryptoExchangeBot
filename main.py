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
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
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


@dp.message_handler(state='support')
async def echo(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Купить")
    markup.add("Продать")
    markup.add("Профиль")
    markup.add("Поддержка")
    await message.answer("Сообщение направлено в поддержку",
                         reply_markup=markup)
    await state.finish()



# Кнопка Купить

#Реагируем на выбор:
from aiogram.dispatcher.filters import Text
@dp.message_handler(Text(equals="Купить"))
async def buy(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="BTC", callback_data="btc"))
    await message.answer("Выберите валюту, которую хотите купить", reply_markup=kb)
    await state.update_data(Valuta="BTC")
    #await state.finish()

#теперь отработаем нажатие BTC
@dp.callback_query_handler(text="btc")
async def enter_btc(call: types.CallbackQuery, state: FSMContext):

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Банковский перевод", callback_data="bp"))
    kb.add(types.InlineKeyboardButton(text="Электронные кошельки", callback_data="ek"))
    kb.add(types.InlineKeyboardButton(text="Наличными в банкомате", callback_data="nvb"))
    #await state.update_data(sp_op=InlineKeyboardButton.text) #?вроде как сохраняем ключ-значение, следовательно потом можем обратиться ко всем значениям по ключам в конечной справке
    await call.message.edit_text("Выберите способ оплаты", reply_markup=kb)


#нажатие Банковский перевод
@dp.callback_query_handler(text="bp")
async def enter_bp(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Альфабанк", callback_data="Alfa"))
    kb.add(types.InlineKeyboardButton(text="Тинькофф", callback_data="Tinkoff"))
    kb.add(types.InlineKeyboardButton(text="Сбербанк", callback_data="Sber"))
    #await state.update_data(bank=InlineKeyboardButton.text)  # ?
    await call.message.edit_text("Выберите банк", reply_markup=kb)

#нажатие Электронные кошельки
@dp.callback_query_handler(text="ek")
async def enter_ek(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Яндекс.Деньги", callback_data="YaMon"))
    kb.add(types.InlineKeyboardButton(text="QIWI.Кошелёк", callback_data="QIWI"))
    #await state.update_data(el_kol=InlineKeyboardButton.text)  # ?
    await call.message.edit_text("Выберите электронный кошелёк", reply_markup=kb)

#нажатие Наличными в банкомате
@dp.callback_query_handler(text="nvb")
async def enter_nvb(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Cash-in Альфабанк", callback_data="cashAlpha"))
    kb.add(types.InlineKeyboardButton(text="Cash-in Тинькофф", callback_data="cashTin"))
    #await state.update_data(cash_in=InlineKeyboardButton.text)  # ?
    await call.message.edit_text("Выберите банк", reply_markup=kb)

#класс для ожидания суммы
class PaymentSystem(StatesGroup):
    waiting_for_sum = State()
    waiting_for_Num_wallet = State()

@dp.message_handler()
async def enter_sum(message: types.Message):
    #await message.answer("Укажите точную сумму BTC, которую хотите получить на свой кошелёк. Пример 0.006489")
    await PaymentSystem.waiting_for_sum.set()
    await PaymentSystem.waiting_for_Num_wallet.set()

# Следующая функция будет вызываться только из указанного состояния,
# сохранять полученный от пользователя текст (если он валидный) и переходить к следующему шагу:
# Парсер суммы
@dp.message_handler()
async def sumFics(message: types.Message, state: FSMContext):
    if message.text.lower is not float :
        await message.answer("Пожалуйста, введите число. Пример: 0.0000324")
        return
    our_sum=message.text.tofloat()
    if our_sum>10 or our_sum<0.0000000001 :
        await message.answer("Пожалуйста, введите сумму в диапазоне от 0.0000000001 до 10 BTC")
        return
    await message.answer("Вы ввели "+str(our_sum))
    await state.update_data(sum=our_sum) #сохряем полученный текст в хранилище данных FSM
    # Концептуально это словарь, поэтому воспользуемся функцией update_data() и сохраним текст сообщения под ключом sum и со значением message.text.tofloat().

    # Для последовательных шагов можно не указывать название состояния, обходясь next()
    await PaymentSystem.next()

#Парсер кошелька BTC
@dp.message_handler()
async def numFics(message: types.Message, state: FSMContext):
    if len(message.text)!=34:
        await message.answer("Пожалуйста, корректно введите номер кошелька. Он должен состоять из 34 символов,"
                             "которые включают в себя латинские буквы(заглавные и строчные) и цифры")
        return
    our_num=message.text.tofloat() #можем перевести число во float, чтобы сравнивать
    #await state.update_data(num_wall=our_num) #сохряем полученный текст в хранилище данных FSM
    # Концептуально это словарь, поэтому воспользуемся функцией update_data() и сохраним текст сообщения под ключом sum и со значением message.text.tofloat().

    # Для последовательных шагов можно не указывать название состояния, обходясь next()
    await PaymentSystem.next()


#Общий выход
@dp.callback_query_handler(text=["Alfa","Tinkoff","Sber","YaMon","QIWI","cashAlpha","cashTin"])
async def enter_all(call: types.CallbackQuery,state: FSMContext ):
    await call.message.edit_text("Укажите точную сумму BTC, которую хотите получить на свой кошелёк. Пример 0.006489")
    await enter_sum()
    await sumFics()
    BD=await state.get_data() #Выгрузили БД
    sum=BD['sum'] #получили значение по ключу
    await call.message.edit_text("Укажите кошелек для зачисления BTC")
    await numFics()
    BD1 = await state.get_data() #Обновленная БД
    num=BD1['num_wall'] #получили значение по ключу
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Да", callback_data="Yes"))
    kb.add(types.InlineKeyboardButton(text="Нет", callback_data="NO"))
    await call.message.edit_text(f'1. Вы хотите купить'+BD1['Valuta']+'\n'
                                 f'2. Сумма: '+BD1['sum1']+'\n'
                                 f'3.'+BD1['Valuta']+'получить на '+BD1['num_wall'] +'\n'
                                 f'4. По актуальному курсу(+10%)\n'
                                 f'5. Общая стоимость 200руб.\n'
                                 f'Подвтерждаете условия сделки?', reply_markup=kb)
    await state.finish()

# нажатие Да
@dp.callback_query_handler(text="Yes")
async def enter_Yes(call: types.CallbackQuery):
    await call.message.edit_text("Заявка создана, дождитесь сообщения от оператора или свяжитесь самостоятельно, "
                                 "что бы ускорить процесс. Доступные операторы: [BEN] Криптосервис")
# нажатие Нет
@dp.callback_query_handler(text="NO")
async def enter_NO(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Вернуться в главное меню", callback_data="MainMenu"))
    kb.add(types.InlineKeyboardButton(text="Назад к заявке", callback_data="Back"))
    await call.message.edit_text("Возможно Вас заинтересуют другие услуги.", reply_markup=kb)








#Реагируем на выбор продать:
from aiogram.dispatcher.filters import Text
@dp.message_handler(Text(equals="Продать"))
async def sold(message: types.Message, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="BTC", callback_data="btc1"))
    await message.answer("Выберите валюту, которую хотите продать", reply_markup=kb)


#теперь отработаем нажатие BTC
@dp.callback_query_handler(text="btc1")
async def enter_btc(call: types.CallbackQuery, state: FSMContext):

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Банковский перевод", callback_data="bp1"))
    kb.add(types.InlineKeyboardButton(text="Электронные кошельки", callback_data="ek1"))
    await call.message.edit_text("Выберите способ оплаты", reply_markup=kb)


#нажатие Банковский перевод
@dp.callback_query_handler(text="bp1")
async def enter_bp(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Альфабанк", callback_data="Alfa1"))
    kb.add(types.InlineKeyboardButton(text="Тинькофф", callback_data="Tinkoff1"))
    kb.add(types.InlineKeyboardButton(text="Сбербанк", callback_data="Sber1"))
    await call.message.edit_text("Выберите банк", reply_markup=kb)

#нажатие Электронные кошельки
@dp.callback_query_handler(text="ek1")
async def enter_ek(call: types.CallbackQuery, state: FSMContext):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text="Яндекс.Деньги", callback_data="YaMon1"))
    kb.add(types.InlineKeyboardButton(text="QIWI.Кошелёк", callback_data="QIWI1"))
    await call.message.edit_text("Выберите электронный кошелёк", reply_markup=kb)


#Общий выход
@dp.callback_query_handler(text=["Alfa1","Tinkoff1","Sber1","YaMon1","QIWI1"])
async def enter_all1(call: types.CallbackQuery,state: FSMContext):
    await call.message.edit_text("Укажите номер карты для получения")
    #await enter_number_card() написать функцию парсера карты
    #await sumFics()
    #sum = await state.get_data()
    #await call.message.edit_text("Укажите кошелек для зачисления BTC")
    # sum1 = await state.get_data()


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
