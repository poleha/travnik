from django.conf import settings as project_settings

class Settings:
    SUPER_MODEL_KEY_NAME = 'user_key'

    USER_ROLE_REGULAR = 1
    USER_ROLE_ADMIN = 33


    USER_ROLES = (
            (USER_ROLE_REGULAR, 'Обычный пользователь'),
            (USER_ROLE_ADMIN, 'Админ'),
        )

    PAGES_TO_SHOW_FOR_LIST_VIEW = 10

    BASE_TEMPLATE = 'super_model/base/base.html'

    BEST_COMMENTS_DAYS = 30

    EMAIL_IS_REQUIRED_FOR_COMMENT = True

    POST_TITLE_UNIQUE = False

    HISTORY_TYPE_COMMENT_CREATED = 1
    HISTORY_TYPE_COMMENT_SAVED = 2
    HISTORY_TYPE_COMMENT_RATED = 3
    HISTORY_TYPE_POST_CREATED = 4
    HISTORY_TYPE_POST_SAVED = 5
    HISTORY_TYPE_POST_RATED = 6
    HISTORY_TYPE_COMMENT_COMPLAINT = 7
    HISTORY_TYPE_USER_POST_RATED = 8
    HISTORY_TYPE_USER_POST_COMPLAINT = 9

    HISTORY_TYPES = (
        (HISTORY_TYPE_COMMENT_CREATED, 'Комментарий создан'),
        (HISTORY_TYPE_COMMENT_SAVED, 'Комментарий сохранен'),
        (HISTORY_TYPE_COMMENT_RATED, 'Комментарий оценен'),
        (HISTORY_TYPE_POST_CREATED, 'Материал создан'),
        (HISTORY_TYPE_POST_SAVED, 'Материал сохранен'),
        (HISTORY_TYPE_POST_RATED, 'Материал оценен'),
        (HISTORY_TYPE_COMMENT_COMPLAINT, 'Жалоба на комментарий'),
        (HISTORY_TYPE_USER_POST_RATED, 'Пользовательский материал оценен'),
        (HISTORY_TYPE_USER_POST_COMPLAINT, 'Жалоба на пользовательский материал'),

    )

    HISTORY_TYPES_POINTS = {
        HISTORY_TYPE_COMMENT_CREATED: 3,
        HISTORY_TYPE_COMMENT_SAVED: 0,
        HISTORY_TYPE_COMMENT_RATED: 1,
        HISTORY_TYPE_POST_CREATED: 0,
        HISTORY_TYPE_POST_SAVED: 0,
        HISTORY_TYPE_POST_RATED: 1,
        HISTORY_TYPE_COMMENT_COMPLAINT: 0,
        HISTORY_TYPE_USER_POST_RATED: 1,
        HISTORY_TYPE_USER_POST_COMPLAINT: 0,
        }

    COUNT_COMPLAINTS_IN_KARM = False

    def __getattribute__(self, item):
        if hasattr(project_settings, item):
            return getattr(project_settings, item)
        else:
            return super().__getattribute__(item)


settings = Settings()