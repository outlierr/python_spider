from configparser import ConfigParser


class MyConfigParser(ConfigParser):
    def __init__(self):
        ConfigParser.__init__(self)

    def optionxform(self, optionstr: str) -> str:
        return optionstr
