class SingletonMeta(type):
    """Metaclass implementing the Singleton pattern.

        Ensures that only one instance of a class is created.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Returns the singleton instance of the class.

            Creates one if it does not exist.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
