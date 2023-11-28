import copy
import sqlite3


class CannotConnectException(Exception):
    "Raised when the SQLDICT can't connect"
    pass


class SQLChooser:
    def __init__(self, name, value_wanted):
        self.name = name
        self.value_wanted = value_wanted


class SQLColumn:
    "Used in SQLDict.__init__ for chooserNames and selects"

    def __init__(self, name, datatype="VARCHAR", can_be_null=True):
        self.name = name
        self.datatype = datatype
        self.can_be_null = can_be_null

    def __str__(self):
        e = self.name + "\t" + self.datatype
        if not self.can_be_null:
            e += "\t" + "NOT NULL"
        return e


class InvalidKeywordException(Exception):
    "Raised when an invalid keyword is given"
    pass


class ColumnNotFound(Exception):
    "Raised when a column is not found"
    pass


class SQLDict:
    "A custom class that represents a dictionary, but instead of being stored in RAM, it's stored in SQL"

    def __init__(
        self,
        database_name,
        name,
        tablename,
        choosers=[SQLColumn("_key")],
        selects=[SQLColumn("_value")],
        init_new_table=True,
    ):
        self.database_name = database_name
        assert isinstance(choosers, list)
        assert isinstance(selects, list)
        self.choosers = choosers
        self.selects = selects
        self.name = name  # each SqlDict
        # test connection to database, and initialize my table
        connection = self.connection
        if init_new_table:
            query = f"CREATE TABLE {self.name} ("
            for item in range(len(choosers)):
                query += str(choosers[item])
                if item != len(choosers) - 1:
                    query += ","
                query += "\n"
            query += ");"

            connection.execute(query)  # initialize the table
            connection.commit()
        else:
            connection.close()

    def __where_clause__(self, choosers):
        "A helper function that provides the help clause"
        query = "WHERE"
        for item in range(len(choosers)):
            query += f"{choosers[item].name} = {choosers[item].value_wanted}"
            if item != len(choosers) - 1:
                query += "AND"
        return query

    @property
    def connection(self):
        "Connect to my database"
        try:
            return sqlite3.connect(self.database_name)
        except Exception as e:
            raise CannotConnectException(
                f"Can't connect to database {self.database_name}, maybe you made a typo?"
            ) from e

    def _connect_and_commit(
        self,
        query,
        _execute_before_querying_=lambda: None,
        _execute_between_querying_and_committing_=lambda: None,
        _execute_after_committing_=lambda: None,
        return_results_of_execution=False,
    ):
        """A helper function for connecting and committing. You can pass in callables to _execute_before_querying, _execute_between_querying_and_commiting, and _execute_after_committing.
        They must take a argument that is the instance of this sqldict. (and _execute_between_querying_and_committing and _execute_after_committing_ must take a Cursor object as its second argument) And they must be in the format (callable, options).
        """
        assert isinstance(_execute_after_committing_, function)

        connection = self.connection
        a = _execute_before_querying_[0](self, *_execute_before_querying_[1])
        cursor = self.connection.cursor
        self.connection.execute(query)
        b = _execute_between_querying_and_committing_[0](
            self, cursor, *_execute_between_querying_and_committing_[1]
        )

        c = _execute_after_committing_[0](self, cursor, *_execute_after_committing_[1])
        if return_results_of_execution:
            return (a, b, c)
        return None

    def get_item(self, choosers: list, wanted: list):
        """Get the item with the exact choosers provided. Like dict[key]
        choosers is a list of SQLChoosers"""
        if len(choosers) != len(self.chooserNames):
            raise ValueError(
                f"{len(choosers)} choosers provided, expected {len(self.chooserNames)} choosers"
            )
        for item in choosers:
            if item not in self.choosers:
                raise ValueError(
                    f"Did not expect chooser argument {item.name}, valid values are {', '.join([item.name for item in self.chooserNames])}"
                )

        for item in wanted:
            if item not in self.selects:
                raise ValueError(
                    f"Did not expect wanted argument {item}, valid values are {', '.join(self.selects)}"
                )

        connection = self.connection  # Establish connection
        query = "SELECT"
        for item in range(len(wanted)):  # Generate the second part (SELECT columns)
            query += wanted[item]
            if item != len(wanted) - 1:
                query += ", "
        query += self.__where_clause__(choosers)
        cursor = self.connection.cursor
        e = cursor.execute(query + f" {query} FROM {self.name}")
        no = lambda cursor: cursor.fetchall()
        no(cursor)
        self.connection.commit()

    def set_item(self, choosers, **selects):
        "Set the item located at choosers to selects (keyword arguments (keyword name: new value))"
        for item in choosers:
            if item not in self.choosers:
                raise ValueError(
                    f"Did not expect chooser argument {item.name}, valid values are {', '.join([item.name for item in self.chooserNames])}"
                )

        for item in selects.keys:
            if item not in [i.item for i in self.selects]:
                raise InvalidKeywordException(f"Did not expect keyword argument {item}")
        q = f"UPDATE {self.name} \nSET "
        for item in selects.keys():  # GENERATE SET column1=value....
            q += f"{item} = {selects[item]}"
        q += "\n"
        q += self.__where_clause__(choosers)
        self._connect_and_commit(q)

    def get_column(self, column_name: str):
        "Get a column's contents."
        query = f"SELECT {column_name} \nFROM {self.name}"
        result = self._connect_and_commit(
            query,
            _execute_after_committing_=(lambda self, cursor: cursor.fetchall(), []),
            return_results_of_execution=True,
        )
        return result[2]  # the list of Rows returned by _execute_after_committing_

    def get_columns(self, columns: list):
        "Get the contents of the columns given"
        columns_to_return = {}
        for c in columns:
            columns_to_return[c] = self.get_column(c)
        return columns_to_return

    @property
    def columns(self):
        c = copy.deepcopy(self.choosers)
        s = copy.deepcopy(self.selects)
        return c.extend(s)

    def return_everything(self):
        "Basically converts this into a dict :-) However, there isn't a way to turn a dictionary into a SQLDict :("
        return self.columns([column.name for column in self.columns])
