import logging
from django.db.models import Sum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackContext, ConversationHandler, CallbackQueryHandler
from secret import BOT_TOKEN
from django.conf import settings
from prof.models import Student, University, Major
from prof.enums import YearChoices
from prof.services import NameMappingService
from easy_vahed.models import Chart, Course
from easy_vahed.services import CacheService, ConflictService
from easy_deadline.services import DeadlineCacheService

# Enable logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    is_registered = False
    if Student.objects.filter(user_id=user_id).exists():
        is_registered = True

    if not is_registered:
        return await blind_start(update, context)

    await menu(update, context)

    return settings.STATES['menu']


async def blind_start(update: Update, _: CallbackContext) -> int:
    message = update.message

    name_service: NameMappingService = NameMappingService()
    keyboard = [
        [
            InlineKeyboardButton(name_service.map_university(university.name), callback_data=university.id)
        ] for university in University.objects.all()
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        settings.TELEGRAM_MESSAGES['blind_start'],x
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['register_university']


async def register_university(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    service = CacheService()
    service.cache_university(user_id=user_id,
                             university=query.data)
    name_service: NameMappingService = NameMappingService()

    keyboard = [
        [
            InlineKeyboardButton(name_service.map_major(major.name), callback_data=major.id)
        ] for major in Major.objects.all()
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['register_university'],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['register_major']


async def register_major(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    service = CacheService()
    service.cache_major(user_id=user_id,
                        major=query.data)

    keyboard = [
        [
            InlineKeyboardButton(label, callback_data=year)
        ] for year, label in YearChoices.choices
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['register_major'],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['register_done']


async def register_done(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    service = CacheService()
    university_id = service.get_university(user_id=user_id)
    major_id = service.get_major(user_id=user_id)
    year = query.data

    if university_id == -1 or major_id == -1:
        await query.edit_message_text(
            settings.TELEGRAM_MESSAGES['expired']
        )
        return ConversationHandler.END

    Student.objects.create(
        name=query.from_user.full_name,
        user_id=user_id,
        user_name=query.from_user.username,
        university_id=university_id,
        major_id=major_id,
        year=year,
    )

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['register_done'],
        parse_mode=ParseMode.MARKDOWN,
    )

    return ConversationHandler.END


async def menu(update: Update, _: CallbackContext) -> int:
    message = update.message

    keyboard = [
        [
            InlineKeyboardButton('پروفایل', callback_data=0),
            InlineKeyboardButton('ایزی واحد', callback_data=1),
            InlineKeyboardButton('ایزی ددلاین', callback_data=2),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        settings.TELEGRAM_MESSAGES['menu'],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['menu']


async def easy_vahed(update: Update, _: CallbackContext) -> int:
    query = update.callback_query

    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton('انتخاب واحد', callback_data=0)
        ],
        [
            InlineKeyboardButton('دانلود چارت', callback_data=1)
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['easy_vahed'],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['easy_vahed']


async def choose_courses(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    selected_course = query.data

    service = CacheService()
    selected_courses = service.get_courses(user_id=user_id)

    if selected_course[0] == 'Z':
        await query.answer(text='تداخل داره!')
        return settings.STATES['choose_courses']

    await query.answer()
    if query.data == '-2':
        service.delete_conflicts_sum(user_id=user_id)
        service.delete_all_courses(user_id=user_id)

    if selected_course[0] == 'C':
        if str(selected_course[1:]) in selected_courses:
            service.delete_courses(user_id, str(selected_course[1:]))
            service.aggregate_conflicts_minus(user_id=user_id, course_id=int(selected_course[1:]))
        else:
            service.cache_course(user_id=user_id, course=selected_course[1:])
            service.aggregate_conflicts_plus(user_id=user_id, course_id=int(selected_course[1:]))

    if selected_course == '-1':
        return await choose_courses_done(update, context)

    selected_courses = service.get_courses(user_id=user_id)
    selected_courses_weight_sum = Course.objects.filter(id__in=selected_courses).aggregate(Sum('weight'))['weight__sum']
    conflicts = service.get_conflicts_sum(user_id=user_id)
    print(f'course: {selected_course}, confs: {conflicts}')

    selected_emoji = '\U0001F351'
    cross_emoji = '\U0001F480'
    get_name = lambda course, it: f'{str(course)}{("", f" {selected_emoji}")[str(course.id) in selected_courses]}' \
                              f'{(f" {cross_emoji}", "")[not conflicts[it] if conflicts else 1]}'
    has_conflict = lambda course, it: 1 if (conflicts[it] if conflicts else 0) else 0

    st = Student.objects.get(user_id=user_id)
    courses = Course.objects.filter(university=st.university,
                                    majors__in=[st.major])

    keyboard = [
        [
            InlineKeyboardButton(get_name(course, it),
                                 callback_data=fr'C{course.id}' if not has_conflict(course, it) else r'Z')
        ] for it, course in enumerate(courses)
    ]

    keyboard += [
        [
            InlineKeyboardButton('ریستارت', callback_data='-2'),
        ],
        [
            InlineKeyboardButton('تموم شد', callback_data='-1'),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['choose_courses'].format(weight=selected_courses_weight_sum or 0),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['choose_courses']


async def choose_courses_done(update: Update, _: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    cache_service = CacheService()
    service = ConflictService()

    st = Student.objects.get(user_id=user_id)
    course_ids = cache_service.get_courses(user_id=user_id)
    courses = Course.objects.filter(id__in=course_ids)
    all_courses = Course.objects.filter(university=st.university,
                                        majors__in=[st.major])

    for it_1, course_1 in enumerate(courses):
        for it_2, course_2 in enumerate(courses):
            if it_2 >= it_1:
                break

            has_conflict, reason = service.check_conflict(course_1, course_2)
            if has_conflict:

                init_message = settings.TELEGRAM_MESSAGES['has_conflict'].format(c1=course_1.name,
                                                                                 c2=course_2.name,
                                                                                 reason=reason)

                await query.edit_message_text(
                    init_message,
                    parse_mode=ParseMode.MARKDOWN
                )

                return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton('نه', callback_data=0),
            InlineKeyboardButton('آره', callback_data=1)
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    if not course_ids:
        await query.edit_message_text(
            settings.TELEGRAM_MESSAGES['has_not_conflict'],
        )

        return ConversationHandler.END

    await query.edit_message_text(
        f'{settings.TELEGRAM_MESSAGES["has_not_conflict"]}\n'
        f'{settings.TELEGRAM_MESSAGES["wanna_add_to_profile"]}',
        reply_markup=markup
    )

    return settings.STATES['add_course_to_profile']


async def add_course_to_profile(update: Update, _: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    service = CacheService()
    selected_courses = Course.objects.filter(id__in=service.get_courses(user_id=user_id))
    student = Student.objects.get(user_id=user_id)

    student.courses.clear()
    list(map(student.courses.add, selected_courses))

    await query.answer()

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['added_to_profile']
    )

    return ConversationHandler.END


async def cancel_adding_courses_to_profile(update: Update, _: CallbackContext):
    query = update.callback_query
    _ = query.from_user.id

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['cancel_adding_to_profile']
    )

    return ConversationHandler.END


async def download_chart(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()

    st = Student.objects.get(user_id=user_id)
    chart = Chart.objects.get(university=st.university,
                              major=st.major)

    await context.bot.send_document(
        document=chart.file.file,
        chat_id=user_id
    )

    return settings.STATES['easy_vahed']


async def profile(update: Update, _: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    st = Student.objects.get(user_id=user_id)
    name_service: NameMappingService = NameMappingService()

    init_message = settings.TELEGRAM_MESSAGES['profile'].format(name=st.name,
                                                                major=name_service.map_major(st.major.name),
                                                                university=name_service.map_university(
                                                                    st.university.name),
                                                                year=name_service.map_year(st.year))
    courses_message = '\n'.join([settings.TELEGRAM_MESSAGES['profile_courses'].format(
        name=course.name,
        prof=course.professor,
        weight=course.weight
    ) for course in st.courses.all()])

    sum_course_weight = Course.objects.filter(
        id__in=st.courses.all().values_list('id')
    ).aggregate(Sum('weight'))['weight__sum'] or 0

    sum_course_weight_message = settings.TELEGRAM_MESSAGES['sum_weight'].format(sum=sum_course_weight)

    await query.answer()
    await query.edit_message_text(
        f"{init_message}\n---\n"
        f"{courses_message}\n---\n"
        f"{sum_course_weight_message}",
        parse_mode=ParseMode.MARKDOWN
    )

    return


async def easy_deadline(update: Update, _: CallbackContext) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    st = Student.objects.get(user_id=user_id)
    keyboard = [
        [
            InlineKeyboardButton(str(course), callback_data=course.id)
        ] for course in st.courses.all()
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['easy_deadline_main'],
        reply_markup=markup,
        parse_mode=ParseMode.MARKDOWN
    )

    return settings.STATES['easy_deadline']


async def deadline_course_select(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    service = DeadlineCacheService()
    if query.id.isdigit():
        course = Course.objects.get(id=int(query.id))
        service.cache_course(user_id=user_id,
                             course_id=course.id,
                             course_name=course.name)
    else:
        if query.data == 'E0':
            await deadline_course_name(update, context)
        elif query.data == 'E1':
            service.cache_deadline(user_id=user_id, deadline=query.data)
        elif query.data == 'E2':
            if service.get_reminder(user_id=user_id):
                service.cache_reminder(user_id=user_id, reminder=0)
            service.cache_reminder(user_id=user_id, reminder=1)
        else:
            ...

    course_id, course_name = service.get_course(user_id=user_id).split(':')
    if not course_id:
        return

    cached_name = service.get_name(user_id=user_id)
    name = f'نام تمرین' + (f': {cached_name}', '')[not cached_name]
    cached_deadline = service.get_deadline(user_id=user_id)
    deadline = f'ددلاین' + (f': {cached_deadline}', '')[not cached_deadline]
    cached_reminder = service.get_reminder(user_id=user_id)
    if cached_reminder == 1:
        cached_reminder = '\U0001F346'
    reminder = f'یادآور' + (f': {cached_reminder}', '')[not cached_reminder]

    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton(name, callback_data='E0'),
        ],
        [
            InlineKeyboardButton(deadline, callback_data='E1'),
        ],
        [
            InlineKeyboardButton(reminder, callback_data='E2')
        ],
        [
            InlineKeyboardButton('تمام شد', callback_data='E-1')
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['easy_deadline_course'].format(name=course_name),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup
    )

    return settings.STATES['easy_deadline_courses']


async def deadline_course_name(update: Update, _: CallbackContext):
    query = update.callback_query

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['easy_deadline_name'],
        parse_mode=ParseMode.MARKDOWN
    )

    return settings.STATES['easy_deadline_name']


async def deadline_store_course_name(update: Update, _: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    service = DeadlineCacheService()
    service.cache_name(user_id=user_id,
                       name=message.text)

    return settings.STATES['easy_deadline_name']


async def deadline_course_deadline(update: Update, _: CallbackContext):
    query = update.callback_query

    await query.edit_message_text(
        settings.TELEGRAM_MESSAGES['easy_deadline_deadline'],
        parse_mode=ParseMode.MARKDOWN
    )

    return settings.STATES['easy_deadline_name']


async def deadline_store_course_deadline(update: Update, _: CallbackContext):
    message = update.message
    user_id = message.from_user.id

    service = DeadlineCacheService()
    service.cache_name(user_id=user_id,
                       name=message.text)

    return settings.STATES['easy_deadline_name']


def main() -> None:
    """Start the bot."""

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            settings.STATES['register_university']: [
                CallbackQueryHandler(register_university, pattern=r'^\d+$')
            ],
            settings.STATES['register_major']: [
                CallbackQueryHandler(register_major, pattern=r'^\d+$')
            ],
            settings.STATES['register_done']: [
                CallbackQueryHandler(register_done, pattern=r'^\d+$')
            ],
            settings.STATES['menu']: [
                CallbackQueryHandler(profile, pattern=r'^0$'),
                CallbackQueryHandler(easy_vahed, pattern=r'^1$'),
                CallbackQueryHandler(easy_deadline, pattern=r'^2$'),
            ],
            settings.STATES['easy_vahed']: [
                CallbackQueryHandler(choose_courses, pattern=r'^0$'),
                CallbackQueryHandler(download_chart, pattern=r'^1$'),
            ],
            settings.STATES['choose_courses']: [
                CallbackQueryHandler(choose_courses, pattern='^.+$')
            ],
            settings.STATES['add_course_to_profile']: [
                CallbackQueryHandler(cancel_adding_courses_to_profile, pattern='^0$'),
                CallbackQueryHandler(add_course_to_profile, pattern='^1$'),
            ],
            settings.STATES['easy_deadline']: [
                # CallbackQueryHandler()
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    ))
    application.run_polling()


if __name__ == "__main__":
    main()
