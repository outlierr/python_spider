class Common:
    def __init__(self, dic):
        for key, value in dic.items():
            if key in self.__dict__.keys():
                setattr(self, key, value)

    def __str__(self) -> str:
        return self.__dict__.__str__()


class User(Common):
    def __init__(self, user):
        self.sex = None
        self.name = None
        self.nick = None
        self.user_id = None
        self.phone = None
        self.authority = None
        self.isSchoolVerify = None
        self.school = None
        super().__init__(user)

    def __str__(self) -> str:
        return "{" + f"'sex': '{self.sex}', 'name': '{self.name}', 'nick': '{self.nick}', 'user_id': '{self.user_id}', " \
               f"'phone': '{self.phone}', 'authority': '{self.authority}', 'isSchoolVerify': '{self.isSchoolVerify}'," \
               f" 'school': {self.school.__str__()}" + "}"


class School(Common):
    def __init__(self, school):
        self.isVerified = None
        self.schoolName = None
        self.schoolId = None
        self.schoolOrgId = None
        self.collegeName = None
        self.collegeId = None
        self.className = None
        self.classId = None
        self.joinSchoolYear = None
        super().__init__(school)

    def __str__(cls) -> str:
        return super().__str__()
