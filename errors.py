"""
    Exception for get_movie_property returning no resource.
"""
class MovieNotFound(Exception):
    error_code: int
    message   : str