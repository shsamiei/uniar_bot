import pandas as pd
from prof.models import Professor, University, Major
from easy_vahed.models import Course, WeekDay


class DataService:

    @staticmethod
    def create_course_from_csv(csv_path):
        df = pd.read_csv(csv_path)
        df = df.astype({"exam_date": str}, errors='raise')

        df.exam_date = '2023-01-' + df.exam_date
        for index, row in df.iterrows():
            course_params = row.to_dict()
            if not Professor.objects.filter(name=course_params['professor']).exists():
                Professor.objects.create(name=course_params['professor'])
            p = Professor.objects.get(name=course_params['professor'])
            u = University.objects.get(name=course_params['university'])
            m = Major.objects.get(name=course_params['majors'])
            c = Course(
                name=course_params['name'],
                professor=p,
                university=u,
                weight=course_params['weight'],
                start_hour=course_params['start_time'],
                end_hour=course_params['end_time'],
                exam_date=course_params['exam_date'],
                exam_start=course_params['exam_start'],
                exam_end=course_params['exam_end'],
            )

            c.save()
            c.majors.add(m)
            [c.days.add(WeekDay.objects.get(day=d)) for d in course_params['days'].split(':')]
