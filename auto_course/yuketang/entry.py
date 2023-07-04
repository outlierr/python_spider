class Common:
    def __init__(self, dic):
        for key, value in dic.items():
            if key in self.__dict__.keys():
                setattr(self, key, value)

    def __str__(self) -> str:
        return self.__dict__.__str__()


class Course(Common):
    def __init__(self, course):
        self.sku_id = None
        self.course_name = None
        self.course_sign = None
        self.classroom_id = None
        self.course_id = None
        self.class_start = None
        self.class_end = None
        super().__init__(course)

    def __str__(self) -> str:
        return super().__str__()


class Chapter(Common):
    def __init__(self, chapter):
        self.id = None
        self.name = None
        self.leaves = None
        super().__init__(chapter)

    def __str__(self) -> str:
        leaves = []
        for leaf in self.leaves:
            leaves.append(leaf.__str__())
        return '{' + "'id': {}, 'name': {}, 'leaves': {}".format(self.id, self.name, leaves) + '}'
        # s = "{'id': '{}', 'name': '{}', leaves: {}".format(
        #     self.id, self.name, leaves
        # )


class Leaf(Common):
    def __init__(self, leaf):
        self.id = None
        self.name = None
        self.leaf_type = None
        super().__init__(leaf)

    def __str__(self) -> str:
        return super().__str__()
