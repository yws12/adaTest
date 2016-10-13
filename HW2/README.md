# API

### Name
to get all students' info for either bachelors or masters


### usage
```
from ISA_api import get_all_student_list

ba_students = get_all_student_list('bachelor')
ms_students = get_all_student_list('master')
```

### return
A dict containing  all students info according to gps_codes keys are the same as gps_codes, values are a list of student info, which is a dict for each student.

Example:
```
{
    'Informatique, 2007-2008, Master semestre 1': [
    {
        'gender': 'Monsieur',
        'minor': None,
        'name': 'Aeberhard François-Xavier',
        'sciper': '153066',
        'specialization': None,
        'status': 'Présent'
    },
    {
        'gender': 'Madame',
        'minor': None,
        'name': 'Agarwal Megha',
        'sciper': '180027',
        'specialization': None,
        'status': 'Présent'
    },
    ...
    ],
    'Informatique, 2007-2008, Master semestre 2': [
    
    ],
    ...
}
```
