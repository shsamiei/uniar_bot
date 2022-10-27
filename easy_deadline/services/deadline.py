from _helpers import BaseCacheService


class DeadlineCacheService(BaseCacheService):
    PREFIX = 'ED'
    KEYS = {
        'course': f'{PREFIX}:''{user_id}_COURSE',
        'name': f'{PREFIX}:''{user_id}_NAME',
        'deadline': f'{PREFIX}:''{user_id}_DEADLINE',
        'reminder': f'{PREFIX}:''{user_id}_REMINDER',
    }
    EX = 60 * 15

    def cache_course(self, user_id, course_id, course_name):
        client = self._get_redis_client()

        client.set(name=self.KEYS['course'].format(user_id=user_id),
                   value=f'{course_id}:{course_name}')

    def get_course(self, user_id) -> str:
        client = self._get_redis_client()

        return (client.get(name=self.KEYS['course'].format(user_id=user_id)) or b'').decode()

    def cache_name(self, user_id, name):
        client = self._get_redis_client()

        client.set(name=self.KEYS['name'].format(user_id=user_id),
                   value=name)

    def get_name(self, user_id) -> str:
        client = self._get_redis_client()

        return (client.get(name=self.KEYS['name'].format(user_id=user_id)) or b'').decode()

    def cache_deadline(self, user_id, deadline):
        client = self._get_redis_client()

        client.set(name=self.KEYS['deadline'].format(user_id=user_id),
                   value=deadline)

    def get_deadline(self, user_id) -> str:
        client = self._get_redis_client()

        return (client.get(name=self.KEYS['deadline'].format(user_id=user_id)) or b'').decode()

    def cache_reminder(self, user_id, reminder):
        client = self._get_redis_client()

        client.set(name=self.KEYS['reminder'].format(user_id=user_id),
                   value=reminder)

    def get_reminder(self, user_id) -> int:
        client = self._get_redis_client()

        return int((client.get(name=self.KEYS['reminder'].format(user_id=user_id)) or b'0').decode())