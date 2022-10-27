from _helpers import BaseCacheService
from django.utils import timezone
from typing import List


class CacheService(BaseCacheService):
    PREFIX = 'E'
    KEYS = {
        'university': f'{PREFIX}:''{user_id}_UNIVERSITY',
        'major': f'{PREFIX}:''{user_id}_MAJOR',
        'course': f'{PREFIX}:''{user_id}_COURSES',
        'conflicts': f'{PREFIX}:''{course_id}_CONFLICTS',
        'conflicts_sum': f'{PREFIX}:''{user_id}_CONFLICTS_SUM',
    }
    EX = 60 * 30

    def cache_university(self, user_id, university):
        client = self._get_redis_client()

        client.set(name=self.KEYS['university'].format(user_id=user_id),
                   value=university,
                   ex=self.EX)

    def get_university(self, user_id) -> int:
        client = self._get_redis_client()

        return int(client.get(name=self.KEYS['university'].format(user_id=user_id)) or b'-1')

    def cache_major(self, user_id, major):
        client = self._get_redis_client()

        client.set(name=self.KEYS['major'].format(user_id=user_id),
                   value=major,
                   ex=self.EX)

    def get_major(self, user_id) -> int:
        client = self._get_redis_client()

        return int(client.get(name=self.KEYS['major'].format(user_id=user_id)) or b'-1')

    def cache_course(self, user_id, course):
        client = self._get_redis_client()

        client.hset(name=self.KEYS['course'].format(user_id=user_id),
                    key=course,
                    value=timezone.now().timestamp())

    def get_courses(self, user_id):
        client = self._get_redis_client()

        return [c.decode() for c in client.hgetall(name=self.KEYS['course'].format(user_id=user_id))]

    def get_course_created(self, user_id, course):
        client = self._get_redis_client()

        return float(client.hget(name=self.KEYS['course'].format(user_id=user_id), key=course).decode())

    def delete_courses(self, user_id, *courses):
        if not courses:
            return

        client = self._get_redis_client()
        client.hdel(self.KEYS['course'].format(user_id=user_id),
                    *courses)

    def delete_all_courses(self, user_id):
        client = self._get_redis_client()

        client.delete(self.KEYS['course'].format(user_id=user_id))

    def delete_non_used_courses(self, user_id):
        now = timezone.now().timestamp()
        courses = [course for course in self.get_courses(user_id=user_id)
                   if now - self.get_course_created(user_id=user_id, course=course) >= self.EX]

        self.delete_courses(user_id, *courses)

    def cache_conflicts(self, course_id, *courses):
        client = self._get_redis_client()

        client.rpush(self.KEYS['conflicts'].format(course_id=course_id), *courses)

    def get_conflicts(self, course_id) -> List[int]:
        client = self._get_redis_client()

        return list(map(lambda x: int(x.decode()),
                        client.lrange(name=self.KEYS['conflicts'].format(course_id=course_id), start=0, end=127)))

    def delete_conflicts(self, course_id):
        client = self._get_redis_client()

        client.delete(self.KEYS['conflicts'].format(course_id=course_id))

    def get_conflicts_sum(self, user_id) -> List[int]:
        client = self._get_redis_client()

        return list(map(lambda x: int(x.decode()),
                        client.lrange(name=self.KEYS['conflicts_sum'].format(user_id=user_id), start=0, end=127)))

    def init_conflicts_sum(self, user_id, *conflicts):
        client = self._get_redis_client()

        client.rpush(
            self.KEYS['conflicts_sum'].format(user_id=user_id),
            *conflicts
        )

    def delete_conflicts_sum(self, user_id):
        client = self._get_redis_client()

        client.delete(self.KEYS['conflicts_sum'].format(user_id=user_id))

    def aggregate_conflicts_plus(self, user_id, course_id):
        client = self._get_redis_client()

        conflicts = self.get_conflicts(course_id=course_id)
        current_conflicts = self.get_conflicts_sum(user_id=user_id)

        if not current_conflicts:
            self.init_conflicts_sum(
                user_id,
                *conflicts
            )

            return

        self.delete_conflicts_sum(user_id=user_id)
        client.rpush(
            self.KEYS['conflicts_sum'].format(user_id=user_id),
            *list(map(lambda x, y: x + y, conflicts, current_conflicts))
        )

    def aggregate_conflicts_minus(self, user_id, course_id):
        client = self._get_redis_client()

        conflicts = self.get_conflicts(course_id=course_id)
        current_conflicts = self.get_conflicts_sum(user_id=user_id)

        if not current_conflicts:
            self.init_conflicts_sum(
                user_id,
                *conflicts
            )

            return

        self.delete_conflicts_sum(user_id=user_id)
        client.rpush(
            self.KEYS['conflicts_sum'].format(user_id=user_id),
            *list(map(lambda x, y: x - y, current_conflicts, conflicts))
        )
